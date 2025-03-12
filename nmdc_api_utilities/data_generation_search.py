# -*- coding: utf-8 -*-
from nmdc_api_utilities.collection_search import CollectionSearch
import logging

logger = logging.getLogger(__name__)


class DataGenerationSearch(CollectionSearch):
    """
    Class to interact with the NMDC API to get data generation sets.
    """

    def __init__(self, env="prod"):
        super().__init__(collection_name="data_generation_set", env=env)
