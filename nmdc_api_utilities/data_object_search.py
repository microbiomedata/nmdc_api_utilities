# -*- coding: utf-8 -*-
from nmdc_api_utilities.collection_search import CollectionSearch
import logging
import requests
import urllib.parse
logger = logging.getLogger(__name__)


class DataObjectSearch(CollectionSearch):
    """
    Class to interact with the NMDC API to get data object sets.
    """

    def __init__(self, env="prod"):
        super().__init__(collection_name="data_object_set", env=env)

    def get_data_objects_for_studies(self, study_id: str, max_page_size: int = 100):
        """
        Get data objects by study id.
        """
        url = f"{self.base_url}/data_objects/study/{study_id}?max_page_size={max_page_size}"
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error("API request failed", exc_info=True)
            raise RuntimeError("Failed to get data_objects from NMDC API") from e
        else:
            logging.debug(
                f"API request response: {response.json()}\n API Status Code: {response.status_code}"
            )

        results = response.json()

        return results
    
    