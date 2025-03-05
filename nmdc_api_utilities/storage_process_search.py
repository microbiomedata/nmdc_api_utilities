# -*- coding: utf-8 -*-
from nmdc_api_utilities.collection_search import CollectionSearch
import logging

logger = logging.getLogger(__name__)


class StorageProcessSearch(CollectionSearch):
    """
    Class to interact with the NMDC API to get storage process sets.
    """

    def __init__(self):
        super().__init__("storage_process_set")
