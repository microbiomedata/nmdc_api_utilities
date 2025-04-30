# -*- coding: utf-8 -*-

from nmdc_api_utilities.collection_search import CollectionSearch


class FunctionalSearch:
    """
    Class to interact with the NMDC API to filter functional annotations by KEGG, COG, or PFAM ids.
    """

    def __init__(self, env="prod"):
        self.collectioninstance = CollectionSearch(
            collection_name="functional_annotation_agg", env=env
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
        Get a record from the NMDC API by id. ID types can be KEGG, COG, or PFAM.
        Parameters
        -----------
        annotation: str
            The data base id to query the function annotations.
        annotation_type:
            The type of id to query. MUST be one of the following:
                KEGG
                COG
                PFAM
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
        """
        if annotation_type not in ["KEGG", "COG", "PFAM"]:
            raise ValueError("id_type must be one of the following: KEGG, COG, PFAM")
        if annotation_type == "KEGG":
            formatted_annotation_type = f"KEGG.ORTHOLOGY:{annotation}"
        elif annotation_type == "COG":
            formatted_annotation_type = f"COG:{annotation}"
        elif annotation_type == "PFAM":
            formatted_annotation_type = f"PFAM:{annotation}"

        filter = f'{{"gene_function_id": "{formatted_annotation_type}"}}'

        result = self.collectioninstance.get_record_by_filter(
            filter, page_size, fields, all_pages
        )
        return result

    def get_records(
        self,
        filter: str = "",
        max_page_size: int = 100,
        fields: str = "",
        all_pages: bool = False,
    ) -> list[dict]:
        """
        Get a collection of data from the NMDC API. Generic function to get a collection of data from the NMDC API. Can provide a specific filter if desired.
        Parameters
        ----------
        filter: str
            The filter to apply to the query. Default is an empty string.
        max_page_size: int
            The maximum number of items to return per page. Default is 100.
        fields: str
            The fields to return. Default is all fields.
        Returns
        -------
        list[dict]
            A list of records.
        """
        return self.collectioninstance.get_records(
            filter, max_page_size, fields, all_pages
        )
