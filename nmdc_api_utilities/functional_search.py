# -*- coding: utf-8 -*-

from nmdc_api_utilities.collection_search import CollectionSearch
from nmdc_api_utilities.config import API_BASE_URL


class FunctionalSearch(CollectionSearch):
    """
    Class to interact with the NMDC API to search for records within the ``functional_annotation_agg`` collection.
    """

    supports_get_by_id = False

    def __init__(self, api_base_url: str = API_BASE_URL, env: str = ""):
        super().__init__(
            collection_name="functional_annotation_agg",
            api_base_url=api_base_url,
            env=env,
        )

    def get_functional_annotations(
        self,
        annotation: str,
        annotation_type: str,
        page_size: int = 25,
        fields: str = "",
        all_pages: bool = False,
    ) -> list[dict]:
        """
        Retrieve records with specific annotation value and type.

        Parameters
        -----------
        annotation: str
            The functional annotation value to query.
        annotation_type:
            The type of id to query. See Notes for more details.
        page_size: int
            The number of results to return per page. Default is 25.
        fields: str
            The fields to return. Default is all fields.
            Example: "id,name"
        all_pages: bool
            True to return all pages. False to return the first page. Default is False.

        Returns
        -------
        list[dict]
            A list of functional annotations.

        Raises
        ------
        ValueError
            If the annotation_type is not one of the allowed types. See Notes for more details.

        Notes
        -----
        The ``annotation_type`` must be one of the following: "KEGG", "COG", "PFAM".
        """
        if annotation_type not in ["KEGG", "COG", "PFAM"]:
            raise ValueError(
                "annotation_type must be one of the following: KEGG, COG, PFAM"
            )
        if annotation_type == "KEGG":
            formatted_annotation_type = f"KEGG.ORTHOLOGY:{annotation}"
        elif annotation_type == "COG":
            formatted_annotation_type = f"COG:{annotation}"
        elif annotation_type == "PFAM":
            formatted_annotation_type = f"PFAM:{annotation}"

        filter = f'{{"gene_function_id": "{formatted_annotation_type}"}}'

        result = self.get_record_by_filter(filter, page_size, fields, all_pages)
        return result
