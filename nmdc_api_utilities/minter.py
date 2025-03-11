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
    def __init__(self, env="Production"):
        super().__init__(env=env)
    def mint(self, nmdc_type:str, client_id: str, client_secret: str) -> str:
        """
        Mint a new identifier for a collection.
        params:
            nmdc_type : str
                The type of NMDC ID to mint (e.g., 'nmdc:MassSpectrometry',
                'nmdc:DataObject').
            client_id : str
                The client ID for the NMDC API.
            client_secret : str
                The client secret for the NMDC API.
        returns:
            str - the new identifier.
        Secrurity Note:
            Your client_id and client_secret should be stored in a secure location. We recommend using environment variables.
            Do not hard code these values in your code.
        """
        # get the token
        client = oauthlib.oauth2.BackendApplicationClient(client_id=client_id)
        oauth = requests_oauthlib.OAuth2Session(client=client)
        oauth.fetch_token(
            token_url=f"{self.base_url}/token",
            client_id=client_id,
            client_secret=client_secret,
        )
        url = f"{self.base_url}/pids/mint"
        payload = {"schema_class": {"id": nmdc_type}, "how_many": 1}
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
        return response.json()[0]