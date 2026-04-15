# -*- coding: utf-8 -*-
import logging
import warnings
from abc import ABC
from typing import Optional

import requests

from nmdc_api_utilities import __version__ as package_version
from nmdc_api_utilities.config import API_BASE_URL, get_api_base_url

logger = logging.getLogger(__name__)


class NMDCAPIClient(ABC):
    """
    Abstract base class for interacting with NMDC Runtime API.

    Parameters
    ----------
    api_base_url: str
        The base URL of an instance of the NMDC Runtime API. By default, this is the base URL of
        the production instance. NMDC team members will occasionally set this to the base URL of
        a different instance; for example, a self-hosted instance used for testing.
    """

    def __init__(self, api_base_url: str = API_BASE_URL, env: str = ""):
        if env != "":
            # Note: We use `stacklevel=3` here so that, when the user instantiates a class that
            #       inherits from this abstract class, the warning shown by Python shows the line of
            #       code where the user instantiated that inheriting class. If we were to use
            #       `stacklevel=2` here, the warning would show the line of code where the
            #       inheriting class called the `__init__` method of its superclass (i.e. this
            #       method of this abstract class), which (unless the user has created their own
            #       class that inherits directly from this one) is not code that the user controls.
            #       Docs: https://docs.python.org/3/library/warnings.html#warnings.deprecated
            #
            warnings.warn(
                "`env` is deprecated and will be removed in a future release. "
                "Use `api_base_url` instead.",
                category=DeprecationWarning,
                stacklevel=3,
            )
        self.api_base_url = get_api_base_url(api_base_url=api_base_url, env=env)

    @staticmethod
    def _build_http_request_headers(
        access_token: Optional[str] = None,
        accept: Optional[str] = None,
        content_type: Optional[str] = None,
        additional_headers: Optional[dict[str, str]] = None,
    ) -> dict[str, str]:
        """
        Builds HTTP headers that can be included with HTTP requests sent by instances of this class
        and its subclasses.

        >>> from nmdc_api_utilities.api_client import NMDCAPIClient
        >>> headers = NMDCAPIClient._build_http_request_headers(
        ...     access_token="abc123",
        ...     accept="application/json",
        ...     additional_headers={"X-FOO": "BAR"},
        ... )
        >>> assert headers.keys() == {"User-Agent", "Authorization", "Accept", "X-FOO"}
        >>> assert headers["User-Agent"].startswith("nmdc-python-client/")
        >>> assert headers["Authorization"] == "Bearer abc123"
        >>> assert headers["Accept"] == "application/json"
        >>> assert headers["X-FOO"] == "BAR"
        """

        # Customize the "User-Agent" header so NMDC API administrators can distinguish requests
        # coming from this package from other requests. If this package is being run from source
        # instead of an installed distribution, the package version will be "0.0.0".
        user_agent = f"nmdc-python-client/{package_version}"
        headers = {"User-Agent": user_agent}

        if isinstance(access_token, str):
            headers["Authorization"] = f"Bearer {access_token}"
        if isinstance(accept, str):
            headers["Accept"] = accept
        if isinstance(content_type, str):
            headers["Content-Type"] = content_type
        if additional_headers is not None:
            headers.update(additional_headers)
        return headers

    def _get_all_pages(
        self,
        response: requests.Response,
        url_prefix: str,
        filter: str = "",
        max_page_size: int = 100,
        fields: str = "",
        access_token: Optional[str] = None,
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
        access_token: Optional[str]
            Optional access token to include in the API request.

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

            # Define the HTTP headers, which may include an access token.
            headers = self._build_http_request_headers(
                access_token=access_token,
                accept="application/json",
                content_type="application/json",
            )

            # TODO: Consider using the `params` argument of `requests.get` to handle building the
            #       URL's query string. That way, we would be delegating the responsibility of
            #       encoding query parameters, to the `requests` library.
            #       Reference: https://requests.readthedocs.io/en/latest/user/quickstart/#passing-parameters-in-urls
            #
            url = f"{url_prefix}?filter={filter}&max_page_size={max_page_size}&projection={fields}&page_token={next_page_token}"
            try:
                response = requests.get(url, headers=headers)
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
