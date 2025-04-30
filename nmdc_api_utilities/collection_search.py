# -*- coding: utf-8 -*-
import requests
from nmdc_api_utilities.data_processing import DataProcessing
import urllib.parse
from nmdc_api_utilities.nmdc_search import NMDCSearch
import logging
import re

logger = logging.getLogger(__name__)
import json


class CollectionSearch(NMDCSearch):
    """
    Class to interact with the NMDC API to get collections of data. Must know the collection name to query.
    """

    def __init__(self, collection_name, env="prod"):
        self.collection_name = collection_name
        super().__init__(env=env)

    def get_records(
        self,
        filter: str = "",
        max_page_size: int = 100,
        fields: str = "",
        all_pages: bool = False,
    ) -> list[dict]:
        """
        Get a collection of data from the NMDC API. Generic function to get a collection of data from the NMDC API. Can provide a specific filter if desired.
        Parameters
        ----------
        filter: str
            The filter to apply to the query. Default is an empty string.
        max_page_size: int
            The maximum number of items to return per page. Default is 100.
        fields: str
            The fields to return. Default is all fields.
        all_pages: bool
            True to return all pages. False to return the first page. Default is False.
        Returns
        -------
        list[dict]
            A list of dictionaries containing the records.
        Raises
        ------
        RuntimeError
            If the API request fails.
        """
        logging.debug(f"get_records Filter: {filter}")
        filter = urllib.parse.quote(filter)
        logging.debug(f"get_records encoded Filter: {filter}")
        url = f"{self.base_url}/nmdcschema/{self.collection_name}?filter={filter}&max_page_size={max_page_size}&projection={fields}"
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

        results = response.json()["resources"]
        # otherwise, get all pages
        if all_pages:
            results = self._get_all_pages(response, filter, max_page_size, fields)[
                "resources"
            ]

        return results

    def _get_all_pages(
        self,
        response: requests.models.Response,
        filter: str = "",
        max_page_size: int = 100,
        fields: str = "",
    ):
        """
        Get all pages of data from the NMDC API. This is a helper function to get all pages of data from the NMDC API.
        Parameters
        ----------
        response: requests.models.Response
            The response object from the API request.
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
            url = f"{self.base_url}/nmdcschema/{self.collection_name}?filter={filter}&max_page_size={max_page_size}&projection={fields}&page_token={next_page_token}"
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

    def get_record_by_filter(
        self, filter: str, max_page_size=25, fields: str = "", all_pages=False
    ) -> list[dict]:
        """
        Get a record from the NMDC API by its id.
        Parameters
        ----------
        filter: str
            The filter to use to query the collection. Must be in MonogDB query format.
                Resources found here - https://www.mongodb.com/docs/manual/reference/method/db.collection.find/#std-label-method-find-query
            Example: {"name":{"my record name"}}
        max_page_size: int
            The number of results to return per page. Default is 25.
        fields: str
            The fields to return. Default is all fields.
            Example: "id,name,description,alternative_identifiers,file_size_bytes,md5_checksum,data_object_type,url,type"
        all_pages: bool
            True to return all pages. False to return the first page. Default is False.
        Returns
        -------
        list[dict]
            A list of dictionaries containing the records.
        Raises
        ------
        """
        results = self.get_records(filter, max_page_size, fields, all_pages)
        return results

    def get_record_by_attribute(
        self,
        attribute_name: str,
        attribute_value: str,
        max_page_size: int = 25,
        fields: str = "",
        all_pages: bool = False,
        exact_match: bool = False,
    ):
        """
        Get a record from the NMDC API by its name. Records can be filtered based on their attributes found https://microbiomedata.github.io/nmdc-schema/.
        Parameters
        ----------
        attribute_name: str
            The name of the attribute to filter by.
        attribute_value: str
            The value of the attribute to filter by.
        max_page_size: int
            The number of results to return per page. Default is 25.
        fields: str
            The fields to return. Default is all fields.
        all_pages: bool
            True to return all pages. False to return the first page. Default is False.
        exact_match: bool
            This var is used to determine if the inputted attribute value is an exact match or a partial match. Default is False, meaning the user does not need to input an exact match.
            Under the hood this is used to determine if the inputted attribute value should be wrapped in a regex expression.
        Returns
        -------
        list[dict]
            A list of dictionaries containing the records.
        """

        if exact_match:
            filter = f'{{"{attribute_name}":"{attribute_value}"}}'
        else:
            # escape special characters - mongo db filters require special characters to be double escaped ex. GC\\-MS \\(2009\\)
            escaped_value = re.sub(r"([\W])", r"\\\\\1", attribute_value)
            filter = (
                f'{{"{attribute_name}":{{"$regex":"{escaped_value}","$options":"i"}}}}'
            )
        logging.debug(f"get_record_by_attribute Filter: {filter}")
        results = self.get_records(filter, max_page_size, fields, all_pages)
        return results

    def get_record_by_id(
        self,
        collection_id: str,
        max_page_size: int = 100,
        fields: str = "",
    ) -> list[dict]:
        """
        Get a collection of data from the NMDC API by id.
        Parameters
        ----------
        collection_id: str
            The id of the collection.
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
        url = f"{self.base_url}/nmdcschema/{self.collection_name}/{collection_id}?max_page_size={max_page_size}&projection={fields}"
        # get the reponse
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error("API request failed", exc_info=True)
            raise RuntimeError("Failed to get collection by id from NMDC API") from e
        else:
            logging.debug(
                f"API request response: {response.json()}\n API Status Code: {response.status_code}"
            )
        results = response.json()
        return results

    def check_ids_exist(
        self, ids: list, chunk_size: int = 100, return_missing_ids: bool = False
    ) -> bool:
        """
        Check if the IDs exist in the collection.

        This method constructs a query to the API to filter the collection based on the given IDs, and checks if all IDs exist in the collection.

        Parameters
        ----------
        ids : list
            A list of IDs to check if they exist in the collection.
        chunk_size : int
            The number of IDs to check in each query. Default is 100.
        return_missing_ids : bool
            If True, and if ids are missing in the collection, return the list of IDs that do not exist in the collection. Default is False.
        Returns
        -------
        bool
            True if all IDs exist in the collection, False otherwise.
        """
        # chunk the input list of IDs into smaller lists of 100 IDs each
        # to avoid the maximum URL length limit
        ids_test = list(set(ids))
        for i in range(0, len(ids_test), chunk_size):
            chunk = ids_test[i : i + chunk_size]
            filter_dict = {"id": {"$in": chunk}}
            filter_json_string = json.dumps(filter_dict, separators=(",", ":"))

            results = self.get_records(
                filter=filter_json_string, max_page_size=len(chunk), fields="id"
            )
            if len(results) != len(chunk) and return_missing_ids:
                missing_ids = list(
                    set(chunk) - set([record["id"] for record in results])
                )
                return False, missing_ids
            elif len(results) != len(chunk) and not return_missing_ids:
                return False
        return True

    def get_batch_records(
        self, id_list: list, search_field: str, chunk_size=100, fields=""
    ) -> list[dict]:
        """
        Get a batch of records from the collection by a list of input IDs. This method is used to identify records that include any of the IDs from the input list, matching the search_field.
        This is using the MongoDB filter keyword $in to identify other records that include the input IDs.
        Parameters
        ---------
        id_list: list
            A list of IDs to get records for.
        search_field: str
            The field to search for. This must match a field from the NMDC Schema.
        chunk_size: int
            The number of IDs to get in each query. Default is 100.
        fields: str
            The fields to return. Default is all fields.
        Returns
        -------
        list[dict]
            A list of dictionaries containing the records.
        """
        dp = DataProcessing()
        results = []
        id_list = list(set(id_list))
        chunks = dp.split_list(input_list=id_list, chunk_size=chunk_size)
        for chunk in chunks:
            chunk = dp._string_mongo_list(data=chunk)
            filter = f'{{"{search_field}": {{"$in": {chunk}}}}}'
            res = self.get_records(
                filter=filter, max_page_size=len(chunk), fields=fields, all_pages=True
            )
            results += res
        return results


if __name__ == "__main__":
    pass
