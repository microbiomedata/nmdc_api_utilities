# -*- coding: utf-8 -*-
import logging

from nmdc_client.collection_search import CollectionSearch
from nmdc_client.config import API_BASE_URL

logger = logging.getLogger(__name__)


class MaterialProcessingSearch(CollectionSearch):
    """
    Class to interact with the NMDC API to search for records within the ``material_processing_set`` collection.
    """

    def __init__(self, api_base_url: str = API_BASE_URL, env: str = ""):
        super().__init__(
            collection_name="material_processing_set",
            api_base_url=api_base_url,
            env=env,
        )
