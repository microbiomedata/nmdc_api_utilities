# -*- coding: utf-8 -*-
from nmdc_api_utilities.collection_helpers import CollectionHelpers
from dotenv import load_dotenv
import os

load_dotenv()
ENV = os.getenv("ENV")


def test_get_record_name_from_id():
    ch = CollectionHelpers(env=ENV)
    result = ch.get_record_name_from_id("nmdc:sty-11-8fb6t785")
    assert result == "study_set"
