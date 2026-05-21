# -*- coding: utf-8 -*-

import json
import logging
import re
from typing import Literal, Optional, cast

import pandas as pd
import requests

from nmdc_api_utilities.config import API_BASE_URL
from nmdc_api_utilities.data_processing import DataProcessing
from nmdc_api_utilities.decorators import has_deprecated_parameter
from nmdc_api_utilities.nmdc_search import NMDCSearch

logger = logging.getLogger(__name__)

QueryParamValue = str | bytes | int | float | None


class OperationNotSupportedError(RuntimeError):
    """Raised when an operation isn't supported by a collection subclass."""

    pass


@has_deprecated_parameter("env", reason="Use ``api_base_url`` instead.")
class CollectionSearch(NMDCSearch):
    """
    Class to interact with the NMDC API to search for records within a specified collection.

    Parameters
    ----------
    collection_name
        The name of the collection to search within.
    api_base_url
        The base URL of an instance of the NMDC Runtime API. By default, this is the base URL of the production instance.
    """

    def __init__(
        self,
        collection_name: str,
        api_base_url: str = API_BASE_URL,
        env: str = "",
    ):
        self.collection_name = collection_name
        super().__init__(
            api_base_url=api_base_url,
            env=env,
        )

    def get_records(
        self,
        filter: str = "",
        max_page_size: int = 100,
        fields: str = "",
        all_pages: bool = True,
        shape: Literal["records", "dataframe"] = "records",
    ) -> list[dict] | pd.DataFrame:
        """
        Retrieve records from the collection via the NMDC API.

        Parameters
        ----------
        filter
            The filter to apply to the query. An empty string will return all records.
        max_page_size
            The maximum number of records to return per page.
        fields
            The fields to return. An empty string will return all fields.
        all_pages
            True to return all pages. False to return only the first page.
        shape
            The shape of the returned data. If "records", the data will be returned as a list of dictionaries,
            where each dictionary is a record. If "dataframe", the data will be returned as a pandas dataframe.

        Returns
        -------
        list[dict] | pd.DataFrame
            A list of dictionaries or a pandas dataframe containing the records.

        Raises
        ------
        RuntimeError
            If the API request fails.

        """
        if shape not in ["records", "dataframe"]:
            raise ValueError(
                f"Invalid shape input: {shape}\n Valid inputs: 'records' or 'dataframe'"
            )
        url = f"{self.api_base_url}/nmdcschema/{self.collection_name}"
        params: dict[str, QueryParamValue] = {
            "filter": filter,
            "max_page_size": max_page_size,
            "projection": fields,
        }
        try:
            response = requests.get(
                url=url,
                params=params,
                headers=self._build_http_request_headers(),
            )
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
            results = self._get_all_pages(response, url, filter, max_page_size, fields)[
                "resources"
            ]

        if shape == "dataframe":
            results = pd.DataFrame(results)
        return results

    def get_record_by_filter(
        self,
        filter: str,
        max_page_size: int = 25,
        fields: str = "",
        all_pages: bool = True,
        shape: Literal["records", "dataframe"] = "records",
    ) -> list[dict] | pd.DataFrame:
        """
        Retrieve a record via the NMDC API using a specified filter.

        Parameters
        ----------
        filter
            The filter to use to query the collection. Must be in MongoDB query format.
            Example: {"name":"my record name"}.
            `More resources for constructing MongoDB filters can be found here <https://www.mongodb.com/docs/manual/reference/method/db.collection.find/#std-label-method-find-query>`_.
        max_page_size
            The number of records to return per page.
        fields
            The fields to return. Default will return all fields.
            Example: "id,name,description,url,type"
        all_pages
            True to return all pages. False to return only the first page.
        shape
            The shape of the returned data. If "records", the data will be returned as a list of dictionaries,
            where each dictionary is a record. If "dataframe", the data will be returned as a pandas dataframe.

        Returns
        -------
        list[dict] | pd.DataFrame
            A list of dictionaries or a pandas dataframe containing the records.

        """
        results = self.get_records(filter, max_page_size, fields, all_pages, shape)
        return results

    def get_record_by_attribute(
        self,
        attribute_name: str,
        attribute_value: str,
        max_page_size: int = 25,
        fields: str = "",
        all_pages: bool = True,
        exact_match: bool = False,
        shape: Literal["records", "dataframe"] = "records",
    ) -> list[dict] | pd.DataFrame:
        """
        Retrieve a record via the NMDC API by a specific attribute's value.

        Parameters
        ----------
        attribute_name
            The name of the attribute to filter by.
        attribute_value
            The value of the attribute to filter by.
        max_page_size
            The number of records to return per page.
        fields
            The fields to return. If empty, all fields are returned.
        all_pages
            True to return all pages. False to return only the first page.
        exact_match
            Whether the attribute value should be matched exactly or partially.
            Used to determine if the inputted attribute value is an exact match or a partial match.
            Default is False, meaning the user does not need to input an exact match.
        shape
            The shape of the returned data. If "records", the data will be returned as a list of dictionaries,
            where each dictionary is a record. If "dataframe", the data will be returned as a pandas dataframe.

        Returns
        -------
        list[dict] | pd.DataFrame
            A list of dictionaries or a pandas dataframe containing the records.

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
        results = self.get_records(
            filter, max_page_size, fields, all_pages, shape=shape
        )
        return results

    @has_deprecated_parameter("collection_id", reason="Use ``record_id`` instead.")
    def get_record_by_id(
        self,
        record_id: Optional[str] = None,
        max_page_size: int = 100,
        fields: str = "",
        collection_id: Optional[str] = None,
        shape: Literal["records", "dataframe"] = "records",
    ) -> list[dict] | pd.DataFrame:
        """
        Retrieve a record from the collection via the NMDC API using a specified ID.

        Parameters
        ----------
        record_id:
            The id of the record to retrieve from the collection. Not required to enable backwards compatibility with the deprecated collection_id parameter.
        max_page_size:
            The maximum number of records to return per page. Default is 100.
        fields:
            The fields to return. Default is all fields.
        collection_id:
            The id of the record to retrieve from the collection. This parameter is deprecated and will be removed in a future version. Please use record_id instead.
        shape
            The shape of the returned data. If "records", the data will be returned as a list of dictionaries,
            where each dictionary is a record. If "dataframe", the data will be returned as a pandas dataframe.

        Returns
        -------
        list[dict] | pd.DataFrame
            A list of dictionaries or a pandas dataframe containing the records.

        Raises
        ------
        RuntimeError
            If the API request fails.

        """
        if not getattr(self, "supports_get_by_id", True):
            raise OperationNotSupportedError(
                f"get_record_by_id is not supported for the {self.collection_name} collection"
            )

        if record_id is None and collection_id is None:
            raise ValueError(
                "No record_id provided. Please provide this parameter to retrieve a record."
            )
        if record_id and collection_id:
            raise ValueError(
                "Both record_id and collection_id were provided. Please provide record_id, as collection_id is deprecated and will be removed in a future version."
            )
        if collection_id:
            record_id = collection_id

        url = f"{self.api_base_url}/nmdcschema/{self.collection_name}/{record_id}"
        params: dict[str, QueryParamValue] = {
            "max_page_size": max_page_size,
            "projection": fields,
        }
        # get the reponse
        try:
            response = requests.get(
                url=url,
                headers=self._build_http_request_headers(),
                params=params,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error("API request failed", exc_info=True)
            raise RuntimeError("Failed to get collection by id from NMDC API") from e
        else:
            logging.debug(
                f"API request response: {response.json()}\n API Status Code: {response.status_code}"
            )
        results = response.json()
        if shape == "dataframe":
            if isinstance(results, dict):
                results = pd.DataFrame([results])
            else:
                results = pd.DataFrame(results)
        return results

    def check_ids_exist(
        self,
        ids: list[str],
        chunk_size: int = 100,
        return_missing_ids: bool = False,
    ) -> bool | tuple[bool, list[str]]:
        """
        Check if specified IDs exist in the collection.

        This method constructs a query to the API to filter the collection based on the given IDs, and checks if all IDs exist in the collection.

        Parameters
        ----------
        ids
            A list of IDs to check if they exist in the collection.
        chunk_size
            The number of IDs to check in each query.
        return_missing_ids
            If True, and if ids are missing in the collection, return the list of IDs that do not exist in the collection.

        Returns
        -------
        bool | tuple[bool, list[str]]
            True if all IDs exist in the collection, False otherwise. However,
            if return_missing_ids is True, returns a tuple whose first item is the aforementioned boolean value,
            and whose second item is a list of the IDs, if any, that don't exist in the collection.
        """
        if not getattr(self, "supports_get_by_id", True):
            raise OperationNotSupportedError(
                f"check_ids_exist is not supported for the {self.collection_name} collection"
            )

        # chunk the input list of IDs into smaller lists of 100 IDs each
        # to avoid the maximum URL length limit
        ids_test = list(set(ids))
        for i in range(0, len(ids_test), chunk_size):
            chunk = ids_test[i : i + chunk_size]
            filter_dict = {"id": {"$in": chunk}}
            filter_json_string = json.dumps(filter_dict, separators=(",", ":"))

            results = self.get_records(
                filter=filter_json_string,
                max_page_size=len(chunk),
                fields="id",
                shape="records",
            )
            results = cast(list[dict], results)
            if len(results) != len(chunk) and return_missing_ids:
                missing_ids = list(
                    set(chunk) - set([record["id"] for record in results])
                )
                return False, missing_ids
            elif len(results) != len(chunk) and not return_missing_ids:
                return False
        return True

    def get_batch_records(
        self,
        id_list: list,
        search_field: str,
        chunk_size: int = 100,
        fields: str = "",
        shape: Literal["records", "dataframe"] = "records",
    ) -> list[dict] | pd.DataFrame:
        """
        Get a batch of records from the collection that relate to input IDs.

        This method is used to retrieve records that include any of the IDs from the input list in specified fields (including fields other than ``id``).
        For example, if records in a collection contain study IDs in a field called ``associated_studies``,
        this method can be used to retrieve all records that include any of the input study IDs in the ``associated_studies`` field.

        Parameters
        ---------
        id_list
            A list of IDs to get records for.
        search_field
            The field in which to search for the IDs.
        chunk_size
            The number of IDs to get in each query.
        fields
            The fields to return. If empty or not provided, all fields are returned.
        shape
            The shape of the returned data. If "records", the data will be returned as a list of dictionaries,
            where each dictionary is a record. If "dataframe", the data will be returned as a pandas dataframe.

        Returns
        -------
        list[dict] | pd.DataFrame
            A list of dictionaries or a pandas dataframe (still packed) containing the records that relate to the input IDs in
            the specified search field.
        """
        if not getattr(self, "supports_get_by_id", True):
            raise OperationNotSupportedError(
                f"get_record_by_id is not supported for the {self.collection_name} collection"
            )

        dp = DataProcessing()
        results: list[dict] = []
        id_list = list(set(id_list))
        chunks = dp.split_list(input_list=id_list, chunk_size=chunk_size)
        for chunk in chunks:
            sanitized_chunk = json.dumps(chunk)
            filter = f'{{"{search_field}": {{"$in": {sanitized_chunk}}}}}'
            res = self.get_records(
                filter=filter, max_page_size=len(chunk), fields=fields, all_pages=True
            )
            res = cast(list[dict], res)
            results += res
        if shape == "dataframe":
            return pd.DataFrame(results)
        return results


if __name__ == "__main__":
    pass
