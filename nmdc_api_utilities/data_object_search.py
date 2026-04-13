# -*- coding: utf-8 -*-

import logging

import requests

from nmdc_api_utilities.collection_search import CollectionSearch
from nmdc_api_utilities.config import API_BASE_URL

logger = logging.getLogger(__name__)


class DataObjectSearch(CollectionSearch):
    """
    Class to interact with the NMDC API to get data objects.
    """

    def __init__(self, api_base_url: str = API_BASE_URL, env: str = ""):
        super().__init__(
            collection_name="data_object_set",
            api_base_url=api_base_url,
            env=env,
        )

    def get_data_objects_for_study(self, study_id: str) -> list[dict]:
        """
        Gets all data objects related to all biosamples associated with the specified study.

        Parameters
        ----------
        study_id: str
            The ID of the study.
        Returns
        -------
        list[dict]
            The data objects.
        Raises
        ------
        RuntimeError
            If the API request fails.
        """
        url = f"{self.api_base_url}/data_objects/study/{study_id}"
        try:
            response = requests.get(
                url,
                headers=self._build_http_request_headers(),
            )
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
