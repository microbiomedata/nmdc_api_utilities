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
    resp = nmdc_client.get_records_by_id(
        id="nmdc:sty-11-8fb6t785", max_page_size=20, fields="id,name", all_pages=False
    )
    logging.debug(f"Record fetched by ID: {resp}")
    assert len(resp) == 20


def test_get_schema_version():
    nmdc_client = NMDCSearch(env=ENV)
    schema_version = nmdc_client.get_schema_version()
    logging.debug(f"NMDC Schema Version: {schema_version}")
    assert isinstance(schema_version, str)
