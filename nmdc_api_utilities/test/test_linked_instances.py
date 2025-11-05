# -*- coding: utf-8 -*-
"""Tests for linked instances functionality."""
import logging
import pytest
from nmdc_api_utilities.linked_instances_search import LinkedInstancesSearch
from nmdc_api_utilities.biosample_search import BiosampleSearch
from nmdc_api_utilities.study_search import StudySearch
from nmdc_api_utilities.data_object_search import DataObjectSearch

logging.basicConfig(level=logging.DEBUG)


# LinkedInstancesSearch tests
def test_linked_instances_basic(env):
    """Test basic linked instances query."""
    client = LinkedInstancesSearch(env=env)
    results = client.get_linked_instances(
        ids=["nmdc:bsm-11-x5xj6p33"],
        types=["nmdc:Study"],
        hydrate=False,
        max_page_size=10,
        all_pages=False
    )
    assert isinstance(results, list)
    assert len(results) > 0
    assert results[0]["type"] == "nmdc:Study"


def test_linked_instances_data_objects(env):
    """Test finding data objects linked to a biosample."""
    client = LinkedInstancesSearch(env=env)
    results = client.get_linked_instances(
        ids=["nmdc:bsm-11-x5xj6p33"],
        types=["nmdc:DataObject"],
        hydrate=False,
        max_page_size=10,
        all_pages=False
    )
    assert isinstance(results, list)
    assert len(results) > 0
    assert all(r["type"] == "nmdc:DataObject" for r in results)


def test_linked_instances_by_direction(env):
    """Test get_linked_by_direction method."""
    client = LinkedInstancesSearch(env=env)
    results = client.get_linked_by_direction(
        ids=["nmdc:bsm-11-x5xj6p33"],
        types=["nmdc:Study"],
        direction="upstream",
        hydrate=False,
        max_page_size=10
    )
    assert isinstance(results, dict)
    assert "upstream" in results
    assert len(results["upstream"]) > 0


def test_linked_instances_validation_empty_ids(env):
    """Test that empty ids raises ValueError."""
    client = LinkedInstancesSearch(env=env)
    with pytest.raises(ValueError, match="ids must be a non-empty list"):
        client.get_linked_instances(ids=[], types=["nmdc:Study"])


def test_linked_instances_validation_invalid_direction(env):
    """Test that invalid direction raises ValueError."""
    client = LinkedInstancesSearch(env=env)
    with pytest.raises(ValueError, match="direction must be"):
        client.get_linked_by_direction(
            ids=["nmdc:bsm-11-x5xj6p33"],
            direction="invalid"
        )


# BiosampleSearch linking tests
def test_biosample_get_linked_studies(env):
    """Test BiosampleSearch.get_linked_studies method."""
    client = BiosampleSearch(env=env)
    results = client.get_linked_studies("nmdc:bsm-11-x5xj6p33", hydrate=True)
    assert isinstance(results, list)
    assert len(results) > 0
    assert all(s["type"] == "nmdc:Study" for s in results)
    # Check that hydration worked
    assert "title" in results[0] or "description" in results[0]


def test_biosample_get_linked_data_objects(env):
    """Test BiosampleSearch.get_linked_data_objects method."""
    client = BiosampleSearch(env=env)
    results = client.get_linked_data_objects("nmdc:bsm-11-x5xj6p33", hydrate=False)
    assert isinstance(results, list)
    assert len(results) > 0
    assert all(d["type"] == "nmdc:DataObject" for d in results)


def test_biosample_get_linked_data_objects_with_filter(env):
    """Test BiosampleSearch.get_linked_data_objects with type filter."""
    client = BiosampleSearch(env=env)
    results = client.get_linked_data_objects(
        "nmdc:bsm-11-x5xj6p33",
        hydrate=True,
        data_object_types=["Metagenome Raw Reads"]
    )
    assert isinstance(results, list)
    # If any results, they should all be the filtered type
    for obj in results:
        assert obj.get("data_object_type") == "Metagenome Raw Reads"


# StudySearch linking tests
def test_study_get_linked_biosamples(env):
    """Test StudySearch.get_linked_biosamples method."""
    client = StudySearch(env=env)
    results = client.get_linked_biosamples("nmdc:sty-11-547rwq94", hydrate=False)
    assert isinstance(results, list)
    assert len(results) > 0
    assert all(b["type"] == "nmdc:Biosample" for b in results)


def test_study_get_all_linked_data_objects_list(env):
    """Test StudySearch.get_all_linked_data_objects returning list."""
    client = StudySearch(env=env)
    results = client.get_all_linked_data_objects(
        "nmdc:sty-11-547rwq94",
        hydrate=False,
        group_by_type=False
    )
    assert isinstance(results, list)
    assert len(results) > 0
    assert all(d["type"] == "nmdc:DataObject" for d in results)


def test_study_get_all_linked_data_objects_grouped(env):
    """Test StudySearch.get_all_linked_data_objects returning grouped dict."""
    client = StudySearch(env=env)
    results = client.get_all_linked_data_objects(
        "nmdc:sty-11-547rwq94",
        hydrate=True,
        group_by_type=True
    )
    assert isinstance(results, dict)
    # Should have at least one data object type
    assert len(results) > 0
    # Each value should be a list
    for obj_type, objects in results.items():
        assert isinstance(objects, list)
        assert all(obj.get("data_object_type") == obj_type for obj in objects)


# DataObjectSearch linking tests
def test_data_object_get_linked_biosample(env):
    """Test DataObjectSearch.get_linked_biosample method."""
    client = DataObjectSearch(env=env)
    results = client.get_linked_biosample("nmdc:dobj-11-nf3t6f36", hydrate=True)
    assert isinstance(results, list)
    assert len(results) > 0
    assert all(b["type"] == "nmdc:Biosample" for b in results)


def test_data_object_get_linked_study(env):
    """Test DataObjectSearch.get_linked_study method."""
    client = DataObjectSearch(env=env)
    results = client.get_linked_study("nmdc:dobj-11-nf3t6f36", hydrate=True)
    assert isinstance(results, list)
    assert len(results) > 0
    assert all(s["type"] == "nmdc:Study" for s in results)


def test_data_object_get_provenance_chain(env):
    """Test DataObjectSearch.get_provenance_chain method."""
    client = DataObjectSearch(env=env)
    provenance = client.get_provenance_chain("nmdc:dobj-11-nf3t6f36", hydrate=False)

    # Should return dict with specific keys
    assert isinstance(provenance, dict)
    expected_keys = {
        "biosamples", "studies", "workflow_executions",
        "data_generations", "processed_samples", "data_objects"
    }
    assert set(provenance.keys()) == expected_keys

    # Should have at least biosamples and studies
    assert len(provenance["biosamples"]) > 0
    assert len(provenance["studies"]) > 0

    # Check types
    for biosample in provenance["biosamples"]:
        assert biosample["type"] == "nmdc:Biosample"
    for study in provenance["studies"]:
        assert study["type"] == "nmdc:Study"


def test_data_object_get_provenance_chain_hydrated(env):
    """Test DataObjectSearch.get_provenance_chain with hydration."""
    client = DataObjectSearch(env=env)
    provenance = client.get_provenance_chain("nmdc:dobj-11-nf3t6f36", hydrate=True)

    # With hydration, entities should have more fields
    if provenance["biosamples"]:
        # Check that hydration worked
        biosample = provenance["biosamples"][0]
        assert "id" in biosample
        # Should have more than just id and type
        assert len(biosample.keys()) > 3


# Integration tests
def test_integration_biosample_to_study_to_data_objects(env):
    """Test complete workflow: biosample -> study -> data objects."""
    # Start with a biosample
    biosample_client = BiosampleSearch(env=env)
    biosample_id = "nmdc:bsm-11-x5xj6p33"

    # Get linked studies
    studies = biosample_client.get_linked_studies(biosample_id, hydrate=False)
    assert len(studies) > 0
    study_id = studies[0]["id"]

    # Get data objects for that study
    study_client = StudySearch(env=env)
    data_objects = study_client.get_all_linked_data_objects(
        study_id,
        hydrate=False,
        group_by_type=False
    )
    assert len(data_objects) > 0


def test_integration_data_object_to_biosample_to_study(env):
    """Test complete workflow: data object -> biosample -> study."""
    # Start with a data object
    data_obj_client = DataObjectSearch(env=env)
    data_obj_id = "nmdc:dobj-11-nf3t6f36"

    # Get linked biosample
    biosamples = data_obj_client.get_linked_biosample(data_obj_id, hydrate=False)
    assert len(biosamples) > 0
    biosample_id = biosamples[0]["id"]

    # Get study from biosample
    biosample_client = BiosampleSearch(env=env)
    studies = biosample_client.get_linked_studies(biosample_id, hydrate=False)
    assert len(studies) > 0

    # Verify we can also get study directly from data object
    direct_studies = data_obj_client.get_linked_study(data_obj_id, hydrate=False)
    assert len(direct_studies) > 0
    assert direct_studies[0]["id"] == studies[0]["id"]
