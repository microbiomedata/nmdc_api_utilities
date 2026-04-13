# -*- coding: utf-8 -*-
import logging

from nmdc_api_utilities.config import API_BASE_URL
from nmdc_api_utilities.data_object_search import DataObjectSearch

logging.basicConfig(level=logging.DEBUG)


def test_get_data_objects_for_study():
    """
    Test the get_data_objects_for_study method.
    """
    do_search = DataObjectSearch(api_base_url=API_BASE_URL)

    study_id = "nmdc:sty-11-aygzgv51"
    results = do_search.get_data_objects_for_study(study_id)
    logging.debug(f"Results: {results}")
    assert results
    assert len(results) > 0
    assert "data_objects" in results[0]
