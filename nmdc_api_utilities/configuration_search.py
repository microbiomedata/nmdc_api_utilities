# -*- coding: utf-8 -*-
from nmdc_api_utilities.collection_search import CollectionSearch
import logging

logger = logging.getLogger(__name__)


class ConfigurationSearch(CollectionSearch):
    """
    Class to interact with the NMDC API to get cofiguration sets.
    """

    def __init__(self, env="Production"):
        super().__init__(collection_name="configuration_set", env=env)
