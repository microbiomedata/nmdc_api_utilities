# -*- coding: utf-8 -*-
from nmdc_api_utilities.collection_search import CollectionSearch
from nmdc_api_utilities.constants import DEFAULT_API_BASE_URL
from nmdc_api_utilities.lat_long_filters import LatLongFilters
import logging

logger = logging.getLogger(__name__)


class FieldResearchSiteSearch(LatLongFilters, CollectionSearch):
    """
    Class to interact with the NMDC API to get field research sites.
    """

    def __init__(self, api_base_url: str = DEFAULT_API_BASE_URL):
        super().__init__("field_research_site_set", api_base_url=api_base_url)
