# -*- coding: utf-8 -*-
from nmdc_api_utilities.metadata import Metadata
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
ENV = os.getenv("ENV")


def test_validate():
    metadata = Metadata(env=ENV)
    results = metadata.validate_json("nmdc_api_utilities/test/test_data/test.json")
    assert results == 200
