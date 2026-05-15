# -*- coding: utf-8 -*-
import logging

from nmdc_api_utilities.collection_search import CollectionSearch
from nmdc_api_utilities.config import API_BASE_URL
from nmdc_api_utilities.decorators import has_deprecated_parameter
from nmdc_api_utilities.lat_long_filters import LatLongFilters

logger = logging.getLogger(__name__)


# Note: We specify the `CollectionSearch` class before the `LatLongFilters` class so that the
#       `BiosampleSearch` class uses the _concrete_ `get_records` method from the `CollectionSearch`
#       class (which is specified first) instead of the _abstract_ `get_records` method from the
#       `LatLongFilters` (which is specified later). An alternative would be to implement a concrete
#       "pass-through" method (here in `BiosampleSearch`) that, itself, explicitly invokes
#       `CollectionSearch.get_records(self, filter, max_page_size, fields, all_pages)`.
#       Docs: https://realpython.com/ref/glossary/mro/
#
@has_deprecated_parameter("env", reason="Use ``api_base_url`` instead.")
class BiosampleSearch(CollectionSearch, LatLongFilters):
    """
    Class to interact with the NMDC API to search for records within the ``biosample_set`` collection.
    """

    def __init__(self, api_base_url: str = API_BASE_URL, env: str = ""):
        super().__init__(
            collection_name="biosample_set",
            api_base_url=api_base_url,
            env=env,
        )
