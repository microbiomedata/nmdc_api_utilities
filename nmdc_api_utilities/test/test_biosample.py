# -*- coding: utf-8 -*-
from nmdc_api_utilities.biosample_search import BiosampleSearch
import logging
from nmdc_api_utilities.data_processing import DataProcessing


def test_find_biosample_by_id():
    biosample = BiosampleSearch()
    results = biosample.get_record_by_id("nmdc:bsm-11-002vgm56")
    assert len(results) > 0
    assert results["id"] == "nmdc:bsm-11-002vgm56"


def test_logger():
    biosample = BiosampleSearch()
    logging.basicConfig(level=logging.DEBUG)
    results = biosample.get_record_by_id("nmdc:bsm-11-002vgm56")


def test_biosample_by_filter():
    biosample = BiosampleSearch()
    results = biosample.get_record_by_filter('{"id":"nmdc:bsm-11-006pnx90"}')
    assert len(results) > 0


def test_biosample_by_attribute():
    biosample = BiosampleSearch()
    results = biosample.get_record_by_attribute(
        "id", "nmdc:bsm-11-006pnx90", exact_match=True
    )
    print(results)
    assert len(results) == 1


def test_biosample_by_latitude():
    # {"lat_lon.latitude": {"$gt": 45.0}, "lat_lon.longitude": {"$lt":45}}
    biosample = BiosampleSearch()
    results = biosample.get_record_by_latitude("gt", 45.0)
    assert len(results) > 0
    assert results[0]["lat_lon"]["latitude"] == 63.875088


def test_biosample_by_longitude():
    # {"lat_lon.latitude": {"$gt": 45.0}, "lat_lon.longitude": {"$lt":45}}
    biosample = BiosampleSearch()
    results = biosample.get_record_by_longitude("lt", 45.0)
    assert len(results) > 0
    assert results[0]["lat_lon"]["longitude"] == -149.210438


def test_biosample_by_lat_long():
    # {"lat_lon.latitude": {"$gt": 45.0}, "lat_lon.longitude": {"$lt":45}}
    biosample = BiosampleSearch()
    results = biosample.get_record_by_lat_long("gt", "lt", 45.0, 45.0)
    assert len(results) > 0
    assert results[0]["lat_lon"]["latitude"] == 63.875088
    assert results[0]["lat_lon"]["longitude"] == -149.210438


def test_biosample_build_filter_1():
    u = DataProcessing()
    b = BiosampleSearch()
    filter = u.build_filter({"name": "G6R2_NF_20JUN2016"})
    results = b.get_record_by_filter(filter)
    print(results)
    assert len(results) == 1


def test_biosample_build_filter_2():
    u = DataProcessing()
    b = BiosampleSearch()
    filter = u.build_filter({"name": "G6R2_NF_20JUN2016", "id": "nmdc:bsm-11-006pnx90"})
    results = b.get_record_by_filter(filter)
    print(results)
    assert len(results) == 1
