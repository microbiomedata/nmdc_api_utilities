# -*- coding: utf-8 -*-
"""
Module for traversing relationships between NMDC objects using the linked_instances endpoint.
"""
from __future__ import annotations

import requests
from nmdc_api_utilities.nmdc_search import NMDCSearch
import logging
import time
import urllib.parse

logger = logging.getLogger(__name__)


class LinkedInstancesSearch(NMDCSearch):
    """
    Wrapper for the NMDC API /linked_instances endpoint.

    This endpoint performs transitive graph traversal to find all objects linked to
    specified nexus IDs, both upstream (provenance) and downstream (derived data).

    Parameters
    ----------
    env : str, optional
        API environment: "prod" (default) or "dev"

    Examples
    --------
    >>> from nmdc_api_utilities.linked_instances_search import LinkedInstancesSearch
    >>> client = LinkedInstancesSearch()
    >>> # Find all DataObjects downstream of a biosample
    >>> results = client.get_linked_instances(
    ...     ids=["nmdc:bsm-11-x5xj6p33"],
    ...     types=["nmdc:DataObject"],
    ...     hydrate=False,
    ...     max_page_size=10
    ... )
    >>> isinstance(results, list)
    True
    >>> len(results) > 0
    True
    """

    def __init__(self, env="prod"):
        super().__init__(env=env)

    def get_linked_instances(
        self,
        ids: list[str],
        types: list[str] | None = None,
        hydrate: bool = False,
        max_page_size: int = 1000,
        all_pages: bool = True
    ) -> list[dict]:
        """
        Get instances linked to the specified nexus IDs.

        This method performs transitive graph traversal, following both upstream
        (provenance) and downstream (derived data) links from the nexus IDs.

        Parameters
        ----------
        ids : list[str]
            List of NMDC IDs to use as nexus points for graph traversal.
            Example: ["nmdc:bsm-11-x5xj6p33", "nmdc:bsm-11-abc123"]
        types : list[str], optional
            List of NMDC types to filter results. If None, returns all NamedThings.
            Can be abstract types (nmdc:InformationObject) or concrete (nmdc:DataObject).
            Example: ["nmdc:DataObject", "nmdc:Biosample"]
        hydrate : bool, default False
            If False, returns slim documents (id and type only).
            If True, returns full hydrated documents with all fields.
        max_page_size : int, default 1000
            Number of results per page. Maximum depends on API limits.
        all_pages : bool, default True
            If True, automatically fetches all pages and returns complete result set.
            If False, returns only the first page.

        Returns
        -------
        list[dict]
            List of linked instance documents. Each document includes:
            - id: NMDC identifier
            - type: NMDC type (e.g., "nmdc:Biosample")
            - _upstream_of: List of nexus IDs this is upstream of (if applicable)
            - _downstream_of: List of nexus IDs this is downstream of (if applicable)
            - Additional fields if hydrate=True

        Raises
        ------
        ValueError
            If ids is empty or types contains invalid type strings
        RuntimeError
            If API request fails

        Examples
        --------
        >>> client = LinkedInstancesSearch()
        >>> # Find all data objects for a biosample
        >>> data_objects = client.get_linked_instances(
        ...     ids=["nmdc:bsm-11-x5xj6p33"],
        ...     types=["nmdc:DataObject"],
        ...     hydrate=False,
        ...     max_page_size=10
        ... )
        >>> isinstance(data_objects, list)
        True
        >>> len(data_objects) > 0
        True
        """
        # Validation
        if not ids or not isinstance(ids, list):
            raise ValueError("ids must be a non-empty list of NMDC ID strings")

        if types is not None and not isinstance(types, list):
            raise ValueError("types must be a list of NMDC type strings or None")

        # Build URL with proper encoding
        url = f"{self.base_url}/nmdcschema/linked_instances"

        # Construct query string manually for multiple ids
        query_parts = []
        for id_val in ids:
            query_parts.append(f"ids={urllib.parse.quote(id_val)}")

        if types:
            for type_val in types:
                query_parts.append(f"types={urllib.parse.quote(type_val)}")

        query_parts.append(f"hydrate={str(hydrate).lower()}")
        query_parts.append(f"max_page_size={max_page_size}")

        full_url = f"{url}?{'&'.join(query_parts)}"

        logger.info(f"Making API request to: {full_url}")
        start_time = time.time()

        try:
            response = requests.get(full_url)
            elapsed = time.time() - start_time
            logger.info(f"API request completed in {elapsed:.2f}s (status: {response.status_code})")
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            elapsed = time.time() - start_time
            logger.error(f"API request failed after {elapsed:.2f}s", exc_info=True)

            # Try to extract API error details
            error_detail = None
            try:
                if hasattr(e, 'response') and e.response is not None:
                    error_json = e.response.json()
                    error_detail = error_json.get('detail', None)
            except:
                pass

            if error_detail:
                raise RuntimeError(f"NMDC API error: {error_detail}") from e
            else:
                raise RuntimeError("Failed to get linked instances from NMDC API") from e

        logger.debug(
            f"API response: {response.json()}\nStatus: {response.status_code}"
        )

        results = response.json()["resources"]

        # Handle pagination if requested
        if all_pages:
            results = self._get_all_pages(response, ids, types, hydrate, max_page_size)

        return results

    def _get_all_pages(
        self,
        response: requests.Response,
        ids: list[str],
        types: list[str] | None,
        hydrate: bool,
        max_page_size: int
    ) -> list[dict]:
        """
        Fetch all pages of results using pagination tokens.

        Parameters
        ----------
        response : requests.Response
            Initial response containing first page and optional next_page_token
        ids : list[str]
            Original nexus IDs
        types : list[str] or None
            Type filter
        hydrate : bool
            Hydration flag
        max_page_size : int
            Page size

        Returns
        -------
        list[dict]
            Complete list of all results across all pages
        """
        all_results = response.json()["resources"]

        while True:
            # Check for next page token
            response_json = response.json()
            next_token = response_json.get("next_page_token")

            if not next_token:
                break

            logger.info(f"Fetching next page (token: {next_token[:20]}...)")

            # Build URL for next page
            url = f"{self.base_url}/nmdcschema/linked_instances"
            query_parts = []

            for id_val in ids:
                query_parts.append(f"ids={urllib.parse.quote(id_val)}")

            if types:
                for type_val in types:
                    query_parts.append(f"types={urllib.parse.quote(type_val)}")

            query_parts.append(f"hydrate={str(hydrate).lower()}")
            query_parts.append(f"max_page_size={max_page_size}")
            query_parts.append(f"page_token={urllib.parse.quote(next_token)}")

            full_url = f"{url}?{'&'.join(query_parts)}"

            try:
                response = requests.get(full_url)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                logger.error("Pagination request failed", exc_info=True)
                raise RuntimeError("Failed to fetch next page of linked instances") from e

            # Append results
            page_results = response.json()["resources"]
            all_results.extend(page_results)
            logger.info(f"Fetched {len(page_results)} results (total: {len(all_results)})")

        return all_results

    def get_linked_by_direction(
        self,
        ids: list[str],
        types: list[str] | None = None,
        direction: str = "both",
        hydrate: bool = False,
        max_page_size: int = 1000
    ) -> dict[str, list[dict]]:
        """
        Get linked instances grouped by relationship direction.

        This is a convenience method that calls get_linked_instances and groups
        results by whether they are upstream or downstream of the nexus IDs.

        Parameters
        ----------
        ids : list[str]
            Nexus IDs for graph traversal
        types : list[str], optional
            Type filter
        direction : str, default "both"
            Which direction to return: "upstream", "downstream", or "both"
        hydrate : bool, default False
            Whether to return full documents
        max_page_size : int, default 1000
            Results per page

        Returns
        -------
        dict
            Dictionary with keys:
            - "upstream": List of instances upstream of nexus IDs
            - "downstream": List of instances downstream of nexus IDs
            - "both": List of instances with both upstream and downstream relationships

        Raises
        ------
        ValueError
            If direction is not one of "upstream", "downstream", or "both"

        Examples
        --------
        >>> client = LinkedInstancesSearch()
        >>> results = client.get_linked_by_direction(
        ...     ids=["nmdc:bsm-11-x5xj6p33"],
        ...     types=["nmdc:Study"],
        ...     direction="upstream",
        ...     max_page_size=10
        ... )
        >>> "upstream" in results
        True
        """
        if direction not in ["upstream", "downstream", "both"]:
            raise ValueError("direction must be 'upstream', 'downstream', or 'both'")

        # Get all linked instances
        all_results = self.get_linked_instances(
            ids=ids,
            types=types,
            hydrate=hydrate,
            max_page_size=max_page_size,
            all_pages=True
        )

        # Group by direction
        grouped = {
            "upstream": [],
            "downstream": [],
            "both": []
        }

        for result in all_results:
            has_upstream = "_upstream_of" in result
            has_downstream = "_downstream_of" in result

            if has_upstream and has_downstream:
                grouped["both"].append(result)
            elif has_upstream:
                grouped["upstream"].append(result)
            elif has_downstream:
                grouped["downstream"].append(result)

        # Return based on direction filter
        if direction == "both":
            return grouped
        elif direction == "upstream":
            return {"upstream": grouped["upstream"] + grouped["both"]}
        else:  # downstream
            return {"downstream": grouped["downstream"] + grouped["both"]}
