# -*- coding: utf-8 -*-
from nmdc_api_utilities.collection_search import CollectionSearch
from nmdc_api_utilities.constants import DEFAULT_API_BASE_URL
import logging


logger = logging.getLogger(__name__)


class CollectingBiosamplesFromSiteSearch(CollectionSearch):
    """
    Class to interact with the NMDC API to get "collecting biosamples from site" records.
    """

    def __init__(self, api_base_url: str = DEFAULT_API_BASE_URL):
        super().__init__(
            collection_name="collecting_biosamples_from_site_set",
            api_base_url=api_base_url,
        )
