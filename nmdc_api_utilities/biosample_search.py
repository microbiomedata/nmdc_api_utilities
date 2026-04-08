# -*- coding: utf-8 -*-
import logging

from nmdc_api_utilities.collection_search import CollectionSearch
from nmdc_api_utilities.config import API_BASE_URL
from nmdc_api_utilities.lat_long_filters import LatLongFilters

logger = logging.getLogger(__name__)


class BiosampleSearch(LatLongFilters, CollectionSearch):
    """
    Class to interact with the NMDC API to get biosamples.
    """

    def __init__(self, api_base_url: str = API_BASE_URL, env: str = ""):
        super().__init__(
            collection_name="biosample_set",
            api_base_url=api_base_url,
            env=env,
        )
