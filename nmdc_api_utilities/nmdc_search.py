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
        self.env = env

    def get_linked_instances(
        self,
        ids: list[str] | str,
        hydrate: bool = False,
        types: list[str] | str = None,
        max_page_size: int = 500,
    ) -> list[dict]:
        """
        Given a list of input ids, get the linked records from the NMDC API.

        Parameters
        ----------
        ids : list[str] | str
            The ids to search for.
        hydrate : bool = False
            Whether to include full documents in the response. The default is False.
        types : list[str] | str = None
            The types of instances you want to return. Default is None, which returns all types.
        max_page_size : int = 500
            The maximum number of records to return per page. Default is 500.

        Returns
        -------
        list[dict]
            A list of linked instance records.
        """
        # highest number I could get to without a timeout
        batch_size = 250
        batch_records = []
        url = f"{self.base_url}/nmdcschema/linked_instances"
        # split the ids into batches
        for i in range(0, len(ids), batch_size):
            batch = ids[i : i + batch_size]
            params = {
                "types": types,
                "ids": batch,
                "hydrate": hydrate,
                "max_page_size": max_page_size,
            }
            response = requests.get(url=url, params=params)
            if response.status_code == 200:
                batch_resources = response.json().get("resources", [])
                next_page = response.json().get("next_page_token", None)
                batch_records.extend(batch_resources)
                if next_page:
                    while next_page:
                        params = {
                            "types": types,
                            "ids": batch,
                            "page_token": next_page,
                        }
                        response = requests.get(url=url, params=params)
                        if response.status_code == 200:
                            batch_resources = response.json().get("resources", [])
                            batch_records.extend(batch_resources)
                            next_page = response.json().get("next_page_token", None)
            else:
                raise RuntimeError(
                    f"Error fetching linked instances: {response.status_code} {response.text}"
                )
        return batch_records

    def get_linked_instances_and_associate_ids(
        self,
        ids: list[str] | str,
        types: list[str] | str = None,
        hydrate: bool = False,
        max_page_size: int = 500,
    ) -> dict[str, list[str]]:
        """
        Given a list of ids, find the associated linked mongo records and
        return a dictionary mapping each id to its linked instances.
        Example:
            If I want to find all the Mongo records (studies, data objects, mass spectrometry records, etc) associated with the biosample `nmdc:bsm-11-002vgm56`
            This function would return to me a dictionary where `nmdc:bsm-11-002vgm56` is the key, and the value is a list of ids that are related to it:
            {"nmdc:bsm-11-002vgm56": ["nmdc:sty-11-nxrz9m96", "nmdc:sty-11-34xj1150"]}

        Parameters
        ----------
        ids : list[str] | str
            The ids to search for.
        types : list[str] | str = None
            The types of instances you want to return. Default is None, which returns all types.
        hydrate : bool = False
            Whether to include full documents in the response. The default is False.
        max_page_size : int = 500
            The maximum number of records to return per page. Default is 500.

        Returns
        -------
        dict[str, list[str]]
            A dictionary mapping each input id to a list of its linked instance records.
        """
        # get the linked instances
        linked_instances = self.get_linked_instances(
            types=types, ids=ids, hydrate=hydrate, max_page_size=max_page_size
        )
        association = {}
        # loop through the linked instances and build the association
        for record in linked_instances:
            study_id = record["id"]
            if "_upstream_of" in record:
                for upstream_id in record["_upstream_of"]:
                    if upstream_id not in association:
                        association[upstream_id] = []
                    association[upstream_id].append(study_id)
            if "_downstream_of" in record:
                for upstream_id in record["_downstream_of"]:
                    if upstream_id not in association:
                        association[upstream_id] = []
                    association[upstream_id].append(study_id)

        return association

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

    def get_records_by_id(self, id: str) -> dict:
        """
        Retrieve records by their ID.

        Parameters
        ----------
        id : str
            The ID of the record to retrieve.

        Returns
        -------
        dict
            The record data.
        """
        collection_name = self.get_record_name_from_id(id)
        url = f"{self.base_url}/{collection_name}/{id}"
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
        return response.json()
