# -*- coding: utf-8 -*-
from __future__ import annotations

from nmdc_api_utilities.collection_search import CollectionSearch
from nmdc_api_utilities.lat_long_filters import LatLongFilters
import logging

logger = logging.getLogger(__name__)


class BiosampleSearch(LatLongFilters, CollectionSearch):
    """
    Class to interact with the NMDC API to get biosamples.
    """

    def __init__(self, env="prod"):
        super().__init__(collection_name="biosample_set", env=env)
        self.env = env  # Store for use in linking methods

    def get_linked_studies(self, biosample_id: str, hydrate: bool = True) -> list[dict]:
        """
        Get all studies associated with a biosample.

        Parameters
        ----------
        biosample_id : str
            NMDC biosample ID (e.g., "nmdc:bsm-11-x5xj6p33")
        hydrate : bool, default True
            If True, returns full study documents. If False, returns only id and type.

        Returns
        -------
        list[dict]
            List of Study objects linked to this biosample

        Examples
        --------
        >>> from nmdc_api_utilities.biosample_search import BiosampleSearch
        >>> client = BiosampleSearch()
        >>> studies = client.get_linked_studies("nmdc:bsm-11-x5xj6p33")
        >>> len(studies) > 0
        True
        >>> all(s["type"] == "nmdc:Study" for s in studies)
        True
        """
        from nmdc_api_utilities.linked_instances_search import LinkedInstancesSearch

        linker = LinkedInstancesSearch(env=self.env)
        return linker.get_linked_instances(
            ids=[biosample_id],
            types=["nmdc:Study"],
            hydrate=hydrate
        )

    def get_linked_data_objects(
        self,
        biosample_id: str,
        hydrate: bool = True,
        data_object_types: list[str] | None = None
    ) -> list[dict]:
        """
        Get all data objects associated with a biosample.

        This includes both raw data (from DataGeneration) and processed data
        (from WorkflowExecution). The relationship graph is traversed automatically.

        Parameters
        ----------
        biosample_id : str
            NMDC biosample ID
        hydrate : bool, default True
            Whether to return full documents or just id/type
        data_object_types : list[str], optional
            Filter to specific data object types (e.g., ["Metagenome Raw Reads"]).
            If None, returns all data objects. Requires hydrate=True.

        Returns
        -------
        list[dict]
            List of DataObject documents. Each includes _downstream_of annotation
            indicating it derives from this biosample.

        Examples
        --------
        >>> client = BiosampleSearch()
        >>> data_objects = client.get_linked_data_objects("nmdc:bsm-11-x5xj6p33", hydrate=False)
        >>> len(data_objects) > 0
        True
        >>> all(d["type"] == "nmdc:DataObject" for d in data_objects)
        True
        """
        from nmdc_api_utilities.linked_instances_search import LinkedInstancesSearch

        linker = LinkedInstancesSearch(env=self.env)
        results = linker.get_linked_instances(
            ids=[biosample_id],
            types=["nmdc:DataObject"],
            hydrate=hydrate
        )

        # Filter by data_object_type if requested (requires hydration)
        if data_object_types and hydrate:
            results = [
                r for r in results
                if r.get("data_object_type") in data_object_types
            ]
        elif data_object_types and not hydrate:
            logger.warning(
                "data_object_types filter requires hydrate=True. "
                "Returning all DataObjects."
            )

        return results
