# -*- coding: utf-8 -*-
import requests
from nmdc_api_utilities.data_processing import DataProcessing
import urllib.parse
from nmdc_api_utilities.nmdc_search import NMDCSearch
import logging
import re
logger = logging.getLogger(__name__)


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
    ):
        """
        Get a collection of data from the NMDC API. Generic function to get a collection of data from the NMDC API. Can provide a specific filter if desired.
        params:
            filter: str
                The filter to apply to the query. Default is an empty string.
            max_page_size: int
                The maximum number of items to return per page. Default is 100.
            fields: str
                The fields to return. Default is all fields.
        """
        logging.debug(f"get_records Filter: {filter}")
        filter = urllib.parse.quote_plus(filter)
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
        self, filter: str, max_page_size=25, fields="", all_pages=False
    ):
        """
        Get a record from the NMDC API by its id.
        params:
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
        """
        results = self.get_records(filter, max_page_size, fields, all_pages)
        return results

    def get_record_by_attribute(
        self,
        attribute_name,
        attribute_value,
        max_page_size=25,
        fields="",
        all_pages=False,
        exact_match=False,
    ):
        """
        Get a record from the NMDC API by its name. Records can be filtered based on their attributes found https://microbiomedata.github.io/nmdc-schema/.
        params:
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
        """

        if exact_match:
            filter = f'{{"{attribute_name}":"{attribute_value}"}}'
        else:
            # escape special characters - mongo db filters require special characters to be double escaped ex. GC\\-MS \\(2009\\)
            escaped_value = re.sub(r'([\W])', r'\\\\\1', attribute_value)
            filter = f'{{"{attribute_name}":{{"$regex":"{escaped_value}","$options":"i"}}}}'
        logging.debug(f"get_record_by_attribute Filter: {filter}")
        results = self.get_records(filter, max_page_size, fields, all_pages)
        return results

    def get_record_by_id(
        self,
        collection_id: str,
        max_page_size: int = 100,
        fields: str = "",
    ):
        """
        Get a collection of data from the NMDC API by id.
        params:
            collection_id: str
                The id of the collection.
            max_page_size: int
                The maximum number of items to return per page. Default is 100.
            fields: str
                The fields to return. Default is all fields.
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
    
    def check_ids_exist(self, ids: list) -> bool:
        """
        Check if the IDs exist in the collection.

        This method constructs a query to the API to filter the collection based on the given IDs, and checks if all IDs exist in the collection.

        Parameters
        ----------
        ids : list
            A list of IDs to check if they exist in the collection.

        Returns
        -------
        bool
            True if all IDs exist in the collection, False otherwise.

        Raises
        ------
        requests.RequestException
            If there's an error in making the API request.
        """
        dp = DataProcessing()
        import json
        ids_test = list(set(ids))
        # ready_list = dp._string_mongo_list(ids_test)
        # filter = f'{{"id":{{"$in":{ready_list}}}}}'
        filter_dict = {
            "id": {"$in": ids_test}
        }
        filter_json_string = json.dumps(filter_dict, separators=(',', ':'))

        results = self.get_records(filter=filter_json_string, max_page_size=len(ids_test), fields="id")
        if len(results) != len(ids_test):
            raise ValueError(f"IDs not found in collection: {set(ids_test) - set([r['id'] for r in results])}")
        return True


if __name__ == "__main__":
    pass
