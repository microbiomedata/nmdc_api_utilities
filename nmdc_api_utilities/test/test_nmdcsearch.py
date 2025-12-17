# -*- coding: utf-8 -*-
import logging
from dotenv import load_dotenv
import os

load_dotenv()
ENV = os.getenv("ENV")
logging.basicConfig(level=logging.DEBUG)
from nmdc_api_utilities.nmdc_search import NMDCSearch


def test_get_records_by_id():
    nmdc_client = NMDCSearch(env=ENV)
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
    nmdc_client = NMDCSearch(env=ENV)
    schema_version = nmdc_client.get_schema_version()
    logging.debug(f"NMDC Schema Version: {schema_version}")
    assert isinstance(schema_version, str)


def test_get_record_from_id():
    nmdc_client = NMDCSearch(env=ENV)
    record = nmdc_client.get_record_from_id("nmdc:sty-11-8fb6t785", fields="id,name")
    logging.debug(f"Record fetched from ID: {record}")
    assert record["id"] == "nmdc:sty-11-8fb6t785"


def test_get_collection_name_from_id():
    ch = NMDCSearch(env=ENV)
    result = ch.get_collection_name_from_id("nmdc:sty-11-8fb6t785")
    assert result == "study_set"
