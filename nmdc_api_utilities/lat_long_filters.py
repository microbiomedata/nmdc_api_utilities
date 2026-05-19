# -*- coding: utf-8 -*-
import logging
import math
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
        all_pages: bool = True,
        shape: Literal["records", "dataframe"] = "records",
    ) -> list[dict] | pd.DataFrame:
        """Retrieve records from a collection via the NMDC API."""

    def get_record_by_latitude(
        self,
        comparison: str,
        latitude: float,
        page_size: int = 25,
        fields: str = "",
        all_pages: bool = True,
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
            True to return all pages. False to return only the first page.

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
        all_pages: bool = True,
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
            True to return all pages. False to return only the first page.

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
        all_pages: bool = True,
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
            True to return all pages. False to return only the first page.

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

    @staticmethod
    def _bounding_box(center_lat: float, center_lon: float, radius_m: float):
        """
        Compute (min_lat, max_lat, min_lon, max_lon) for a circle of radius_m (meters)
        around (center_lat, center_lon). Good approximation for typical radii.
        """
        R = 6378137.0  # Earth radius in meters (WGS84)
        lat_rad = math.radians(center_lat)

        # Angular distance in radians on Earth’s surface
        ang_dist = radius_m / R

        # Latitude bounds
        min_lat = center_lat - math.degrees(ang_dist)
        max_lat = center_lat + math.degrees(ang_dist)

        # Longitude bounds
        if abs(lat_rad) > (math.pi / 2 - 1e-6):
            # Near the poles: longitude is essentially all longitudes
            min_lon = -180.0
            max_lon = 180.0
        else:
            delta_lon = math.asin(math.sin(ang_dist) / math.cos(lat_rad))
            min_lon = center_lon - math.degrees(delta_lon)
            max_lon = center_lon + math.degrees(delta_lon)

        return min_lat, max_lat, min_lon, max_lon

    @staticmethod
    def _haversine_distance_m(
        lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Great-circle distance in meters between two points on Earth.
        """
        R = 6378137.0  # Earth radius in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = (
            math.sin(dphi / 2.0) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return R * c

    def get_record_by_proximity(
        self,
        radius_km: float,
        record_id: str | None = None,
        query_lat: float | None = None,
        query_lon: float | None = None,
        page_size: int = 25,
        fields: str = "",
        all_pages: bool = True,
    ) -> list[dict]:
        """
        Retrieve records by proximity to a record or lat lon via the NMDC API.
        First retrieve records within a bounding box, then refine to those within the circular radius.

        Parameters
        ----------
        radius_km
            The radius in kilometers to search for records around the record.
        record_id
            The ID of a record to query where lat/lon are provided (Biosample or FieldResearchSite). If provided, query_lat and query_lon must not be provided.
        query_lat
            The latitude, in decimal degrees, to query. If provided, record_id must not be provided.
            Example: 63.875088
        query_lon
            The longitude, in decimal degrees, to query. If provided, record_id must not be provided.
            Example: -149.210438
        page_size
            The number of results to return per page.
        fields
            The fields to return. If empty, all fields are returned.
            Example: "id,name,description,type"
        all_pages
            True to return all pages. False to return only the first page.

        Returns
        -------
        list[dict]
            A list of records.

        """
        radius_meters = radius_km * 1000

        if record_id is not None and (query_lat is not None or query_lon is not None):
            logger.error(
                "Invalid input: ONLY record_id or query_lat/query_lon can be used, not both."
            )
            raise ValueError(
                "Invalid input: ONLY record_id or query_lat/query_lon can be used, not both."
            )
        if (
            query_lat is not None
            and query_lon is None
            or query_lat is None
            and query_lon is not None
        ):
            logger.error(
                "Invalid input: BOTH query_lat and query_lon must be provided."
            )
            raise ValueError(
                "Invalid input: BOTH query_lat and query_lon must be provided."
            )

        # Calculate bounding box for mongoDB query
        if record_id is not None:
            record_lat_lon = self.get_records(
                filter=f'{{"id": "{record_id}"}}',
                max_page_size=1,
                fields="lat_lon",
                all_pages=False,
                shape="records",
            )
            center_lat = record_lat_lon[0].get("lat_lon", {}).get("latitude")
            center_lon = record_lat_lon[0].get("lat_lon", {}).get("longitude")
        if query_lat is not None and query_lon is not None:
            center_lat = query_lat
            center_lon = query_lon
        min_lat, max_lat, min_lon, max_lon = self._bounding_box(
            center_lat, center_lon, radius_meters
        )

        # MongoDB query with bounding box
        filter = f'{{"lat_lon.latitude": {{"$gte": {min_lat}, "$lte": {max_lat}}},"lat_lon.longitude": {{"$gte": {min_lon}, "$lte": {max_lon}}}}}'
        results = cast(
            list[dict],
            self.get_records(filter, page_size, fields, all_pages, shape="records"),
        )

        # Refine results to those within circular radius
        refined_results = []
        for record in results:
            lat_lon = record.get("lat_lon")
            if not isinstance(lat_lon, dict):
                continue
            rec_lat = lat_lon.get("latitude")
            rec_lon = lat_lon.get("longitude")
            if rec_lat is not None and rec_lon is not None:
                distance = self._haversine_distance_m(
                    center_lat, center_lon, rec_lat, rec_lon
                )
                if distance <= radius_meters:
                    refined_results.append(record)

        return cast(list[dict], refined_results)
