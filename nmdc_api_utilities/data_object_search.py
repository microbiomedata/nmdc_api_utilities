# -*- coding: utf-8 -*-

import logging
import warnings
from typing import Optional

import requests

from nmdc_api_utilities.collection_search import CollectionSearch
from nmdc_api_utilities.config import API_BASE_URL
from nmdc_api_utilities.lib.deprecation import deprecated, has_deprecated_parameter

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

    @has_deprecated_parameter(
        parameter_name="max_page_size", stacklevel=2, footnote="It has no effect."
    )
    @deprecated("Use ``get_data_objects_for_study`` instead.", stacklevel=2)
    def get_data_objects_for_studies(
        self,
        study_id: str,
        max_page_size: Optional[int] = None,
    ) -> list[dict]:
        """
        .. deprecated:: 0.6.2 Use the ``get_data_objects_for_study`` method instead.
        """

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
