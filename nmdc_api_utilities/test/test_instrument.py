from nmdc_api_utilities.instrument_search import InstrumentSearch
import logging
from dotenv import load_dotenv
import os
import pytest
load_dotenv()
ENV = os.getenv("ENV")
logging.basicConfig(level=logging.DEBUG)


def test_get_by_non_standard_attribute():
    """
    Test to get a record by a non-standard attribute.
    """
    is_client = InstrumentSearch(env=ENV)
    instrument_name = "Agilent GC-MS (2009)"
    result = is_client.get_record_by_attribute(
            attribute_name="name", attribute_value=instrument_name
        )
    logging.debug(result)
    assert len(result) > 0
    assert result[0]["name"] == instrument_name

def test_get_by_standard_attribute():
    """
    Test to get a record by a standard attribute.
    """
    is_client = InstrumentSearch(env = ENV)
    instrument_name = "Agilent GC-MS"
    result = is_client.get_record_by_attribute(
            attribute_name="name", attribute_value=instrument_name
        )
    logging.debug(result)
    assert len(result) == 1
    assert instrument_name in result[0]["name"]

test_get_by_non_standard_attribute()