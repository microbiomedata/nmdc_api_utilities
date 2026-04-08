# -*- coding: utf-8 -*-
from nmdc_api_utilities.config import API_BASE_URL
from nmdc_api_utilities.metadata import Metadata


def test_validate():
    metadata = Metadata(api_base_url=API_BASE_URL)
    results = metadata.validate_json("nmdc_api_utilities/test/test_data/test.json")
    assert results == 200
