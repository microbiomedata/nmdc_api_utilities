# -*- coding: utf-8 -*-
import os

from dotenv import load_dotenv

from nmdc_api_utilities.metadata import Metadata

load_dotenv()
ENV = os.getenv("ENV")


def test_validate():
    metadata = Metadata(env=ENV)
    results = metadata.validate_json("nmdc_api_utilities/test/test_data/test.json")
    assert results == 200
