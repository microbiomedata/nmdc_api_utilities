# -*- coding: utf-8 -*-
import logging
from nmdc_api_utilities.collection_search import CollectionSearch
from nmdc_api_utilities.constants import DEFAULT_API_BASE_URL

logger = logging.getLogger(__name__)


class StudySearch(CollectionSearch):
    """
    Class to interact with the NMDC API to get studies.
    """

    def __init__(self, api_base_url: str = DEFAULT_API_BASE_URL):
        super().__init__(collection_name="study_set", api_base_url=api_base_url)
