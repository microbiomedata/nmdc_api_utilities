# -*- coding: utf-8 -*-
from nmdc_api_utilities.biosample_search import BiosampleSearch
import logging
from nmdc_api_utilities.data_processing import DataProcessing

logging.basicConfig(level=logging.DEBUG)


def test_find_biosample_by_id(env):
    biosample = BiosampleSearch(env=env)
    results = biosample.get_record_by_id("nmdc:bsm-11-002vgm56")
    assert len(results) > 0
    assert results["id"] == "nmdc:bsm-11-002vgm56"


def test_logger(env):
    biosample = BiosampleSearch(env=env)
    logging.basicConfig(level=logging.DEBUG)
    results = biosample.get_record_by_id("nmdc:bsm-11-002vgm56")


def test_biosample_by_filter(env):
    biosample = BiosampleSearch(env=env)
    results = biosample.get_record_by_filter('{"id":"nmdc:bsm-11-006pnx90"}')
    assert len(results) > 0


def test_biosample_by_attribute(env):
    biosample = BiosampleSearch(env=env)
    results = biosample.get_record_by_attribute(
        "id", "nmdc:bsm-11-006pnx90", exact_match=False
    )
    logging.debug(results)
    assert len(results) == 1


def test_biosample_by_latitude(env):
    # {"lat_lon.latitude": {"$gt": 45.0}, "lat_lon.longitude": {"$lt":45}}
    biosample = BiosampleSearch(env=env)
    results = biosample.get_record_by_latitude("gt", 45.0)
    assert len(results) > 0
    assert results[0]["lat_lon"]["latitude"] == 63.875088


def test_biosample_by_longitude(env):
    # {"lat_lon.latitude": {"$gt": 45.0}, "lat_lon.longitude": {"$lt":45}}
    biosample = BiosampleSearch(env=env)
    results = biosample.get_record_by_longitude("lt", 45.0)
    assert len(results) > 0
    assert results[0]["lat_lon"]["longitude"] == -149.210438


def test_biosample_by_lat_long(env):
    # {"lat_lon.latitude": {"$gt": 45.0}, "lat_lon.longitude": {"$lt":45}}
    biosample = BiosampleSearch(env=env)
    results = biosample.get_record_by_lat_long("gt", "lt", 45.0, 45.0)
    assert len(results) > 0
    assert results[0]["lat_lon"]["latitude"] == 63.875088
    assert results[0]["lat_lon"]["longitude"] == -149.210438


def test_biosample_build_filter_1(env):
    u = DataProcessing()
    b = BiosampleSearch(env=env)
    filter = u.build_filter({"name": "G6R2_NF_20JUN2016"})
    results = b.get_record_by_filter(filter)
    print(results)
    assert len(results) == 1


def test_biosample_build_filter_2(env):
    u = DataProcessing()
    b = BiosampleSearch(env=env)
    filter = u.build_filter({"name": "G6R2_NF_20JUN2016", "id": "nmdc:bsm-11-006pnx90"})
    logging.debug("Biosample test filter:", filter)
    results = b.get_record_by_filter(filter)
    assert len(results) == 1
