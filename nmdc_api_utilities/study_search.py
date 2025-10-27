# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from nmdc_api_utilities.collection_search import CollectionSearch

logger = logging.getLogger(__name__)


class StudySearch(CollectionSearch):
    """
    Class to interact with the NMDC API to get studies.
    """

    def __init__(self, env="prod"):
        super().__init__(collection_name="study_set", env=env)
        self.env = env  # Store for use in linking methods

    def get_linked_biosamples(self, study_id: str, hydrate: bool = True) -> list[dict]:
        """
        Get all biosamples associated with a study.

        Parameters
        ----------
        study_id : str
            NMDC study ID (e.g., "nmdc:sty-11-547rwq94")
        hydrate : bool, default True
            Whether to return full biosample documents

        Returns
        -------
        list[dict]
            List of Biosample objects in this study

        Examples
        --------
        >>> from nmdc_api_utilities.study_search import StudySearch
        >>> client = StudySearch()
        >>> biosamples = client.get_linked_biosamples("nmdc:sty-11-547rwq94")
        >>> len(biosamples) > 0
        True
        >>> all(b["type"] == "nmdc:Biosample" for b in biosamples)
        True
        """
        from nmdc_api_utilities.linked_instances_search import LinkedInstancesSearch

        linker = LinkedInstancesSearch(env=self.env)
        return linker.get_linked_instances(
            ids=[study_id],
            types=["nmdc:Biosample"],
            hydrate=hydrate
        )

    def get_all_linked_data_objects(
        self,
        study_id: str,
        hydrate: bool = True,
        group_by_type: bool = True
    ) -> dict[str, list[dict]] | list[dict]:
        """
        Get all data objects associated with a study.

        This traverses the entire graph from study through biosamples to all
        derived data objects. Can return thousands of objects for large studies.

        Parameters
        ----------
        study_id : str
            NMDC study ID
        hydrate : bool, default True
            Whether to return full documents
        group_by_type : bool, default True
            If True, returns dict grouped by data_object_type.
            If False, returns flat list.

        Returns
        -------
        dict or list
            If group_by_type=True: Dictionary mapping data_object_type to list of objects
            If group_by_type=False: Flat list of all data objects

        Examples
        --------
        >>> client = StudySearch()
        >>> data_objects = client.get_all_linked_data_objects(
        ...     "nmdc:sty-11-547rwq94",
        ...     hydrate=False,
        ...     group_by_type=False
        ... )
        >>> isinstance(data_objects, list)
        True
        >>> len(data_objects) > 0
        True
        """
        from nmdc_api_utilities.linked_instances_search import LinkedInstancesSearch

        linker = LinkedInstancesSearch(env=self.env)
        results = linker.get_linked_instances(
            ids=[study_id],
            types=["nmdc:DataObject"],
            hydrate=hydrate,
            max_page_size=1000,
            all_pages=True
        )

        if not group_by_type:
            return results

        # Group by data_object_type
        grouped = {}
        for obj in results:
            obj_type = obj.get("data_object_type", "Unknown")
            if obj_type not in grouped:
                grouped[obj_type] = []
            grouped[obj_type].append(obj)

        return grouped
