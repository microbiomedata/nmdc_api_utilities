# -*- coding: utf-8 -*-
from __future__ import annotations

from nmdc_api_utilities.collection_search import CollectionSearch
import logging
import requests
import urllib.parse

logger = logging.getLogger(__name__)


class DataObjectSearch(CollectionSearch):
    """
    Class to interact with the NMDC API to get data object sets.
    """

    def __init__(self, env="prod"):
        super().__init__(collection_name="data_object_set", env=env)
        self.env = env  # Store for use in linking methods

    def get_data_objects_for_studies(
        self, study_id: str, max_page_size: int = 100
    ) -> list[dict]:
        """
        Get data objects by study id.
        Parameters
        ----------
        study_id: str
            The study id to search for.
        max_page_size: int
            The maximum number of items to return per page. Default is 100
        Returns
        -------
        list[dict]
            A list of data objects.
        Raises
        ------
        RuntimeError
            If the API request fails.
        """
        url = f"{self.base_url}/data_objects/study/{study_id}?max_page_size={max_page_size}"
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error("API request failed", exc_info=True)
            raise RuntimeError("Failed to get data_objects from NMDC API") from e
        else:
            logging.debug(
                f"API request response: {response.json()}\n API Status Code: {response.status_code}"
            )

        results = response.json()

        return results

    def get_linked_biosample(self, data_object_id: str, hydrate: bool = True) -> list[dict]:
        """
        Trace a data object back to its source biosample(s).

        This follows the provenance chain upstream through workflow executions
        and data generations to find the originating biosamples.

        Parameters
        ----------
        data_object_id : str
            NMDC data object ID
        hydrate : bool, default True
            Whether to return full biosample documents

        Returns
        -------
        list[dict]
            List of Biosample objects (typically 1, but could be more for merged data)

        Examples
        --------
        >>> from nmdc_api_utilities.data_object_search import DataObjectSearch
        >>> client = DataObjectSearch()
        >>> biosamples = client.get_linked_biosample("nmdc:dobj-11-nf3t6f36")
        >>> len(biosamples) > 0
        True
        >>> all(b["type"] == "nmdc:Biosample" for b in biosamples)
        True
        """
        from nmdc_api_utilities.linked_instances_search import LinkedInstancesSearch

        linker = LinkedInstancesSearch(env=self.env)
        return linker.get_linked_instances(
            ids=[data_object_id],
            types=["nmdc:Biosample"],
            hydrate=hydrate
        )

    def get_linked_study(self, data_object_id: str, hydrate: bool = True) -> list[dict]:
        """
        Find the study that a data object belongs to.

        Parameters
        ----------
        data_object_id : str
            NMDC data object ID
        hydrate : bool, default True
            Whether to return full study documents

        Returns
        -------
        list[dict]
            List of Study objects

        Examples
        --------
        >>> client = DataObjectSearch()
        >>> studies = client.get_linked_study("nmdc:dobj-11-nf3t6f36")
        >>> len(studies) > 0
        True
        >>> all(s["type"] == "nmdc:Study" for s in studies)
        True
        """
        from nmdc_api_utilities.linked_instances_search import LinkedInstancesSearch

        linker = LinkedInstancesSearch(env=self.env)
        return linker.get_linked_instances(
            ids=[data_object_id],
            types=["nmdc:Study"],
            hydrate=hydrate
        )

    def get_provenance_chain(self, data_object_id: str, hydrate: bool = False) -> dict:
        """
        Get complete provenance chain for a data object.

        Returns all upstream entities including workflow executions, data generations,
        processed samples, biosamples, and studies.

        Parameters
        ----------
        data_object_id : str
            NMDC data object ID
        hydrate : bool, default False
            Whether to return full documents (can be large for full chains)

        Returns
        -------
        dict
            Dictionary with keys for each entity type:
            - "biosamples": List of source biosamples
            - "studies": List of associated studies
            - "workflow_executions": List of workflow executions in chain
            - "data_generations": List of data generation processes
            - "processed_samples": List of processed samples
            - "data_objects": Other data objects in chain

        Examples
        --------
        >>> client = DataObjectSearch()
        >>> provenance = client.get_provenance_chain("nmdc:dobj-11-nf3t6f36")
        >>> "biosamples" in provenance and "studies" in provenance
        True
        >>> len(provenance["biosamples"]) > 0 or len(provenance["studies"]) > 0
        True
        """
        from nmdc_api_utilities.linked_instances_search import LinkedInstancesSearch

        linker = LinkedInstancesSearch(env=self.env)

        # Get everything upstream (no type filter)
        all_upstream = linker.get_linked_by_direction(
            ids=[data_object_id],
            direction="upstream",
            hydrate=hydrate
        )["upstream"]

        # Group by type
        grouped = {
            "biosamples": [],
            "studies": [],
            "workflow_executions": [],
            "data_generations": [],
            "processed_samples": [],
            "data_objects": []
        }

        for entity in all_upstream:
            entity_type = entity.get("type", "")

            if entity_type == "nmdc:Biosample":
                grouped["biosamples"].append(entity)
            elif entity_type == "nmdc:Study":
                grouped["studies"].append(entity)
            elif "WorkflowExecution" in entity_type or "Analysis" in entity_type:
                grouped["workflow_executions"].append(entity)
            elif "DataGeneration" in entity_type or (entity_type.startswith("nmdc:") and entity_type.endswith("ometry")):
                grouped["data_generations"].append(entity)
            elif entity_type == "nmdc:ProcessedSample":
                grouped["processed_samples"].append(entity)
            elif entity_type == "nmdc:DataObject":
                grouped["data_objects"].append(entity)

        return grouped
