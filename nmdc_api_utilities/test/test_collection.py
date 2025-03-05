# -*- coding: utf-8 -*-
from nmdc_api_utilities.collection_search import CollectionSearch


def test_get_collection():
    # testing the filters
    collection = CollectionSearch()
    results = collection.get_record("study_set")
    assert len(results) > 0


def test_get_collection_data_object_by_type():
    collection = CollectionSearch()
    results = collection.get_record_data_object_by_type(
        "data_object_set", "nmdc:bsm-11-002vgm56"
    )
    assert len(results) > 0
