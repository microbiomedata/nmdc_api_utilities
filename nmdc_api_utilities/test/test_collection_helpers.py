# -*- coding: utf-8 -*-
from nmdc_api_utilities.collection_helpers import CollectionHelpers


def test_get_record_name_from_id(env):
    ch = CollectionHelpers(env=env)
    result = ch.get_record_name_from_id("nmdc:sty-11-8fb6t785")
    assert result == "study_set"
