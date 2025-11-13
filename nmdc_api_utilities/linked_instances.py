# -*- coding: utf-8 -*-
import requests
from nmdc_api_utilities.nmdc_search import NMDCSearch


class LinkedInstances(NMDCSearch):
    """
    Class for interacting with the NMDC linked instances API.

    Inherits from NMDCSearch to utilize the base URL setup.
    """

    def __init__(self, env="prod"):
        super().__init__(env=env)

    def linked_instances(
        self, types: list[str] | str, ids: list[str] | str
    ) -> list[dict]:
        """
        Given a list of sample ids, find the associated study ids.

        Parameters
        ----------
        types : list[str] | str
            The types of instances you want to return
        ids : list[str] | str
            The ids to search for.

        Returns
        -------
        list[dict]
            A list of linked instance records.
        """
        # highest number I could get to without a timeout
        batch_size = 250
        batch_records = []
        url = f"{self.base_url}/nmdcschema/linked_instances"
        # split the ids into batches
        for i in range(0, len(ids), batch_size):
            batch = ids[i : i + batch_size]
            params = {"types": types, "ids": batch}
            response = requests.get(url=url, params=params)
            if response.status_code == 200:
                batch_resources = response.json().get("resources", [])
                next_page = response.json().get("next_page_token", None)
                batch_records.extend(batch_resources)
                if next_page:
                    while next_page:
                        params = {
                            "types": types,
                            "ids": batch,
                            "page_token": next_page,
                        }
                        response = requests.get(url=url, params=params)
                        if response.status_code == 200:
                            batch_resources = response.json().get("resources", [])
                            batch_records.extend(batch_resources)
                            next_page = response.json().get("next_page_token", None)
            else:
                raise RuntimeError(
                    f"Error fetching linked instances: {response.status_code} {response.text}"
                )
        return batch_records

    def associate_ids_with_linked_instances(
        self, types: list[str] | str, ids: list[str] | str
    ) -> dict[str, list[str]]:
        """
        Given a list of ids, find the associated linked instances and
        return a dictionary mapping each id to its linked instances.

        Parameters
        ----------
        types : list[str] | str
            The types of instances you want to return
        ids : list[str] | str
            The ids to search for.

        Returns
        -------
        dict[str, list[str]]
            A dictionary mapping each input id to a list of its linked instance records.
        """
        # get the linked instances
        linked_instances = self.linked_instances(types=types, ids=ids)
        association = {}
        # loop through the linked instances and build the association
        for record in linked_instances:
            study_id = record["id"]
            if "_upstream_of" in record:
                for upstream_id in record["_upstream_of"]:
                    if upstream_id not in association:
                        association[upstream_id] = []
                    association[upstream_id].append(study_id)

        return association
