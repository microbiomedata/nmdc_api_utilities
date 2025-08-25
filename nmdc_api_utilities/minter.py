# -*- coding: utf-8 -*-
from nmdc_api_utilities.nmdc_search import NMDCSearch
import logging
import requests
from nmdc_api_utilities.auth import NMDCAuth
from nmdc_api_utilities.decorators import requires_auth
import json

logger = logging.getLogger(__name__)


class Minter(NMDCSearch):
    """
    Class to interact with the NMDC API to mint new identifiers.

    Parameters
    ----------
    auth : NMDCAuth
        An instance of the NMDCAuth class for authentication.
    """

    def __init__(self, env="prod", auth: NMDCAuth = None):
        self.env = env
        self.auth = auth or NMDCAuth()
        super().__init__(env=env)

    @requires_auth
    def mint(
        self,
        nmdc_type: str,
        count: int = 1,
        client_id: str = None,
        client_secret: str = None,
    ) -> str | list[str]:
        """
        Mint new identifier(s) for a collection.

        Parameters
        ----------
        nmdc_type : str
            The type of NMDC ID to mint (e.g., 'nmdc:MassSpectrometry',
            'nmdc:DataObject').

        count : int, optional
            The number of identifiers to mint. Default is 1.

        client_id : str
            The client ID for authentication. Kept for backwards compatibility.

        client_secret : str
            The client secret for authentication. Kept for backwards compatibility.

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

        Note
        ----
        If client_id and client_secret are provided, a new NMDCAuth object will be created. The newest and preferred method for authentication is to use the NMDCAuth class directly.

        """
        # if they are passed into the function, create the auth object
        if client_id and client_secret:
            self.auth = NMDCAuth(
                client_id=client_id, client_secret=client_secret, env=self.env
            )
        # Validate count parameter
        if count < 1:
            raise ValueError("count must be at least 1")

        # get the token
        token = self.auth.get_token()

        url = f"{self.base_url}/pids/mint"
        payload = {"schema_class": {"id": nmdc_type}, "how_many": count}
        try:
            response = requests.post(
                url,
                headers={"Authorization": f"Bearer {token}"},
                data=json.dumps(payload),
            )
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
