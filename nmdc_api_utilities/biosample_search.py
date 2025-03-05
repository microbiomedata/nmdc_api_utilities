# -*- coding: utf-8 -*-
from nmdc_api_utilities.collection_search import CollectionSearch
from nmdc_api_utilities.lat_long_filters import LatLongFilters
import logging

logger = logging.getLogger(__name__)


class BiosampleSearch(LatLongFilters, CollectionSearch):
    """
    Class to interact with the NMDC API to get biosamples.
    """

    def __init__(self):
        super().__init__("biosample_set")
