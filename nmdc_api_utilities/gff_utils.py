# -*- coding: utf-8 -*-
"""
GFF utilities for NMDC functional annotation files.

This module provides efficient parsing and querying of NMDC GFF files using DuckDB.
NMDC GFF files contain functional annotations with attributes like EC numbers, PFAM,
COG, KEGG orthologs, etc.

Examples
--------
Load and query a GFF file:

>>> from nmdc_api_utilities.gff_utils import GFFReader
>>> reader = GFFReader("path/to/annotations.gff")
>>>
>>> # Query by EC number
>>> kinases = reader.query_by_ec("2.7.%")  # All kinases (EC 2.7.x.x)
>>>
>>> # Query by PFAM domain
>>> abc_transporters = reader.query_by_pfam("PF00005")
>>>
>>> # Query by location
>>> region = reader.query_region("contig_001", 1000, 5000)
>>>
>>> # Find biosynthetic gene clusters
>>> bgcs = reader.find_bgc_candidates(min_genes=5, max_distance=10000)

Use with optional DuckDB for better performance:

>>> # Create an in-memory DuckDB database
>>> reader = GFFReader("path/to/annotations.gff", use_duckdb=True)
>>>
>>> # Or persist to disk for reuse
>>> reader = GFFReader("path/to/annotations.gff",
...                    use_duckdb=True,
...                    db_path="annotations.duckdb")
>>>
>>> # Run custom SQL queries
>>> results = reader.query("SELECT * FROM features WHERE strand = '+' AND score > 100")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Union, Optional, List, Dict, Any
import re

logger = logging.getLogger(__name__)


class GFFReader:
    """
    Efficient reader for NMDC GFF functional annotation files.

    This class parses GFF files and optionally loads them into DuckDB
    for fast querying. It provides specialized methods for common NMDC
    queries like searching by EC number, PFAM domain, or genomic location.

    Parameters
    ----------
    gff_path : Union[str, Path]
        Path to the GFF file
    use_duckdb : bool, optional
        Whether to use DuckDB for queries (default: True)
    db_path : Union[str, Path, None], optional
        Path to DuckDB database file. If None, uses in-memory database
    lazy_load : bool, optional
        If True, don't parse file until first query (default: False)

    Attributes
    ----------
    gff_path : Path
        Path to the GFF file
    use_duckdb : bool
        Whether DuckDB is being used
    db_path : Optional[Path]
        Path to DuckDB database if persisted

    Examples
    --------
    Basic usage with pandas (no DuckDB):

    >>> reader = GFFReader("annotations.gff", use_duckdb=False)
    >>> print(f"Loaded {len(reader.df)} features")

    With DuckDB for better performance:

    >>> reader = GFFReader("annotations.gff", use_duckdb=True)
    >>> kinases = reader.query_by_ec("2.7.%")
    >>> print(f"Found {len(kinases)} kinases")
    """

    def __init__(
        self,
        gff_path: Union[str, Path],
        use_duckdb: bool = True,
        db_path: Union[str, Path, None] = None,
        lazy_load: bool = False
    ):
        self.gff_path = Path(gff_path)
        self.use_duckdb = use_duckdb
        self.db_path = Path(db_path) if db_path else None
        self._df = None
        self._conn = None

        if not self.gff_path.exists():
            raise FileNotFoundError(f"GFF file not found: {self.gff_path}")

        if not lazy_load:
            self._load()

    def _load(self):
        """Load and parse the GFF file."""
        logger.info(f"Loading GFF file: {self.gff_path}")

        if self.use_duckdb:
            self._load_with_duckdb()
        else:
            self._load_with_pandas()

    def _parse_attributes(self, attr_string: str) -> Dict[str, str]:
        """
        Parse GFF attribute string into a dictionary.

        Parameters
        ----------
        attr_string : str
            GFF attribute string (e.g., "ID=gene1;product=kinase;ec_number=EC:2.7.1.1")

        Returns
        -------
        Dict[str, str]
            Dictionary of attribute key-value pairs

        Examples
        --------
        >>> reader = GFFReader("test.gff", lazy_load=True)
        >>> attrs = reader._parse_attributes("ID=gene1;product=kinase;ec_number=EC:2.7.1.1")
        >>> attrs["ec_number"]
        'EC:2.7.1.1'
        """
        attributes = {}
        for item in attr_string.split(";"):
            item = item.strip()
            if "=" in item:
                key, value = item.split("=", 1)
                attributes[key] = value
        return attributes

    def _load_with_pandas(self):
        """Load GFF using pandas (fallback method)."""
        import pandas as pd

        # Read GFF file (tab-separated, no header)
        logger.info("Parsing GFF with pandas...")
        df = pd.read_csv(
            self.gff_path,
            sep="\t",
            header=None,
            comment="#",
            names=["seqid", "source", "type", "start", "end", "score", "strand", "phase", "attributes"]
        )

        # Parse attributes into separate columns
        logger.info("Parsing GFF attributes...")
        parsed_attrs = df["attributes"].apply(self._parse_attributes)

        # Extract common attributes into columns
        for key in ["ID", "product", "ec_number", "pfam", "cog", "ko", "tigrfam",
                    "smart", "cath_funfam", "superfamily", "product_source"]:
            df[key] = parsed_attrs.apply(lambda x: x.get(key, None))

        # Handle PFAM IDs in the type column (HMMER GFF format)
        # Some GFF files (particularly from HMMER) have the PFAM ID in column 3 (type)
        # instead of in the attributes. Pattern: PF followed by 5 digits
        pfam_pattern = re.compile(r'^PF\d{5}$')
        type_is_pfam = df["type"].apply(lambda x: bool(pfam_pattern.match(str(x))) if pd.notna(x) else False)

        # If type column contains PFAM ID and pfam column is empty, use type as pfam
        df.loc[type_is_pfam & df["pfam"].isna(), "pfam"] = df.loc[type_is_pfam & df["pfam"].isna(), "type"]

        # Log how many features have PFAM from type column
        pfam_from_type_count = type_is_pfam.sum()
        if pfam_from_type_count > 0:
            logger.info(f"Found {pfam_from_type_count} features with PFAM ID in type column")

        self._df = df
        logger.info(f"Loaded {len(df)} features")

    def _load_with_duckdb(self):
        """Load GFF into DuckDB for efficient querying."""
        try:
            import duckdb
        except ImportError:
            logger.warning("DuckDB not available. Install with: pip install duckdb")
            logger.info("Falling back to pandas...")
            self.use_duckdb = False
            self._load_with_pandas()
            return

        # Create connection
        if self.db_path:
            logger.info(f"Creating DuckDB database: {self.db_path}")
            self._conn = duckdb.connect(str(self.db_path))
        else:
            logger.info("Creating in-memory DuckDB database")
            self._conn = duckdb.connect(":memory:")

        # First load with pandas to parse attributes
        self._load_with_pandas()

        # Register the dataframe as a DuckDB table
        logger.info("Loading data into DuckDB...")
        self._conn.register("df_temp", self._df)
        self._conn.execute("CREATE TABLE features AS SELECT * FROM df_temp")

        # Create indexes for common queries
        logger.info("Creating indexes...")
        self._conn.execute("CREATE INDEX idx_seqid ON features(seqid)")
        self._conn.execute("CREATE INDEX idx_type ON features(type)")
        self._conn.execute("CREATE INDEX idx_start ON features(start)")
        self._conn.execute('CREATE INDEX idx_end ON features("end")')

        logger.info("GFF loaded into DuckDB successfully")

    @property
    def df(self):
        """Get the pandas DataFrame of GFF features."""
        if self._df is None:
            self._load()
        return self._df

    @property
    def conn(self):
        """Get the DuckDB connection (if using DuckDB)."""
        if self.use_duckdb and self._conn is None:
            self._load()
        return self._conn

    def query(self, sql: str) -> "pd.DataFrame":
        """
        Execute a SQL query on the GFF data.

        Parameters
        ----------
        sql : str
            SQL query string. Table name is 'features'.

        Returns
        -------
        pd.DataFrame
            Query results

        Examples
        --------
        >>> reader = GFFReader("annotations.gff")
        >>> high_score = reader.query("SELECT * FROM features WHERE score > 100")
        >>> kinases = reader.query("SELECT * FROM features WHERE ec_number LIKE '2.7.%'")
        """
        if self.use_duckdb:
            return self.conn.execute(sql).df()
        else:
            # Fallback to pandas query (limited SQL support)
            raise NotImplementedError("SQL queries require DuckDB. Set use_duckdb=True")

    def query_by_ec(self, ec_pattern: str) -> "pd.DataFrame":
        """
        Query features by EC number pattern.

        Parameters
        ----------
        ec_pattern : str
            EC number pattern (e.g., "2.7.1.1" for exact match, "2.7.%" for all kinases)

        Returns
        -------
        pd.DataFrame
            Features matching the EC number pattern

        Examples
        --------
        >>> reader = GFFReader("annotations.gff")
        >>> kinases = reader.query_by_ec("2.7.%")  # All kinases
        >>> hexokinases = reader.query_by_ec("2.7.1.%")  # Phosphotransferases with OH group
        """
        if self.use_duckdb:
            return self.query(f"SELECT * FROM features WHERE ec_number LIKE '%{ec_pattern}%'")
        else:
            return self.df[self.df["ec_number"].str.contains(ec_pattern, na=False)]

    def query_by_pfam(self, pfam_id: str) -> "pd.DataFrame":
        """
        Query features by PFAM domain ID.

        Parameters
        ----------
        pfam_id : str
            PFAM ID (e.g., "PF00005" for ABC transporter)

        Returns
        -------
        pd.DataFrame
            Features containing the PFAM domain

        Examples
        --------
        >>> reader = GFFReader("annotations.gff")
        >>> abc_transporters = reader.query_by_pfam("PF00005")
        """
        if self.use_duckdb:
            return self.query(f"SELECT * FROM features WHERE pfam LIKE '%{pfam_id}%'")
        else:
            return self.df[self.df["pfam"].str.contains(pfam_id, na=False)]

    def query_by_cog(self, cog_id: str) -> "pd.DataFrame":
        """
        Query features by COG ID.

        Parameters
        ----------
        cog_id : str
            COG ID (e.g., "COG0001")

        Returns
        -------
        pd.DataFrame
            Features with the COG annotation

        Examples
        --------
        >>> reader = GFFReader("annotations.gff")
        >>> features = reader.query_by_cog("COG0001")
        """
        if self.use_duckdb:
            return self.query(f"SELECT * FROM features WHERE cog LIKE '%{cog_id}%'")
        else:
            return self.df[self.df["cog"].str.contains(cog_id, na=False)]

    def query_by_ko(self, ko_id: str) -> "pd.DataFrame":
        """
        Query features by KEGG Orthology ID.

        Parameters
        ----------
        ko_id : str
            KO ID (e.g., "K00001" or "KO:K00001")

        Returns
        -------
        pd.DataFrame
            Features with the KO annotation

        Examples
        --------
        >>> reader = GFFReader("annotations.gff")
        >>> features = reader.query_by_ko("K00001")
        """
        if self.use_duckdb:
            return self.query(f"SELECT * FROM features WHERE ko LIKE '%{ko_id}%'")
        else:
            return self.df[self.df["ko"].str.contains(ko_id, na=False)]

    def query_region(
        self,
        seqid: str,
        start: int,
        end: int,
        feature_type: Optional[str] = None
    ) -> "pd.DataFrame":
        """
        Query features in a genomic region.

        Parameters
        ----------
        seqid : str
            Sequence/contig ID
        start : int
            Start position (1-based, inclusive)
        end : int
            End position (1-based, inclusive)
        feature_type : str, optional
            Filter by feature type (e.g., "CDS", "tRNA")

        Returns
        -------
        pd.DataFrame
            Features overlapping the region

        Examples
        --------
        >>> reader = GFFReader("annotations.gff")
        >>> region = reader.query_region("nmdc:wfmgan-11-ddkkwt71.1_000001", 1000, 5000)
        >>> cds_only = reader.query_region("contig_1", 1000, 5000, feature_type="CDS")
        """
        # Features overlap if: feature.start <= region.end AND feature.end >= region.start
        if self.use_duckdb:
            query = f"""
                SELECT * FROM features
                WHERE seqid = '{seqid}'
                AND start <= {end}
                AND "end" >= {start}
            """
            if feature_type:
                query += f" AND type = '{feature_type}'"
            return self.query(query)
        else:
            mask = (
                (self.df["seqid"] == seqid) &
                (self.df["start"] <= end) &
                (self.df["end"] >= start)
            )
            if feature_type:
                mask = mask & (self.df["type"] == feature_type)
            return self.df[mask]

    def find_bgc_candidates(
        self,
        min_genes: int = 5,
        max_distance: int = 10000,
        required_annotations: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find candidate biosynthetic gene clusters (BGCs).

        A BGC candidate is a genomic region with multiple genes in close proximity,
        potentially with specific functional annotations.

        Parameters
        ----------
        min_genes : int, optional
            Minimum number of genes in a cluster (default: 5)
        max_distance : int, optional
            Maximum distance between adjacent genes (default: 10000 bp)
        required_annotations : List[str], optional
            Required annotation types (e.g., ["PFAM", "EC"]) to consider a gene

        Returns
        -------
        List[Dict[str, Any]]
            List of BGC candidates, each with keys:
            - seqid: Sequence ID
            - start: Cluster start position
            - end: Cluster end position
            - gene_count: Number of genes
            - genes: List of gene IDs

        Examples
        --------
        >>> reader = GFFReader("annotations.gff")
        >>> bgcs = reader.find_bgc_candidates(min_genes=5, max_distance=10000)
        >>> print(f"Found {len(bgcs)} potential BGCs")

        >>> # Find BGCs with specific annotations
        >>> bgcs = reader.find_bgc_candidates(
        ...     min_genes=4,
        ...     required_annotations=["pfam", "ec_number"]
        ... )
        """
        # Get all CDS features, sorted by position
        if self.use_duckdb:
            cds = self.query('SELECT * FROM features WHERE type = \'CDS\' ORDER BY seqid, start')
        else:
            cds = self.df[self.df["type"] == "CDS"].sort_values(["seqid", "start"])

        clusters = []
        current_cluster = []
        current_seqid = None

        for idx, gene in cds.iterrows():
            # Check if gene has required annotations
            if required_annotations:
                has_required = any(
                    gene.get(ann) is not None and str(gene.get(ann)) != "nan"
                    for ann in required_annotations
                )
                if not has_required:
                    continue

            # Start new cluster if on different sequence
            if gene["seqid"] != current_seqid:
                if len(current_cluster) >= min_genes:
                    clusters.append(self._create_cluster_dict(current_cluster))
                current_cluster = [gene]
                current_seqid = gene["seqid"]
                continue

            # Check distance to last gene in cluster
            if current_cluster:
                last_gene = current_cluster[-1]
                distance = gene["start"] - last_gene["end"]

                if distance <= max_distance:
                    # Add to current cluster
                    current_cluster.append(gene)
                else:
                    # Save cluster and start new one
                    if len(current_cluster) >= min_genes:
                        clusters.append(self._create_cluster_dict(current_cluster))
                    current_cluster = [gene]
            else:
                current_cluster = [gene]

        # Don't forget the last cluster
        if len(current_cluster) >= min_genes:
            clusters.append(self._create_cluster_dict(current_cluster))

        logger.info(f"Found {len(clusters)} BGC candidates")
        return clusters

    def _create_cluster_dict(self, genes: List) -> Dict[str, Any]:
        """Create a dictionary representing a gene cluster."""
        return {
            "seqid": genes[0]["seqid"],
            "start": int(genes[0]["start"]),
            "end": int(genes[-1]["end"]),
            "gene_count": len(genes),
            "genes": [g["ID"] for g in genes],
            "annotations": {
                "ec_numbers": list({g.get("ec_number") for g in genes if g.get("ec_number")}),
                "pfams": list({g.get("pfam") for g in genes if g.get("pfam")}),
                "cogs": list({g.get("cog") for g in genes if g.get("cog")}),
            }
        }

    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics about the GFF file.

        Returns
        -------
        Dict[str, Any]
            Summary statistics including:
            - total_features: Total number of features
            - feature_types: Count of each feature type
            - sequences: List of sequence IDs
            - has_ec: Number of features with EC numbers
            - has_pfam: Number of features with PFAM domains
            - has_cog: Number of features with COG annotations

        Examples
        --------
        >>> reader = GFFReader("annotations.gff")
        >>> stats = reader.get_summary_stats()
        >>> print(f"Total features: {stats['total_features']}")
        >>> print(f"CDS count: {stats['feature_types']['CDS']}")
        """
        df = self.df

        return {
            "total_features": len(df),
            "feature_types": df["type"].value_counts().to_dict(),
            "sequences": df["seqid"].unique().tolist(),
            "has_ec": df["ec_number"].notna().sum(),
            "has_pfam": df["pfam"].notna().sum(),
            "has_cog": df["cog"].notna().sum(),
            "has_ko": df["ko"].notna().sum(),
        }

    def export_to_tsv(
        self,
        output_path: Union[str, Path],
        columns: Optional[List[str]] = None
    ):
        """
        Export GFF data to a TSV file.

        Parameters
        ----------
        output_path : Union[str, Path]
            Output file path
        columns : List[str], optional
            Columns to export. If None, exports all columns.

        Examples
        --------
        >>> reader = GFFReader("annotations.gff")
        >>> reader.export_to_tsv("annotations_table.tsv")
        >>>
        >>> # Export only specific columns
        >>> reader.export_to_tsv(
        ...     "ec_annotations.tsv",
        ...     columns=["seqid", "start", "end", "strand", "ec_number", "product"]
        ... )
        """
        df = self.df
        if columns:
            df = df[columns]
        df.to_csv(output_path, sep="\t", index=False)
        logger.info(f"Exported to {output_path}")

    def close(self):
        """Close the DuckDB connection (if open)."""
        if self._conn:
            self._conn.close()
            logger.info("DuckDB connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __repr__(self):
        if self._df is not None:
            return f"GFFReader({self.gff_path}, features={len(self.df)}, duckdb={self.use_duckdb})"
        return f"GFFReader({self.gff_path}, lazy_load=True)"


def load_gff(
    gff_path: Union[str, Path],
    use_duckdb: bool = True,
    db_path: Union[str, Path, None] = None
) -> GFFReader:
    """
    Convenience function to load a GFF file.

    Parameters
    ----------
    gff_path : Union[str, Path]
        Path to GFF file
    use_duckdb : bool, optional
        Whether to use DuckDB (default: True)
    db_path : Union[str, Path, None], optional
        Path to persist DuckDB database

    Returns
    -------
    GFFReader
        Loaded GFF reader

    Examples
    --------
    >>> from nmdc_api_utilities.gff_utils import load_gff
    >>> reader = load_gff("annotations.gff")
    >>> kinases = reader.query_by_ec("2.7.%")
    """
    return GFFReader(gff_path, use_duckdb=use_duckdb, db_path=db_path)
