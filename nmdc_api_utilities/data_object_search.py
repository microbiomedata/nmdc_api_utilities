# -*- coding: utf-8 -*-

import logging
import warnings
from typing import Optional

import requests

from nmdc_api_utilities.collection_search import CollectionSearch
from nmdc_api_utilities.config import API_BASE_URL

logger = logging.getLogger(__name__)


class DataObjectSearch(CollectionSearch):
    """
    Class to interact with the NMDC API to search for records within the ``data_object_set`` collection.
    """

    def __init__(self, api_base_url: str = API_BASE_URL, env: str = ""):
        super().__init__(
            collection_name="data_object_set",
            api_base_url=api_base_url,
            env=env,
        )

    def get_data_objects_for_studies(
        self,
        study_id: str,
        max_page_size: Optional[int] = None,
    ) -> list[dict]:
        """
        (Deprecated) This method is deprecated. Use `get_data_objects_for_study` instead.
        """

        warnings.warn(
            "The `get_data_objects_for_studies` method is deprecated and will be removed in "
            "a future release. Use the `get_data_objects_for_study` method instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )

        if max_page_size is not None:
            warnings.warn(
                "The `max_page_size` parameter is deprecated and will be removed in "
                "a future release. It has no effect.",
                category=DeprecationWarning,
                stacklevel=2,
            )

        return self.get_data_objects_for_study(study_id)

    def get_data_objects_for_study(self, study_id: str) -> list[dict]:
        """
        Get all data objects related to the specified study.

        Parameters
        ----------
        study_id
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
