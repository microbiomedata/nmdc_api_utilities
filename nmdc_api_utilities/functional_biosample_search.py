# -*- coding: utf-8 -*-
"""
Module for searching biosamples by functional annotations (PFAM, KEGG, COG, GO).

This module uses the specialized biosample search endpoint at
data.microbiomedata.org/api/biosample/search which supports filtering
by functional annotations. This is different from the standard nmdcschema
API which does not support functional filtering.
"""

import requests
import logging
from typing import Union
from nmdc_api_utilities.nmdc_search import NMDCSearch

logger = logging.getLogger(__name__)


def _parse_function_id(function_id: str) -> tuple[str, str]:
    """
    Parse a function ID into (prefix, id).

    Parameters
    ----------
    function_id : str
        Function ID with or without prefix

    Returns
    -------
    tuple[str, str]
        (prefix, id) tuple

    Examples
    --------
    >>> _parse_function_id("PFAM:PF00005")
    ('PFAM', 'PF00005')
    >>> _parse_function_id("KEGG.ORTHOLOGY:K00001")
    ('KEGG.ORTHOLOGY', 'K00001')
    >>> _parse_function_id("PF00005")
    ('PFAM', 'PF00005')
    >>> _parse_function_id("K00001")
    ('KEGG.ORTHOLOGY', 'K00001')
    """
    # If it has a colon, split on it
    if ":" in function_id:
        parts = function_id.split(":", 1)
        return (parts[0], parts[1])

    # Otherwise, try to infer the type from the format
    # PFAM: PFxxxxx
    if function_id.startswith("PF") and len(function_id) >= 7:
        return ("PFAM", function_id)
    # KEGG: Kxxxxx
    elif function_id.startswith("K") and function_id[1:].isdigit():
        return ("KEGG.ORTHOLOGY", function_id)
    # COG: COGxxxx
    elif function_id.startswith("COG"):
        return ("COG", function_id)
    # GO: GOxxxxxxx or numeric
    elif function_id.startswith("GO"):
        return ("GO", function_id)

    raise ValueError(
        f"Cannot parse function ID '{function_id}'. "
        "Expected format: PREFIX:ID (e.g., PFAM:PF00005) or recognizable ID format"
    )


def _determine_function_table(prefix: str) -> str:
    """
    Map function ID prefix to API table name.

    Parameters
    ----------
    prefix : str
        Function ID prefix (e.g., "PFAM", "KEGG.ORTHOLOGY")

    Returns
    -------
    str
        Table name for the API

    Examples
    --------
    >>> _determine_function_table("PFAM")
    'pfam_function'
    >>> _determine_function_table("KEGG.ORTHOLOGY")
    'kegg_function'
    >>> _determine_function_table("COG")
    'cog_function'
    >>> _determine_function_table("GO")
    'go_function'
    """
    table_map = {
        "PFAM": "pfam_function",
        "KEGG.ORTHOLOGY": "kegg_function",
        "KEGG": "kegg_function",  # Accept KEGG without .ORTHOLOGY
        "COG": "cog_function",
        "GO": "go_function",
    }

    if prefix not in table_map:
        raise ValueError(
            f"Unsupported function type '{prefix}'. "
            f"Supported types: {', '.join(table_map.keys())}"
        )

    return table_map[prefix]


class FunctionalBiosampleSearch(NMDCSearch):
    """
    Search for biosamples by functional annotations (PFAM, KEGG, COG, GO).

    This class uses the specialized biosample search endpoint at
    https://data.microbiomedata.org/api/biosample/search which supports
    filtering by functional annotations.

    Unlike the standard nmdcschema API, this endpoint can find biosamples
    that contain specific functional annotations like PFAM domains.

    Examples
    --------
    >>> from nmdc_api_utilities.functional_biosample_search import FunctionalBiosampleSearch
    >>> client = FunctionalBiosampleSearch()
    >>> # Search for biosamples with a specific PFAM domain
    >>> results = client.search_by_pfam(["PF00005"], limit=5)
    >>> results["count"] > 0
    True
    >>> len(results["results"]) <= 5
    True
    """

    def __init__(self, env="prod"):
        """
        Initialize the FunctionalBiosampleSearch client.

        Parameters
        ----------
        env : str, default "prod"
            Environment to use ("prod" or "dev")
        """
        super().__init__(env=env)
        # Use the data API endpoint, not the schema endpoint
        if env == "prod":
            self.data_base_url = "https://data.microbiomedata.org"
        elif env == "dev":
            self.data_base_url = "https://data-dev.microbiomedata.org"
        else:
            raise ValueError("env must be one of the following: prod, dev")

    def search_by_functions(
        self,
        function_ids: list[str],
        limit: int = 100,
        offset: int = 0,
        logic: str = "AND",
    ) -> dict:
        """
        Search biosamples containing specified functional annotations.

        Parameters
        ----------
        function_ids : list[str]
            Function IDs with or without prefixes. Examples:
            - PFAM: "PFAM:PF00005" or "PF00005"
            - KEGG: "KEGG.ORTHOLOGY:K00001" or "K00001"
            - COG: "COG:COG0001" or "COG0001"
            - GO: "GO:GO0000001" or "GO0000001"
        limit : int, default 100
            Maximum biosamples to return
        offset : int, default 0
            Pagination offset
        logic : str, default "AND"
            "AND" returns samples with ALL functions
            "OR" returns samples with ANY function (client-side implementation)

        Returns
        -------
        dict
            {
                "count": int,           # Total biosamples available
                "results": list[dict],  # Biosample records
                "search_criteria": dict # Query parameters used
            }

        Raises
        ------
        ValueError
            If function_ids is empty or contains invalid IDs
        RuntimeError
            If the API request fails

        Examples
        --------
        >>> client = FunctionalBiosampleSearch()
        >>> # Search with PFAM ID
        >>> results = client.search_by_functions(["PFAM:PF00005"], limit=5)
        >>> "count" in results and "results" in results
        True
        >>> # Search with multiple functions (AND logic)
        >>> results = client.search_by_functions(
        ...     ["PFAM:PF00005", "KEGG.ORTHOLOGY:K00001"],
        ...     limit=10,
        ...     logic="AND"
        ... )
        >>> "count" in results
        True
        """
        if not function_ids:
            raise ValueError("function_ids cannot be empty")

        if logic not in ["AND", "OR"]:
            raise ValueError("logic must be 'AND' or 'OR'")

        # Parse and validate all function IDs
        parsed_functions = []
        for func_id in function_ids:
            prefix, func_id_clean = _parse_function_id(func_id)
            table = _determine_function_table(prefix)
            # Reconstruct the full ID with proper prefix
            full_id = f"{prefix}:{func_id_clean}"
            parsed_functions.append((full_id, table))

        logger.info(
            f"Searching for biosamples with {logic} logic for functions: "
            f"{[f[0] for f in parsed_functions]}"
        )

        if logic == "AND":
            # Use API's native AND logic
            return self._search_and(parsed_functions, limit, offset)
        else:
            # Implement OR logic client-side
            return self._search_or(parsed_functions, limit, offset)

    def _search_and(
        self, parsed_functions: list[tuple[str, str]], limit: int, offset: int
    ) -> dict:
        """
        Search using AND logic (all functions must be present).

        The API natively supports AND logic by including multiple conditions.
        """
        # Build conditions for all functions
        conditions = []
        for func_id, table in parsed_functions:
            conditions.append(
                {"op": "==", "field": "id", "value": func_id, "table": table}
            )

        payload = {"data_object_filter": [], "conditions": conditions}

        url = f"{self.data_base_url}/api/biosample/search?limit={limit}&offset={offset}"

        logger.debug(f"POST request to {url} with payload: {payload}")

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            return {
                "count": data.get("count", 0),
                "results": data.get("results", []),
                "search_criteria": {
                    "function_ids": [f[0] for f in parsed_functions],
                    "limit": limit,
                    "offset": offset,
                    "logic": "AND",
                },
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}", exc_info=True)
            raise RuntimeError(f"Failed to search biosamples: {e}") from e

    def _search_or(
        self, parsed_functions: list[tuple[str, str]], limit: int, offset: int
    ) -> dict:
        """
        Search using OR logic (any function can be present).

        Since the API doesn't natively support OR logic, we need to:
        1. Query each function separately
        2. Combine results
        3. Deduplicate by biosample ID
        """
        all_biosamples = {}
        total_count = 0

        for func_id, table in parsed_functions:
            conditions = [{"op": "==", "field": "id", "value": func_id, "table": table}]
            payload = {"data_object_filter": [], "conditions": conditions}

            # For OR logic, we need to get more results per query to reach the limit
            # after deduplication
            query_limit = limit * len(parsed_functions)

            url = f"{self.data_base_url}/api/biosample/search?limit={query_limit}&offset={offset}"

            try:
                response = requests.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

                total_count = max(total_count, data.get("count", 0))

                # Add biosamples to our deduplicated dict
                for biosample in data.get("results", []):
                    biosample_id = biosample.get("id")
                    if biosample_id and biosample_id not in all_biosamples:
                        all_biosamples[biosample_id] = biosample

            except requests.exceptions.RequestException as e:
                logger.warning(f"Failed to query function {func_id}: {e}")
                continue

        # Convert to list and apply limit
        results = list(all_biosamples.values())[:limit]

        return {
            "count": len(all_biosamples),  # Total unique biosamples found
            "results": results,
            "search_criteria": {
                "function_ids": [f[0] for f in parsed_functions],
                "limit": limit,
                "offset": offset,
                "logic": "OR",
            },
        }

    def search_by_pfam(
        self, pfam_ids: list[str], limit: int = 100, require_all: bool = True
    ) -> dict:
        """
        Convenience method for PFAM domain searches.

        Parameters
        ----------
        pfam_ids : list[str]
            PFAM IDs with or without "PFAM:" prefix (e.g., ["PF00005", "PF00072"])
        limit : int, default 100
            Maximum biosamples to return
        require_all : bool, default True
            If True, return only samples with ALL PFAMs (AND logic)
            If False, return samples with ANY PFAMs (OR logic)

        Returns
        -------
        dict
            Search results with count, results, and search_criteria

        Examples
        --------
        >>> client = FunctionalBiosampleSearch()
        >>> # Search for samples with specific PFAM domain
        >>> results = client.search_by_pfam(["PF00005"], limit=5)
        >>> "count" in results
        True
        >>> # Search for samples with ALL specified PFAMs
        >>> results = client.search_by_pfam(["PF00005", "PF00072"], require_all=True)
        >>> "results" in results
        True
        """
        # Ensure PFAM prefix
        prefixed_ids = []
        for pfam_id in pfam_ids:
            if not pfam_id.startswith("PFAM:"):
                prefixed_ids.append(f"PFAM:{pfam_id}")
            else:
                prefixed_ids.append(pfam_id)

        logic = "AND" if require_all else "OR"
        return self.search_by_functions(prefixed_ids, limit=limit, logic=logic)

    def search_by_kegg(
        self, kegg_ids: list[str], limit: int = 100, require_all: bool = True
    ) -> dict:
        """
        Convenience method for KEGG orthology searches.

        Parameters
        ----------
        kegg_ids : list[str]
            KEGG IDs with or without prefix (e.g., ["K00001", "K00002"])
        limit : int, default 100
            Maximum biosamples to return
        require_all : bool, default True
            If True, return only samples with ALL KEGGs (AND logic)
            If False, return samples with ANY KEGGs (OR logic)

        Returns
        -------
        dict
            Search results with count, results, and search_criteria

        Examples
        --------
        >>> client = FunctionalBiosampleSearch()
        >>> results = client.search_by_kegg(["K00001"], limit=5)
        >>> "count" in results
        True
        """
        # Ensure KEGG prefix
        prefixed_ids = []
        for kegg_id in kegg_ids:
            if ":" not in kegg_id:
                prefixed_ids.append(f"KEGG.ORTHOLOGY:{kegg_id}")
            else:
                prefixed_ids.append(kegg_id)

        logic = "AND" if require_all else "OR"
        return self.search_by_functions(prefixed_ids, limit=limit, logic=logic)

    def search_by_cog(
        self, cog_ids: list[str], limit: int = 100, require_all: bool = True
    ) -> dict:
        """
        Convenience method for COG searches.

        Parameters
        ----------
        cog_ids : list[str]
            COG IDs with or without prefix (e.g., ["COG0001", "COG0002"])
        limit : int, default 100
            Maximum biosamples to return
        require_all : bool, default True
            If True, return only samples with ALL COGs (AND logic)
            If False, return samples with ANY COGs (OR logic)

        Returns
        -------
        dict
            Search results with count, results, and search_criteria

        Examples
        --------
        >>> client = FunctionalBiosampleSearch()
        >>> results = client.search_by_cog(["COG0001"], limit=5)
        >>> "count" in results
        True
        """
        # Ensure COG prefix
        prefixed_ids = []
        for cog_id in cog_ids:
            if not cog_id.startswith("COG:"):
                prefixed_ids.append(f"COG:{cog_id}")
            else:
                prefixed_ids.append(cog_id)

        logic = "AND" if require_all else "OR"
        return self.search_by_functions(prefixed_ids, limit=limit, logic=logic)

    def search_by_go(
        self, go_ids: list[str], limit: int = 100, require_all: bool = True
    ) -> dict:
        """
        Convenience method for GO (Gene Ontology) searches.

        Parameters
        ----------
        go_ids : list[str]
            GO IDs with or without prefix (e.g., ["GO0000001", "GO:0000002"])
        limit : int, default 100
            Maximum biosamples to return
        require_all : bool, default True
            If True, return only samples with ALL GOs (AND logic)
            If False, return samples with ANY GOs (OR logic)

        Returns
        -------
        dict
            Search results with count, results, and search_criteria

        Examples
        --------
        >>> client = FunctionalBiosampleSearch()
        >>> results = client.search_by_go(["GO0000001"], limit=5)
        >>> "count" in results
        True
        """
        # Ensure GO prefix
        prefixed_ids = []
        for go_id in go_ids:
            if not go_id.startswith("GO:"):
                prefixed_ids.append(f"GO:{go_id}")
            else:
                prefixed_ids.append(go_id)

        logic = "AND" if require_all else "OR"
        return self.search_by_functions(prefixed_ids, limit=limit, logic=logic)
