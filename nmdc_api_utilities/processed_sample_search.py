# -*- coding: utf-8 -*-
import logging

from nmdc_api_utilities.collection_search import CollectionSearch
from nmdc_api_utilities.config import API_BASE_URL

logger = logging.getLogger(__name__)


class ProcessedSampleSearch(CollectionSearch):
    """
    Class to interact with the NMDC API to get processed samples.
    """

    def __init__(self, api_base_url: str = API_BASE_URL, env: str = ""):
        super().__init__(
            collection_name="processed_sample_set",
            api_base_url=api_base_url,
            env=env,
        )
