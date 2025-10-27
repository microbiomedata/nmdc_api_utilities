# -*- coding: utf-8 -*-
"""Tests for link caching functionality."""
import pytest
from pathlib import Path
import tempfile
import shutil

from nmdc_api_utilities.link_cache import LinkCache


@pytest.fixture
def temp_cache():
    """Create a temporary cache for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    cache_path = temp_dir / "test_links.db"

    cache = LinkCache(cache_path=cache_path)
    yield cache

    cache.close()
    shutil.rmtree(temp_dir)


def test_link_cache_init(temp_cache):
    """Test cache initialization."""
    assert temp_cache.cache_path.exists()


def test_add_single_link(temp_cache):
    """Test adding a single link."""
    temp_cache.add_link(
        source_id="nmdc:bsm-123",
        target_id="nmdc:sty-456",
        relationship_type="part_of",
        source_type="nmdc:Biosample",
        target_type="nmdc:Study"
    )

    links = temp_cache.get_links_for_id("nmdc:bsm-123")
    assert len(links) == 1
    assert links[0]["source_id"] == "nmdc:bsm-123"
    assert links[0]["target_id"] == "nmdc:sty-456"
    assert links[0]["relationship_type"] == "part_of"


def test_add_bulk_links(temp_cache):
    """Test adding multiple links at once."""
    links_data = [
        {
            "source_id": "nmdc:bsm-123",
            "target_id": "nmdc:sty-456",
            "relationship_type": "part_of",
            "source_type": "nmdc:Biosample",
            "target_type": "nmdc:Study"
        },
        {
            "source_id": "nmdc:bsm-123",
            "target_id": "nmdc:dobj-789",
            "relationship_type": "generated",
            "source_type": "nmdc:Biosample",
            "target_type": "nmdc:DataObject"
        }
    ]

    temp_cache.add_links_bulk(links_data)

    links = temp_cache.get_links_for_id("nmdc:bsm-123")
    assert len(links) == 2


def test_get_links_by_direction(temp_cache):
    """Test filtering links by direction."""
    # Add bidirectional links
    temp_cache.add_link("nmdc:bsm-123", "nmdc:sty-456", "part_of")
    temp_cache.add_link("nmdc:dobj-789", "nmdc:bsm-123", "generated_from")

    # Outgoing links
    outgoing = temp_cache.get_links_for_id("nmdc:bsm-123", direction="outgoing")
    assert len(outgoing) == 1
    assert outgoing[0]["target_id"] == "nmdc:sty-456"

    # Incoming links
    incoming = temp_cache.get_links_for_id("nmdc:bsm-123", direction="incoming")
    assert len(incoming) == 1
    assert incoming[0]["source_id"] == "nmdc:dobj-789"

    # Both directions
    both = temp_cache.get_links_for_id("nmdc:bsm-123", direction="both")
    assert len(both) == 2


def test_get_links_by_relationship_type(temp_cache):
    """Test filtering links by relationship type."""
    temp_cache.add_link("nmdc:bsm-123", "nmdc:sty-456", "part_of")
    temp_cache.add_link("nmdc:bsm-123", "nmdc:sty-789", "part_of")
    temp_cache.add_link("nmdc:bsm-123", "nmdc:dobj-111", "generated")

    part_of_links = temp_cache.get_links_for_id("nmdc:bsm-123", relationship_type="part_of")
    assert len(part_of_links) == 2

    generated_links = temp_cache.get_links_for_id("nmdc:bsm-123", relationship_type="generated")
    assert len(generated_links) == 1


def test_get_connected_ids(temp_cache):
    """Test getting connected entity IDs."""
    temp_cache.add_link("nmdc:bsm-123", "nmdc:sty-456", "part_of")
    temp_cache.add_link("nmdc:bsm-123", "nmdc:sty-789", "part_of")
    temp_cache.add_link("nmdc:dobj-111", "nmdc:bsm-123", "generated_from")

    connected = temp_cache.get_connected_ids("nmdc:bsm-123")
    assert len(connected) == 3
    assert "nmdc:sty-456" in connected
    assert "nmdc:sty-789" in connected
    assert "nmdc:dobj-111" in connected


def test_cache_from_collection_record(temp_cache):
    """Test extracting links from a biosample record."""
    biosample_record = {
        "id": "nmdc:bsm-123",
        "type": "nmdc:Biosample",
        "name": "Test Biosample",
        "associated_studies": ["nmdc:sty-456", "nmdc:sty-789"]
    }

    link_count = temp_cache.cache_from_collection_record(biosample_record)
    assert link_count == 2

    links = temp_cache.get_links_for_id("nmdc:bsm-123")
    assert len(links) == 2
    assert all(link["relationship_type"] == "part_of" for link in links)


def test_cache_from_linked_instances(temp_cache):
    """Test extracting links from linked_instances API response."""
    nexus_id = "nmdc:bsm-123"
    linked_instances_results = [
        {
            "id": "nmdc:sty-456",
            "type": "nmdc:Study",
            "_downstream_of": [nexus_id]
        },
        {
            "id": "nmdc:dobj-789",
            "type": "nmdc:DataObject",
            "_upstream_of": [nexus_id]
        }
    ]

    link_count = temp_cache.cache_from_linked_instances(linked_instances_results, nexus_id)
    assert link_count == 2

    links = temp_cache.get_links_for_id(nexus_id)
    assert len(links) == 2


def test_cache_stats(temp_cache):
    """Test getting cache statistics."""
    temp_cache.add_link("nmdc:bsm-123", "nmdc:sty-456", "part_of")
    temp_cache.add_link("nmdc:bsm-456", "nmdc:sty-456", "part_of")
    temp_cache.add_link("nmdc:dobj-789", "nmdc:bsm-123", "generated_from")

    # Need to update metadata to count entities
    temp_cache.conn.execute("""
        INSERT INTO cache_metadata (entity_id, entity_type, last_synced, link_count, sync_source)
        VALUES ('nmdc:bsm-123', 'nmdc:Biosample', CURRENT_TIMESTAMP, 1, 'manual')
    """)

    stats = temp_cache.get_stats()
    assert stats["total_links"] == 3
    assert stats["total_entities_cached"] == 1
    assert "part_of" in stats["relationship_types"]
    assert stats["relationship_types"]["part_of"] == 2


def test_clear_cache_for_entity(temp_cache):
    """Test clearing cache for a specific entity."""
    temp_cache.add_link("nmdc:bsm-123", "nmdc:sty-456", "part_of")
    temp_cache.add_link("nmdc:bsm-456", "nmdc:sty-456", "part_of")

    temp_cache.clear_cache(entity_id="nmdc:bsm-123")

    links_123 = temp_cache.get_links_for_id("nmdc:bsm-123")
    assert len(links_123) == 0

    links_456 = temp_cache.get_links_for_id("nmdc:bsm-456")
    assert len(links_456) == 1


def test_clear_entire_cache(temp_cache):
    """Test clearing the entire cache."""
    temp_cache.add_link("nmdc:bsm-123", "nmdc:sty-456", "part_of")
    temp_cache.add_link("nmdc:bsm-456", "nmdc:sty-789", "part_of")

    temp_cache.clear_cache()

    stats = temp_cache.get_stats()
    assert stats["total_links"] == 0
