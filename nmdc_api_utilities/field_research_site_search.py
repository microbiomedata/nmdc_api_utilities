# -*- coding: utf-8 -*-
from nmdc_api_utilities.collection_search import CollectionSearch
from nmdc_api_utilities.lat_long_filters import LatLongFilters
import logging

logger = logging.getLogger(__name__)

class FieldResearchSiteSearch(LatLongFilters, CollectionSearch):
    """
    Class to interact with the NMDC API to get field research site sets.
    """

    def __init__(self, env="prod"):
        super().__init__("field_research_site_set", env=env)
