# -*- coding: utf-8 -*-
import logging

from nmdc_api_utilities.collection_search import CollectionSearch
from nmdc_api_utilities.config import API_BASE_URL
from nmdc_api_utilities.decorators import has_deprecated_parameter

logger = logging.getLogger(__name__)


@has_deprecated_parameter("env", reason="Use ``api_base_url`` instead.")
class ProcessedSampleSearch(CollectionSearch):
    """
    Class to interact with the NMDC API to search for records within the ``processed_sample_set`` collection.
    """

    def __init__(self, api_base_url: str = API_BASE_URL, env: str = ""):
        super().__init__(
            collection_name="processed_sample_set",
            api_base_url=api_base_url,
            env=env,
        )
