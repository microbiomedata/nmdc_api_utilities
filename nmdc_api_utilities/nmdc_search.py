# -*- coding: utf-8 -*-
import logging
from typing import Any

import requests

from nmdc_api_utilities.api_client import NMDCAPIClient
from nmdc_api_utilities.config import API_BASE_URL

logger = logging.getLogger(__name__)


class NMDCSearch(NMDCAPIClient):
    """
    Class for interacting with the NMDC Runtime API for searching and retrieving records in the NMDC metadata database.

    Parameters
    ----------
    api_base_url: str
        The base URL of an instance of the NMDC Runtime API. By default, this is the base URL of
        the production instance. NMDC team members will occasionally set this to the base URL of
        a different instance; for example, a self-hosted instance used for testing.

    """

    def __init__(self, api_base_url: str = API_BASE_URL, env: str = ""):
        super().__init__(api_base_url=api_base_url, env=env)

    @staticmethod
    def _normalize_ids(ids: list[str] | str) -> list[str]:
        """Ensures the IDs are in a list, even if there is only one ID."""
        return ids if isinstance(ids, list) else [ids]

    def get_linked_instances(
        self,
        ids: list[str] | str,
        hydrate: bool = False,
        types: list[str] | str | None = None,
        max_page_size: int = 500,
    ) -> list[dict]:
        """
        Retrieve linked instances for the given IDs from the NMDC API.

        This method returns a list of linked instance records for the given IDs. For instance,
        if you provide a study ID, this returns records from the ``biosample_set``,
        ``data_generation_set``, etc. that are associated with that study, even if the association
        is not represented by a single direct link.

        See ``get_linked_instances_and_associate_ids`` for a method that returns an alternate format of the data.

        Parameters
        ----------
        ids : list[str] | str
            The ids to search for.
        hydrate : bool = False
            Whether to include full documents in the response. The default is False.
        types : list[str] | str = None
            The types of records you want to return. Default is None, which returns all types.
            Example: ["nmdc:Study", "nmdc:Biosample", "nmdc:MassSpectrometry"].
        max_page_size : int = 500
            The maximum number of records to return per page. Default is 500.

        Returns
        -------
        list[dict]
            A list of linked instance records.
        """
        # highest number I could get to without a timeout
        batch_size = 250
        # Note: We normalize the `ids` value into a list, since the docstring says the caller can
        #       pass it in as either a bare string _or_ a list of strings. If we didn't do this,
        #       and the caller did pass in a bare string, the code below would iterate over the
        #       individual characters of that string (strings are iterable in Python).
        list_of_ids = NMDCSearch._normalize_ids(ids)
        batch_records: list[dict[str, Any]] = []
        url = f"{self.api_base_url}/nmdcschema/linked_instances"
        # split the ids into batches
        for i in range(0, len(list_of_ids), batch_size):
            batch = list_of_ids[i : i + batch_size]
            params = {
                "types": types,
                "ids": batch,
                "hydrate": hydrate,
                "max_page_size": max_page_size,
            }
            response = requests.get(
                url=url,
                params=params,
                headers=self._build_http_request_headers(),
            )
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
                        response = requests.get(
                            url=url,
                            params=params,
                            headers=self._build_http_request_headers(),
                        )
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
        types: list[str] | str | None = None,
        hydrate: bool = False,
        max_page_size: int = 500,
    ) -> dict[str, list[dict] | list[str]]:
        """
        Retrieve linked instances for the given IDs from the NMDC API and associate them with the input IDs.

        This method returns a list of records that are linked to the records with the given IDs. For instance,
        if you provide an ID for a study record, this can return the ids records within the ``biosample_set``,
        ``data_generation_set`` etc that are associated with this study, even if it is not a single link between records.

        See also ``get_linked_instances`` for a method that returns the linked instances in their original list format.
        This method reformats into a dictionary with keys as query ids, and either a list of resulting linked ids or a list of hydrated records as values.


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
        dict[str, list[dict] | list[str]]
            A dictionary mapping each input id to a list of its linked instance records.
        """
        # get the linked instances
        linked_instances = self.get_linked_instances(
            types=types, ids=ids, hydrate=hydrate, max_page_size=max_page_size
        )
        association: dict[str, list[dict] | list[str]] = {}
        # loop through the linked instances and build the association
        for record in linked_instances:
            for stream in ["_upstream_of", "_downstream_of"]:
                if stream in record:
                    for stream_id in record[stream]:
                        if stream_id not in association:
                            association[stream_id] = []
                        if hydrate:
                            association[stream_id].append(
                                {key: record[key] for key in record if key != stream}
                            )
                        else:
                            association[stream_id].append(record["id"])
                else:
                    continue

        return association

    def get_collection_name_from_id(self, doc_id: str) -> str:
        """
        Used when you have an id but not the collection name.
        Determine the collection the id is stored in.

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
        url = f"{self.api_base_url}/nmdcschema/ids/{doc_id}/collection-name"
        try:
            response = requests.get(url, headers=self._build_http_request_headers())
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error("API request failed", exc_info=True)
            raise RuntimeError("Failed to get record name from NMDC API") from e
        else:
            logging.debug(
                f"API request response: {response.json()}\n API Status Code: {response.status_code}"
            )

        collection_name = response.json()["collection_name"]
        return collection_name

    def get_records_by_id(
        self,
        ids: list[str] | str,
        fields: str = "",
    ) -> list[dict]:
        """
        Retrieve records via the NMDC API from a provided list of record IDs.

        The input ids can be from multiple collections. Input like
        ["nmdc:sty-11-8fb6t785", "nmdc:bsm-11-002vgm56", "nmdc:dobj-11-00095294"] is valid and will return each of these records in a list of dictionaries.

        Parameters
        ----------
        ids : list[str] | str
            List of IDs of records to retrieve.
        fields : str
            Comma-separated list of fields to include in the response.

        Returns
        -------
        list[dict]
            The record(s) data.
        """

        resources: list[dict[str, Any]] = []
        # sort the input ids
        sorted_ids = sorted(ids) if isinstance(ids, list) else [ids]
        id_dict: dict[str, list[str]] = {}
        # group ids by their collection subset nmdc:sty, nmdc:bsm, etc
        for id in sorted_ids:
            cur_group = id.split("-")[0]
            if cur_group not in id_dict:
                id_dict[cur_group] = []
            id_dict[cur_group].append(id)

        for cur_group in id_dict:
            # process each group of ids
            id_list = id_dict[cur_group]
            # for each group, get the collection name from one of the ids
            collection_name = self.get_collection_name_from_id(id_list[0])
            # import in function to circumvent circular import error
            from nmdc_api_utilities.collection_search import CollectionSearch

            cs = CollectionSearch(
                collection_name=collection_name, api_base_url=self.api_base_url
            )
            records = cs.get_batch_records(
                id_list=id_list,
                search_field="id",
                fields=fields,
            )
            resources.extend(records)
        return resources

    def get_schema_version(self) -> str:
        """
        Get the current NMDC schema version used by the NMDC API.

        Returns
        -------
        str
            The NMDC schema version
        """

        url = f"{self.api_base_url}/version"
        try:
            response = requests.get(url, headers=self._build_http_request_headers())
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error("API request failed", exc_info=True)
            raise RuntimeError("Failed to version from NMDC API") from e
        return response.json()["nmdc-schema"]

    def get_record_from_id(self, id: str, filter: str = "", fields: str = "") -> dict:
        """
        Retrieve a record via the NMDC API from a provided record ID.

        Parameters
        ----------
        id : str
            The ID of the record to retrieve.
        filter : str
            Additional filter to apply to the records.
        fields : str
            Comma-separated list of fields to include in the response.

        Returns
        -------
        dict
            The full record data.
        """
        collection_name = self.get_collection_name_from_id(id)
        url = f"{self.api_base_url}/nmdcschema/{collection_name}/{id}"
        params = {
            "filter": filter,
            "projection": fields,
        }
        try:
            response = requests.get(
                url,
                params=params,
                headers=self._build_http_request_headers(),
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error("API request failed", exc_info=True)
            raise RuntimeError(f"Failed to get record {id} from NMDC API") from e
        return response.json()
