# -*- coding: utf-8 -*-
import logging
from abc import ABC, abstractmethod
from typing import Literal, cast

import pandas as pd

logger = logging.getLogger(__name__)


class LatLongFilters(ABC):
    """
    Mixin class with methods to interact with collections that
    can be searched by latitude and longitude via the NMDC API.
    """

    @abstractmethod
    def get_records(
        self,
        filter: str = "",
        max_page_size: int = 100,
        fields: str = "",
        all_pages: bool = False,
        shape: Literal["records", "dataframe"] = "records",
    ) -> list[dict] | pd.DataFrame:
        """Retrieve records from a collection via the NMDC API."""

    def get_record_by_latitude(
        self,
        comparison: str,
        latitude: float,
        page_size: int = 25,
        fields: str = "",
        all_pages: bool = False,
    ) -> list[dict]:
        """
        Retrieve records by latitude filter via the NMDC API.

        Parameters
        ----------
        comparison
            The comparison to use to query the record. See Notes for more details.
        latitude
            The latitude of the record to query.
        page_size
            The number of results to return per page.
        fields
            The fields to return. Default is all fields.
            Example: "id,name,description,type"
        all_pages
            True to return all pages. False to return the first page.

        Returns
        -------
        list[dict]
            A list of records.

        Raises
        ------
        ValueError
            If the comparison is not one of the allowed comparisons.

        Notes
        -----
        The ``comparison`` must be one of the following: "eq", "gt", "lt", "gte", "lte".

        - eq : Matches values that are equal to the given value.
        - gt : Matches if values are greater than the given value.
        - lt : Matches if values are less than the given value.
        - gte : Matches if values are greater or equal to the given value.
        - lte : Matches if values are less or equal to the given value.

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

        result = self.get_records(filter, page_size, fields, all_pages, shape="records")
        return cast(list[dict], result)

    def get_record_by_longitude(
        self,
        comparison: str,
        longitude: float,
        page_size: int = 25,
        fields: str = "",
        all_pages: bool = False,
    ) -> list[dict]:
        """
        Retrieve records by longitude filter via the NMDC API.

        Parameters
        ----------
        comparison
            The comparison to use to query the record. See Notes for more details.
        longitude
            The longitude of the record to query.
        page_size
            The number of results to return per page.
        fields
            The fields to return. If empty, all fields are returned.
            Example: "id,name,description,type"
        all_pages
            True to return all pages. False to return the first page.

        Returns
        -------
        list[dict]
            A list of records.

        Raises
        ------
        ValueError
            If the comparison is not one of the allowed comparisons.

        Notes
        -----
        The ``comparison`` must be one of the following: "eq", "gt", "lt", "gte", "lte".

        - eq : Matches values that are equal to the given value.
        - gt : Matches if values are greater than the given value.
        - lt : Matches if values are less than the given value.
        - gte : Matches if values are greater or equal to the given value.
        - lte : Matches if values are less or equal to the given value.
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
        result = self.get_records(filter, page_size, fields, all_pages, shape="records")
        return cast(list[dict], result)

    def get_record_by_lat_long(
        self,
        lat_comparison: str,
        long_comparison: str,
        latitude: float,
        longitude: float,
        page_size: int = 25,
        fields: str = "",
        all_pages: bool = False,
    ) -> list[dict]:
        """
        Retrieve records by latitude and longitude filters via the NMDC API.

        Parameters
        ----------
        lat_comparison
            The comparison to use to query the record for latitude. See Notes for more details.
        long_comparison
            The comparison to use to query the record for longitude. See Notes for more details.
        latitude
            The latitude of the record to query.
        longitude
            The longitude of the record to query.
        page_size
            The number of results to return per page.
        fields
            The fields to return. If empty, all fields are returned.
            Example: "id,name,description,type"
        all_pages
            True to return all pages. False to return the first page.

        Returns
        -------
        list[dict]
            A list of records.

        Raises
        ------
        ValueError
            If the comparison is not one of the allowed comparisons.

        Notes
        -----
        ``lat_comparison`` and ``long_comparison`` must be one of the following:

        - eq : Matches values that are equal to the given value.
        - gt : Matches if values are greater than the given value.
        - lt : Matches if values are less than the given value.
        - gte : Matches if values are greater or equal to the given value.
        - lte : Matches if values are less or equal to the given value.

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
        results = self.get_records(
            filter, page_size, fields, all_pages, shape="records"
        )
        return cast(list[dict], results)
