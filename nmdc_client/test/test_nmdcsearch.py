# -*- coding: utf-8 -*-
import logging

from nmdc_client import NMDCSearch
from nmdc_client.config import API_BASE_URL

logging.basicConfig(level=logging.DEBUG)


def test_get_records_by_id():
    nmdc_client = NMDCSearch(api_base_url=API_BASE_URL)
    ids = [
        "nmdc:sty-11-8fb6t785",
        "nmdc:bsm-11-002vgm56",
        "nmdc:bsm-11-006pnx90",
        "nmdc:bsm-11-00dkyf35",
        "nmdc:dobj-11-0001ab10",
        "nmdc:dobj-11-00095294",
    ]
    resp = nmdc_client.get_records_by_id(ids=ids, fields="id,name")

    assert len(resp) == len(ids)


def test_get_schema_version():
    nmdc_client = NMDCSearch(api_base_url=API_BASE_URL)
    schema_version = nmdc_client.get_schema_version()
    logging.debug(f"NMDC Schema Version: {schema_version}")
    assert isinstance(schema_version, str)


def test_get_record_from_id():
    nmdc_client = NMDCSearch(api_base_url=API_BASE_URL)
    record = nmdc_client.get_record_from_id("nmdc:sty-11-8fb6t785", fields="id,name")
    logging.debug(f"Record fetched from ID: {record}")
    assert record["id"] == "nmdc:sty-11-8fb6t785"


def test_get_collection_name_from_id():
    ch = NMDCSearch(api_base_url=API_BASE_URL)
    result = ch.get_collection_name_from_id("nmdc:sty-11-8fb6t785")
    assert result == "study_set"
