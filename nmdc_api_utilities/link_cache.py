# -*- coding: utf-8 -*-
"""
Link caching for NMDC relationships using DuckDB.

This module provides fast local caching of relationships between NMDC objects,
without attempting to cache the full object data (which has schema evolution issues).

The cache stores a simple edge table with relationships like:
- biosample → study (part_of)
- data_object → biosample (generated_from)
- workflow_execution → data_object (has_output)
- etc.

Design principles:
- Links-only: We cache relationships, not full objects
- Stable schema: 5-column edge table that won't change
- Hybrid queries: Fast link lookups + API for full object data
- User-managed: Explicit sync, no auto-refresh
"""
import duckdb
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class LinkCache:
    """
    DuckDB-based cache for NMDC object relationships.

    Examples
    --------
    >>> cache = LinkCache()
    >>> # Cache links for a biosample
    >>> cache.cache_links_for_id('nmdc:bsm-11-x5xj6p33', fetch_from_api=True)
    >>> # Query cached links
    >>> links = cache.get_links_for_id('nmdc:bsm-11-x5xj6p33', direction='downstream')
    >>> len(links) > 0
    True
    """

    def __init__(self, cache_path: Optional[Path] = None):
        """
        Initialize link cache.

        Parameters
        ----------
        cache_path : Path, optional
            Path to DuckDB file. Defaults to ~/.nmdc/links.db
        """
        if cache_path is None:
            cache_path = Path.home() / ".nmdc" / "links.db"

        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

        # Connect to DuckDB
        self.conn = duckdb.connect(str(self.cache_path))

        # Initialize schema
        self._init_schema()

        logger.info(f"Link cache initialized at {self.cache_path}")

    def _init_schema(self):
        """Create tables if they don't exist."""

        # Links table - the core edge table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS links (
                source_id VARCHAR,
                target_id VARCHAR,
                relationship_type VARCHAR,
                source_type VARCHAR,
                target_type VARCHAR,
                _cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (source_id, target_id, relationship_type)
            )
        """)

        # Indexes for fast lookups
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_links_source ON links(source_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_links_target ON links(target_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_links_rel_type ON links(relationship_type)")

        # Metadata table - track what we've cached
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS cache_metadata (
                entity_id VARCHAR PRIMARY KEY,
                entity_type VARCHAR,
                last_synced TIMESTAMP,
                link_count INTEGER,
                sync_source VARCHAR,  -- 'linked_instances', 'collection_record', 'manual'
                notes TEXT
            )
        """)

        logger.debug("Link cache schema initialized")

    def add_link(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        source_type: Optional[str] = None,
        target_type: Optional[str] = None
    ):
        """
        Add a single link to the cache.

        Parameters
        ----------
        source_id : str
            Source NMDC ID (e.g., 'nmdc:bsm-11-x5xj6p33')
        target_id : str
            Target NMDC ID
        relationship_type : str
            Type of relationship (e.g., 'part_of', 'generated_from', 'upstream', 'downstream')
        source_type : str, optional
            NMDC type of source (e.g., 'nmdc:Biosample')
        target_type : str, optional
            NMDC type of target
        """
        self.conn.execute("""
            INSERT INTO links
            (source_id, target_id, relationship_type, source_type, target_type, _cached_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT (source_id, target_id, relationship_type)
            DO UPDATE SET
                source_type = EXCLUDED.source_type,
                target_type = EXCLUDED.target_type,
                _cached_at = (SELECT CURRENT_TIMESTAMP)
        """, [source_id, target_id, relationship_type, source_type, target_type])

        logger.debug(f"Added link: {source_id} --[{relationship_type}]--> {target_id}")

    def add_links_bulk(self, links: List[Dict]):
        """
        Add multiple links efficiently.

        Parameters
        ----------
        links : list of dict
            List of link dictionaries with keys: source_id, target_id, relationship_type,
            and optionally source_type, target_type
        """
        if not links:
            return

        # Prepare tuples for bulk insert
        values = [
            (
                link['source_id'],
                link['target_id'],
                link['relationship_type'],
                link.get('source_type'),
                link.get('target_type')
            )
            for link in links
        ]

        self.conn.executemany("""
            INSERT INTO links
            (source_id, target_id, relationship_type, source_type, target_type, _cached_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT (source_id, target_id, relationship_type)
            DO UPDATE SET
                source_type = EXCLUDED.source_type,
                target_type = EXCLUDED.target_type,
                _cached_at = (SELECT CURRENT_TIMESTAMP)
        """, values)

        logger.info(f"Added {len(links)} links to cache")

    def get_links_for_id(
        self,
        entity_id: str,
        direction: str = 'both',
        relationship_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Get all cached links for an entity.

        Parameters
        ----------
        entity_id : str
            NMDC ID to query
        direction : str
            'both', 'outgoing', or 'incoming'
        relationship_type : str, optional
            Filter by specific relationship type

        Returns
        -------
        list of dict
            List of link records
        """
        conditions = []
        params = []

        if direction == 'outgoing':
            conditions.append("source_id = ?")
            params.append(entity_id)
        elif direction == 'incoming':
            conditions.append("target_id = ?")
            params.append(entity_id)
        else:  # both
            conditions.append("(source_id = ? OR target_id = ?)")
            params.extend([entity_id, entity_id])

        if relationship_type:
            conditions.append("relationship_type = ?")
            params.append(relationship_type)

        where_clause = " AND ".join(conditions)
        query = f"SELECT * FROM links WHERE {where_clause}"

        result = self.conn.execute(query, params).fetchall()

        # Convert to list of dicts
        columns = ['source_id', 'target_id', 'relationship_type', 'source_type', 'target_type', '_cached_at']
        links = [dict(zip(columns, row)) for row in result]

        logger.debug(f"Found {len(links)} cached links for {entity_id}")
        return links

    def get_connected_ids(
        self,
        entity_id: str,
        direction: str = 'both',
        relationship_type: Optional[str] = None,
        target_type: Optional[str] = None
    ) -> List[str]:
        """
        Get IDs of entities connected to this one.

        Parameters
        ----------
        entity_id : str
            NMDC ID to query
        direction : str
            'both', 'outgoing', or 'incoming'
        relationship_type : str, optional
            Filter by relationship type
        target_type : str, optional
            Filter by target entity type (e.g., 'nmdc:Study')

        Returns
        -------
        list of str
            List of connected NMDC IDs
        """
        links = self.get_links_for_id(entity_id, direction, relationship_type)

        connected = set()
        for link in links:
            if link['source_id'] == entity_id:
                if target_type is None or link['target_type'] == target_type:
                    connected.add(link['target_id'])
            else:
                if target_type is None or link['source_type'] == target_type:
                    connected.add(link['source_id'])

        return list(connected)

    def cache_from_linked_instances(self, results: List[Dict], nexus_id: str):
        """
        Extract and cache links from linked_instances API response.

        Parameters
        ----------
        results : list of dict
            Results from LinkedInstancesSearch.get_linked_instances()
        nexus_id : str
            The nexus ID used in the query
        """
        links = []

        for record in results:
            record_id = record.get('id')
            record_type = record.get('type')

            if not record_id:
                continue

            # Extract upstream relationships
            if '_upstream_of' in record and nexus_id in record['_upstream_of']:
                links.append({
                    'source_id': record_id,
                    'target_id': nexus_id,
                    'relationship_type': 'upstream',
                    'source_type': record_type,
                    'target_type': None  # We don't know target type from this
                })

            # Extract downstream relationships
            if '_downstream_of' in record and nexus_id in record['_downstream_of']:
                links.append({
                    'source_id': nexus_id,
                    'target_id': record_id,
                    'relationship_type': 'downstream',
                    'source_type': None,
                    'target_type': record_type
                })

        if links:
            self.add_links_bulk(links)

            # Update metadata
            self.conn.execute("""
                INSERT INTO cache_metadata
                (entity_id, entity_type, last_synced, link_count, sync_source)
                VALUES (?, ?, CURRENT_TIMESTAMP, ?, 'linked_instances')
                ON CONFLICT (entity_id)
                DO UPDATE SET
                    last_synced = (SELECT CURRENT_TIMESTAMP),
                    link_count = EXCLUDED.link_count,
                    sync_source = EXCLUDED.sync_source
            """, [nexus_id, None, len(links)])

        return len(links)

    def cache_from_collection_record(self, record: Dict):
        """
        Extract and cache links from a collection record (biosample, study, etc.).

        This extracts obvious relationships from flattened fields like:
        - biosample.associated_studies → study
        - data_object.was_generated_by → workflow

        Parameters
        ----------
        record : dict
            A collection record (from BiosampleSearch, etc.)
        """
        links = []
        record_id = record.get('id')
        record_type = record.get('type')

        if not record_id:
            return 0

        # Extract biosample → study links
        if 'associated_studies' in record:
            studies = record['associated_studies']
            if isinstance(studies, list):
                study_ids = studies
            elif isinstance(studies, str):
                # Handle pipe-separated from flattened export
                study_ids = [s.strip() for s in studies.split('|') if s.strip()]
            else:
                study_ids = []

            for study_id in study_ids:
                links.append({
                    'source_id': record_id,
                    'target_id': study_id,
                    'relationship_type': 'part_of',
                    'source_type': record_type or 'nmdc:Biosample',
                    'target_type': 'nmdc:Study'
                })

        # Extract data_object → workflow links
        if 'was_generated_by' in record:
            workflow_id = record['was_generated_by']
            if workflow_id:
                links.append({
                    'source_id': record_id,
                    'target_id': workflow_id,
                    'relationship_type': 'was_generated_by',
                    'source_type': record_type or 'nmdc:DataObject',
                    'target_type': 'nmdc:WorkflowExecution'
                })

        # Extract study → parent study links
        if 'part_of' in record:
            parent_ids = record['part_of']
            if isinstance(parent_ids, list):
                parent_id_list = parent_ids
            elif isinstance(parent_ids, str):
                parent_id_list = [p.strip() for p in parent_ids.split('|') if p.strip()]
            else:
                parent_id_list = []

            for parent_id in parent_id_list:
                links.append({
                    'source_id': record_id,
                    'target_id': parent_id,
                    'relationship_type': 'part_of',
                    'source_type': record_type or 'nmdc:Study',
                    'target_type': 'nmdc:Study'
                })

        if links:
            self.add_links_bulk(links)

            # Update metadata
            self.conn.execute("""
                INSERT INTO cache_metadata
                (entity_id, entity_type, last_synced, link_count, sync_source)
                VALUES (?, ?, CURRENT_TIMESTAMP, ?, 'collection_record')
                ON CONFLICT (entity_id)
                DO UPDATE SET
                    entity_type = EXCLUDED.entity_type,
                    last_synced = (SELECT CURRENT_TIMESTAMP),
                    link_count = EXCLUDED.link_count,
                    sync_source = EXCLUDED.sync_source
            """, [record_id, record_type, len(links)])

        return len(links)

    def get_stats(self) -> Dict:
        """Get cache statistics."""
        total_links = self.conn.execute("SELECT COUNT(*) FROM links").fetchone()[0]
        total_entities = self.conn.execute("SELECT COUNT(*) FROM cache_metadata").fetchone()[0]

        rel_types = self.conn.execute("""
            SELECT relationship_type, COUNT(*) as count
            FROM links
            GROUP BY relationship_type
            ORDER BY count DESC
        """).fetchall()

        oldest_sync = self.conn.execute("""
            SELECT MIN(last_synced) FROM cache_metadata
        """).fetchone()[0]

        newest_sync = self.conn.execute("""
            SELECT MAX(last_synced) FROM cache_metadata
        """).fetchone()[0]

        return {
            'total_links': total_links,
            'total_entities_cached': total_entities,
            'relationship_types': dict(rel_types),
            'oldest_sync': oldest_sync,
            'newest_sync': newest_sync,
            'cache_path': str(self.cache_path)
        }

    def clear_cache(self, entity_id: Optional[str] = None):
        """
        Clear cache.

        Parameters
        ----------
        entity_id : str, optional
            If provided, clear only links for this entity.
            If None, clear entire cache.
        """
        if entity_id:
            self.conn.execute("""
                DELETE FROM links
                WHERE source_id = ? OR target_id = ?
            """, [entity_id, entity_id])
            self.conn.execute("DELETE FROM cache_metadata WHERE entity_id = ?", [entity_id])
            logger.info(f"Cleared cache for {entity_id}")
        else:
            self.conn.execute("DELETE FROM links")
            self.conn.execute("DELETE FROM cache_metadata")
            logger.info("Cleared entire link cache")

    def close(self):
        """Close database connection."""
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
