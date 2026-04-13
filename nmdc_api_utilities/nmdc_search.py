# -*- coding: utf-8 -*-
import logging
import warnings
from typing import Optional

import requests

from nmdc_api_utilities import __version__ as package_version
from nmdc_api_utilities.config import API_BASE_URL, get_api_base_url

logger = logging.getLogger(__name__)


class NMDCSearch:
    """
    Class for interacting with the NMDC runtime API for searching and retrieving records in the NMDC metadata database.

    Parameters
    ----------
    api_base_url: str
        The base URL of an instance of the NMDC Runtime API. By default, this is the base URL of
        the production instance. NMDC team members will occasionally set this to the base URL of
        a different instance; for example, a self-hosted instance used for testing.

    """

    def __init__(self, api_base_url: str = API_BASE_URL, env: str = ""):
        if env != "":
            warnings.warn(
                "`env` is deprecated and will be removed in a future release. "
                "Use `api_base_url` instead.",
                DeprecationWarning,
            )
        self.api_base_url = get_api_base_url(api_base_url=api_base_url, env=env)

    def _build_http_request_headers(
        self,
        access_token: Optional[str] = None,
        accept: Optional[str] = None,
        content_type: Optional[str] = None,
        additional_headers: Optional[dict[str, str]] = None,
    ) -> dict[str, str]:
        """
        Builds HTTP headers that can be included with HTTP requests sent by instances of this class
        and its subclasses.

        >>> searcher = NMDCSearch()
        >>> headers = searcher._build_http_request_headers(
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
    ) -> dict:
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
            The maximum number of records to return per page. Default is 100.
        fields: str
            The fields to return. Default is all fields.
        access_token: Optional[str]
            Optional access token to include in the API request.

        Returns
        -------
        dict
            A dictionary containing the records in a "resources" key.

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

    def get_linked_instances(
        self,
        ids: list[str] | str,
        hydrate: bool = False,
        types: list[str] | str = None,
        max_page_size: int = 500,
    ) -> list[dict]:
        """
        Retrieve linked instances for the given IDs from the NMDC API.

        This method returns a list of linked instance records for the given IDs, for instance,
        if you provide a study id, this will return the ids records within the ``biosample_set``,
        ``data_generation_set`` etc that are associated with this study, even if it is not a single link.

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
        batch_records = []
        url = f"{self.api_base_url}/nmdcschema/linked_instances"
        # split the ids into batches
        for i in range(0, len(ids), batch_size):
            batch = ids[i : i + batch_size]
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
        types: list[str] | str = None,
        hydrate: bool = False,
        max_page_size: int = 500,
    ) -> dict[str, list[str]]:
        """
        Retrieve linked instances for the given IDs from the NMDC API and associate them with the input IDs.

        This method returns a list of linked instance records for the given IDs, for instance,
        if you provide a study id, this will return the ids records within the ``biosample_set``,
        ``data_generation_set`` etc that are associated with this study, even if it is not a single link between records.

        See also ``get_linked_instances`` for a method that returns the linked instances in their original list format.
        This method reformats into a dictionary with keys as query ids, and a list of resulting linked ids as values.


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

        resources = []
        # sort the input ids
        sorted_ids = sorted(ids) if isinstance(ids, list) else [ids]
        id_dict = {}
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
