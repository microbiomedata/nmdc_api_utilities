# -*- coding: utf-8 -*-
from nmdc_api_utilities.nmdc_search import NMDCSearch
import requests
import logging

logger = logging.getLogger(__name__)


class CollectionHelpers(NMDCSearch):
    """
    Class to interact with the NMDC API to get additional information about collections.
    These functions may not be specific to a particular collection.
    """

    def __init__(self, env="prod"):
        super().__init__(env=env)

    def get_record_name_from_id(self, doc_id: str) -> str:
        """
        Used when you have an id but not the collection name.
        Determine the schema class by which the id belongs to.

        Parameters
        ----------
        doc_id: str
            The id of the document.

        Returns
        -------
        str
            The collection name of the document.

        Raises
        ------
        RuntimeError
            If the API request fails.

        """
        url = f"{self.base_url}/nmdcschema/ids/{doc_id}/collection-name"
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error("API request failed", exc_info=True)
            raise RuntimeError("Failed to get record from NMDC API") from e
        else:
            logging.debug(
                f"API request response: {response.json()}\n API Status Code: {response.status_code}"
            )

        collection_name = response.json()["collection_name"]
        return collection_name
