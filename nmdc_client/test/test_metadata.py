# -*- coding: utf-8 -*-
from nmdc_client.config import API_BASE_URL
from nmdc_client.metadata import Metadata


def test_validate():
    metadata = Metadata(api_base_url=API_BASE_URL)
    results = metadata.validate_json("nmdc_client/test/test_data/test.json")
    assert results == 200
