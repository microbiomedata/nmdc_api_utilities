# -*- coding: utf-8 -*-
import json
import logging

import requests

from nmdc_api_utilities.api_client import NMDCAPIClient
from nmdc_api_utilities.auth import NMDCAuth
from nmdc_api_utilities.config import API_BASE_URL
from nmdc_api_utilities.decorators import requires_auth

logger = logging.getLogger(__name__)


class Metadata(NMDCAPIClient):
    """
    Class to interact with the NMDC API metadata endpoints.

    This class includes methods for interacting with endpoints for metadata management, including validation and submission and is not intended for general/public use.

    Parameters
    ----------
    api_base_url : str
        The base URL of the NMDC API.
    auth : NMDCAuth
        An instance of the NMDCAuth class for authentication.
    """

    def __init__(
        self,
        api_base_url: str = API_BASE_URL,
        auth: NMDCAuth = None,
        env: str = "",
    ):
        super().__init__(
            api_base_url=api_base_url,
            env=env,
        )
        self.auth = auth or NMDCAuth(api_base_url=self.api_base_url)

    def validate_json(self, json_records: list[dict] | str) -> int:
        """
        Validates a json file using the NMDC json validate endpoint.

        If the validation passes, the method returns without any side effects.

        Parameters
        ----------
        json_records : list[dict] | str
            The json records to be validated. Can be passed in as a file path or list of dictionaries.

        Returns
        -------
        int
            The HTTP status code of the validation request.

        Raises
        ------
        Exception
            If the validation fails.
        """
        if isinstance(json_records, str):
            with open(json_records, "r") as f:
                data = json.load(f)
        else:
            data = json_records

        # Check that the term "placeholder" is not present anywhere in the json
        if "placeholder" in json.dumps(data):
            raise Exception("Placeholder values found in json!")

        url = f"{self.api_base_url}/metadata/json:validate"
        headers = self._build_http_request_headers(
            accept="application/json",
            content_type="application/json",
        )
        response = requests.post(url, headers=headers, json=data)
        if response.text != '{"result":"All Okay!"}' or response.status_code != 200:
            logging.error(f"Validation failed.")
            raise Exception(
                f"Validation failed with the following information:\n"
                f"Status Code: {response.status_code}\n"
                f"Response: {response.text}"
            )
        else:
            logging.info("Validation passed!")

        return response.status_code

    @requires_auth
    def submit_json(self, json_records: list[dict] | str) -> int:
        """
        Submits a json file to the NMDC metadata database via the NMDC runtime API's json_submit endpoint.

        Parameters
        ----------
        json_records : list[dict] | str
            The json records to be submitted. Can be passed in as a file path or list of dictionaries.

        Returns
        -------
        int
            The HTTP status code of the submission request.

        Raises
        ------
        Exception
            If the submission fails.

        """
        # if a file is passed in, load the json
        if isinstance(json_records, str):
            with open(json_records, "r") as f:
                json_records = json.load(f)

        token = self.auth.get_token()

        # api request
        url = f"{self.api_base_url}/metadata/json:submit"
        headers = self._build_http_request_headers(
            access_token=token,
            accept="application/json",
            content_type="application/json",
        )
        response = requests.post(url, headers=headers, json=json_records)

        # error handling
        if response.status_code != 200:
            logging.error(f"Request failed with response {response.text}")
            raise Exception(
                "Submission failed with the following information:\n"
                f"Status Code: {response.status_code}\n"
                f"Response: {response.text}"
            )
        else:
            logging.info("Submission passed!")

        return response.status_code
