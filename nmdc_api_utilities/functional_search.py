# -*- coding: utf-8 -*-

from typing import cast

from nmdc_api_utilities.collection_search import CollectionSearch
from nmdc_api_utilities.config import API_BASE_URL
from nmdc_api_utilities.decorators import has_deprecated_parameter


@has_deprecated_parameter("env", reason="Use ``api_base_url`` instead.")
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
        all_pages: bool = True,
    ) -> list[dict]:
        """
        Retrieve records with specific annotation value and type.

        Parameters
        -----------
        annotation
            The functional annotation value to query.
        annotation_type
            The type of id to query. See Notes for more details.
        page_size
            The number of results to return per page.
        fields
            The fields to return. If empty, all fields are returned.
            Example: "id,name"
        all_pages
            True to return all pages. False to return only the first page.

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

        result = self.get_record_by_filter(
            filter, page_size, fields, all_pages, shape="records"
        )
        records = cast(list[dict], result)
        return records
