# -*- coding: utf-8 -*-
import logging
import requests

logger = logging.getLogger(__name__)


class NMDCSearch:
    """
    Base class for interacting with the NMDC API. Sets the base URL for the API based on the environment.
    Environment is defaulted to the production isntance of the API. This functionality is in place for monthly testing of the runtime updates to the API.

    Parameters
    ----------
    env: str
        The environment to use. Default is prod. Must be one of the following:
            prod
            dev

    """

    def __init__(self, env="prod"):
        if env == "prod":
            self.base_url = "https://api.microbiomedata.org"
        elif env == "dev":
            self.base_url = "https://api-dev.microbiomedata.org"
        else:
            raise ValueError("env must be one of the following: prod, dev")

    def _get_all_pages(
        self,
        response: requests.Response,
        url_prefix: str,
        filter: str = "",
        max_page_size: int = 100,
        fields: str = "",
    ):
        """
        Get all pages of data from the NMDC API. This is a helper function to get all pages of data from the NMDC API.

        Parameters
        ----------
        response: requests.Response
            The response object from the API request. Do not modify before passing in.
        url_prefix: str
            The URL prefix for the API endpoint.
        filter: str
            The filter to apply to the query. Default is an empty string.
        max_page_size: int
            The maximum number of items to return per page. Default is 100.
        fields: str
            The fields to return. Default is all fields.

        Returns
        -------
        list[dict]
            A list of dictionaries containing the records.

        Raises
        ------
        RuntimeError
            If the API request fails.

        """

        results = response.json()

        while True:
            if response.json().get("next_page_token"):
                next_page_token = response.json()["next_page_token"]
            else:
                break
            url = f"{url_prefix}?filter={filter}&max_page_size={max_page_size}&projection={fields}&page_token={next_page_token}"
            try:
                response = requests.get(url)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                logger.error("API request failed", exc_info=True)
                raise RuntimeError("Failed to get collection from NMDC API") from e
            else:
                logging.debug(
                    f"API request response: {response.json()}\n API Status Code: {response.status_code}"
                )
            results = {"resources": results["resources"] + response.json()["resources"]}
        return results
