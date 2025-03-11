# -*- coding: utf-8 -*-
from nmdc_api_utilities.collection_search import CollectionSearch
import logging

logger = logging.getLogger(__name__)


class LatLongFilters(CollectionSearch):
    """
    Class to interact with the NMDC API to filter sets by latitude and longitude.
    """

    def __init__(self, collection_name, env="Production"):
        self.collection_name = collection_name
        super().__init__(collection_name=self.collection_name, env=env)

    def get_record_by_latitude(
        self, comparison: str, latitude: float, page_size=25, fields="", all_pages=False
    ):
        """
        Get a record from the NMDC API by latitude comparison.
        params:
            comparison: str
                The comparison to use to query the record. MUST BE ONE OF THE FOLLOWING:
                    eq    - Matches values that are equal to the given value.
                    gt    - Matches if values are greater than the given value.
                    lt    - Matches if values are less than the given value.
                    gte    - Matches if values are greater or equal to the given value.
                    lte - Matches if values are less or equal to the given value.
            latitude: float
                The latitude of the record to query.
            page_size: int
                The number of results to return per page. Default is 25.
            fields: str
                The fields to return. Default is all fields.
                Example: "id,name,description,alternative_identifiers,file_size_bytes,md5_checksum,data_object_type,url,type"
            all_pages: bool
                True to return all pages. False to return the first page. Default is False.
        """
        allowed_comparisons = ["eq", "gt", "lt", "gte", "lte"]
        if comparison not in allowed_comparisons:
            logger.error(
                f"Invalid comparison input: {comparison}\n Valid inputs: {allowed_comparisons}"
            )
            raise ValueError(
                f"Invalid comparison input: {comparison}\n Valid inputs: {allowed_comparisons}"
            )
        filter = f'{{"lat_lon.latitude": {{"${comparison}": {latitude}}}}}'

        result = self.get_records(filter, page_size, fields, all_pages)
        return result

    def get_record_by_longitude(
        self,
        comparison: str,
        longitude: float,
        page_size=25,
        fields="",
        all_pages=False,
    ):
        """
        Get a record from the NMDC API by longitude comparison.
        params:
            comparison: str
                The comparison to use to query the record. MUST BE ONE OF THE FOLLOWING:
                    eq    - Matches values that are equal to the given value.
                    gt    - Matches if values are greater than the given value.
                    lt    - Matches if values are less than the given value.
                    gte    - Matches if values are greater or equal to the given value.
                    lte - Matches if values are less or equal to the given value.
            longitude: float
                The longitude of the record to query.
            page_size: int
                The number of results to return per page. Default is 25.
            fields: str
                The fields to return. Default is all fields.
                Example: "id,name,description,alternative_identifiers,file_size_bytes,md5_checksum,data_object_type,url,type"
            all_pages: bool
                True to return all pages. False to return the first page. Default is False.
        """
        allowed_comparisons = ["eq", "gt", "lt", "gte", "lte"]
        if comparison not in allowed_comparisons:
            logger.error(
                f"Invalid comparison input: {comparison}\n Valid inputs: {allowed_comparisons}"
            )
            raise ValueError(
                f"Invalid comparison input: {comparison}\n Valid inputs: {allowed_comparisons}"
            )
        filter = f'{{"lat_lon.longitude": {{"${comparison}": {longitude}}}}}'
        result = self.get_records(filter, page_size, fields, all_pages)
        return result

    def get_record_by_lat_long(
        self,
        lat_comparison: str,
        long_comparison: str,
        latitude: float,
        longitude: float,
        page_size=25,
        fields="",
        all_pages=False,
    ):
        """
        Get a record from the NMDC API by latitude and longitude comparison.
        params:
            lat_comparison: str
                The comparison to use to query the record for latitude. MUST BE ONE OF THE FOLLOWING:
                    eq    - Matches values that are equal to the given value.
                    gt    - Matches if values are greater than the given value.
                    lt    - Matches if values are less than the given value.
                    gte    - Matches if values are greater or equal to the given value.
                    lte - Matches if values are less or equal to the given value.
            long_comparison: str
                The comparison to use to query the record for longitude. MUST BE ONE OF THE FOLLOWING:
                    eq    - Matches values that are equal to the given value.
                    gt    - Matches if values are greater than the given value.
                    lt    - Matches if values are less than the given value.
                    gte    - Matches if values are greater or equal to the given value.
                    lte - Matches if values are less or equal to the given value.
            latitude: float
                The latitude of the record to query.
            longitude: float
                The longitude of the record to query.
            page_size: int
                The number of results to return per page. Default is 25.
            fields: str
                The fields to return. Default is all fields.
                Example: "id,name,description,alternative_identifiers,file_size_bytes,md5_checksum,data_object_type,url,type"
            all_pages: bool
                True to return all pages. False to return the first page. Default is False.
        """
        allowed_comparisons = ["eq", "gt", "lt", "gte", "lte"]
        if lat_comparison not in allowed_comparisons:
            logger.error(
                f"Invalid comparison input: {lat_comparison}\n Valid inputs: {allowed_comparisons}"
            )
            raise ValueError(
                f"Invalid comparison input: {lat_comparison}\n Valid inputs: {allowed_comparisons}"
            )
        if long_comparison not in allowed_comparisons:
            logger.error(
                f"Invalid comparison input: {long_comparison}\n Valid inputs: {allowed_comparisons}"
            )
            raise ValueError(
                f"Invalid comparison input: {long_comparison}\n Valid inputs: {allowed_comparisons}"
            )
        filter = f'{{"lat_lon.latitude": {{"${lat_comparison}": {latitude}}}, "lat_lon.longitude": {{"${long_comparison}": {longitude}}}}}'
        results = self.get_records(filter, page_size, fields, all_pages)
        return results
