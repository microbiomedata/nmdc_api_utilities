# -*- coding: utf-8 -*-
import logging

from nmdc_api_utilities.config import API_BASE_URL
from nmdc_api_utilities.functional_search import FunctionalSearch

logger = logging.getLogger(__name__)


class FunctionalAnnotationAggSearch(FunctionalSearch):
    """
    Class to interact with the NMDC API to search for records within the ``functional_annotation_agg`` collection.

    These are most helpful when trying to identify workflows associated with a KEGG, COG, or PFAM ids.
    """

    def __init__(self, api_base_url: str = API_BASE_URL, env: str = ""):
        super().__init__(
            api_base_url=api_base_url,
            env=env,
        )
