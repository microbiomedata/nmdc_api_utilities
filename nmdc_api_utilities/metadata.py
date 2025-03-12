# -*- coding: utf-8 -*-
from nmdc_api_utilities.nmdc_search import NMDCSearch
import requests
import logging
import json

logger = logging.getLogger(__name__)
class Metadata(NMDCSearch):
    """
    Class to interact with the NMDC API metadata. 
    """
    def __init__(self, env="prod"):
        super().__init__(env=env)

    def validate_json(self, json_path) -> None:
        """
        Validates a json file using the NMDC json validate endpoint.

        If the validation passes, the method returns without any side effects.

        Parameters
        ----------
        json_path : str
            The path to the json file to be validated.

        Raises
        ------
        Exception
            If the validation fails.
        """
        with open(json_path, "r") as f:
            data = json.load(f)

        # Check that the term "placeholder" is not present anywhere in the json
        if "placeholder" in json.dumps(data):
            raise Exception("Placeholder values found in json!")

        url = f"{self.base_url}/metadata/json:validate"
        headers = {"accept": "application/json", "Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json=data)
        if response.text != '{"result":"All Okay!"}' or response.status_code != 200:
            logging.error(f"Request failed with response {response.text}")
            raise Exception("Validation failed")
        else:
            logging.info("Validation passed")