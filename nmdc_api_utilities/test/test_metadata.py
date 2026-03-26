# -*- coding: utf-8 -*-
from nmdc_api_utilities.constants import DEFAULT_API_BASE_URL
from nmdc_api_utilities.metadata import Metadata
import os
from dotenv import load_dotenv

load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL)


def test_validate():
    metadata = Metadata(api_base_url=API_BASE_URL)
    results = metadata.validate_json("nmdc_api_utilities/test/test_data/test.json")
    assert results == 200
