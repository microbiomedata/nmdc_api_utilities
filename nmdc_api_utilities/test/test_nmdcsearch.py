# -*- coding: utf-8 -*-
import logging
import pytest
from dotenv import load_dotenv
import os

load_dotenv()
ENV = os.getenv("ENV")
logging.basicConfig(level=logging.DEBUG)
from nmdc_api_utilities.nmdc_search import NMDCSearch


def test_base_url_prod():
    nmdc_client = NMDCSearch(env="prod")
    assert nmdc_client.base_url == "https://api.microbiomedata.org"


def test_base_url_dev():
    nmdc_client = NMDCSearch(env="dev")
    assert nmdc_client.base_url == "https://api-dev.microbiomedata.org"


def test_base_url_custom():
    custom_url = "http://localhost:8000"
    nmdc_client = NMDCSearch(env="custom", base_url=custom_url)
    assert nmdc_client.base_url == custom_url


def test_base_url_custom_trailing_slash_stripped():
    nmdc_client = NMDCSearch(env="custom", base_url="http://localhost:8000/")
    assert nmdc_client.base_url == "http://localhost:8000"


def test_base_url_custom_missing_base_url():
    with pytest.raises(ValueError, match="base_url"):
        NMDCSearch(env="custom")


def test_base_url_invalid():
    with pytest.raises(ValueError, match="Invalid value for env"):
        NMDCSearch(env="not-a-valid-value")


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
