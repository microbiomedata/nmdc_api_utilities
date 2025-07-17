# -*- coding: utf-8 -*-
from nmdc_api_utilities.nmdc_search import NMDCSearch
import logging
import requests
import oauthlib
import requests_oauthlib
import json

logger = logging.getLogger(__name__)


class Minter(NMDCSearch):
    """
    Class to interact with the NMDC API to mint new identifiers.
    """

    def __init__(self, env="prod"):
        super().__init__(env=env)

    def mint(
        self, nmdc_type: str, client_id: str, client_secret: str, count: int = 1
    ) -> str | list[str]:
        """
        Mint new identifier(s) for a collection.

        Parameters
        ----------
        nmdc_type : str
            The type of NMDC ID to mint (e.g., 'nmdc:MassSpectrometry',
            'nmdc:DataObject').
        client_id : str
            The client ID for the NMDC API.
        client_secret : str
            The client secret for the NMDC API.
        count : int, optional
            The number of identifiers to mint. Default is 1.

        Returns
        -------
        str or list[str]
            If count is 1, returns a single minted identifier as a string.
            If count is greater than 1, returns a list of minted identifiers.

        Raises
        ------
        RuntimeError
            If the API request fails.
        ValueError
            If count is less than 1.

        Notes
        -----
        Security Warning: Your client_id and client_secret should be stored in a secure location.
            We recommend using environment variables.
            Do not hard code these values in your code.

        """
        # Validate count parameter
        if count < 1:
            raise ValueError("count must be at least 1")

        # get the token
        client = oauthlib.oauth2.BackendApplicationClient(client_id=client_id)
        oauth = requests_oauthlib.OAuth2Session(client=client)
        oauth.fetch_token(
            token_url=f"{self.base_url}/token",
            client_id=client_id,
            client_secret=client_secret,
        )
        url = f"{self.base_url}/pids/mint"
        payload = {"schema_class": {"id": nmdc_type}, "how_many": count}
        try:
            response = oauth.post(url, data=json.dumps(payload))
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error("API request failed", exc_info=True)
            raise RuntimeError("Failed to mint new identifier from NMDC API") from e
        else:
            logging.debug(
                f"API request response: {response.json()}\n API Status Code: {response.status_code}"
            )
        # return the response
        response_data = response.json()
        if count == 1:
            return response_data[0]
        else:
            return response_data
