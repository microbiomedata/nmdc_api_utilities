# -*- coding: utf-8 -*-
from nmdc_api_utilities.collection_search import CollectionSearch
from nmdc_api_utilities.config import API_BASE_URL
import logging


logger = logging.getLogger(__name__)


class ChemicalEntitySearch(CollectionSearch):
    """
    Class to interact with the NMDC API to get chemical entities.
    """

    def __init__(self, api_base_url: str = API_BASE_URL):
        super().__init__(
            collection_name="chemical_entity_set", api_base_url=api_base_url
        )
