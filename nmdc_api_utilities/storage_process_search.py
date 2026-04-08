# -*- coding: utf-8 -*-
from nmdc_api_utilities.collection_search import CollectionSearch
from nmdc_api_utilities.config import API_BASE_URL
import logging

logger = logging.getLogger(__name__)


class StorageProcessSearch(CollectionSearch):
    """
    Class to interact with the NMDC API to get storage processes.
    """

    def __init__(self, api_base_url: str = API_BASE_URL, env: str = ""):
        super().__init__(
            collection_name="storage_process_set",
            api_base_url=api_base_url,
            env=env,
        )
