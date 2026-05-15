# -*- coding: utf-8 -*-
import json
import logging
import re
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


class DataProcessing:
    def __init__(self):
        pass

    def convert_to_df(self, data: list[dict[str, Any]]) -> pd.DataFrame:
        """
        Convert a list of dictionaries to a pandas dataframe.

        Parameters
        ----------
        data
            A list of dictionaries.

        Returns
        -------
        pd.DataFrame
            A pandas dataframe representation of the input dictionaries.
        """
        return pd.DataFrame(data)

    def split_list(
        self, input_list: list[Any], chunk_size: int = 100
    ) -> list[list[Any]]:
        """
        Split a list into chunks of a specified size.

        Parameters
        ----------
        input_list
            The list to split.
        chunk_size
            The size of each chunk.

        Returns
        -------
        list: A list of lists where each sublist has a maximum length of chunk_size.
        """
        result = []
        for i in range(0, len(input_list), chunk_size):
            result.append(input_list[i : i + chunk_size])

        return result

    def rename_columns(
        self, df: pd.DataFrame, new_col_names: list[str]
    ) -> pd.DataFrame:
        """
        Rename columns in a pandas dataframe.

        Parameters
        ----------
        df
            The pandas dataframe whose columns you want to rename.
        new_col_names
            A list of new column names. Names MUST be in order of the columns in the dataframe.
            For example, if the column in the dataframe are named "col1", "col2", and "col3" (in
            that order) and you want to rename "col1" to "new_col1", "col2" to "new_col2",
            and "col3" to "new_col3", you would pass in ``["new_col1", "new_col2", "new_col3"]``.

        Returns
        -------
        pd.DataFrame
            A pandas dataframe with renamed columns.

        """
        df.columns = new_col_names
        return df

    def merge_dataframes(
        self, column: str, df1: pd.DataFrame, df2: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Merge two dataframes.

        Wrapper around ``pandas.merge`` to merge two dataframes on a specified column using an inner join.

        Parameters
        ----------
        column
            The column to merge on.
        df1
            The first dataframe to merge.
        df2
            The second dataframe to merge.

        Returns
        -------
        pd.DataFrame
            A pandas dataframe with the merged data.
        """
        return pd.merge(df1, df2, on=column, how="inner")

    def merge_df(
        self,
        df1: pd.DataFrame,
        df2: pd.DataFrame,
        key1: str,
        key2: str,
    ) -> pd.DataFrame:
        """
        Merges two dataframes using an inner join based on specified keys, automatically exploding list-like columns and removing duplicates.

        Helpful for merging two sets of dataframe results obtained from the ``convert_to_df`` method.

        Parameters
        ----------
        df1
            The first dataframe to merge.
        df2
            The second dataframe to merge.
        key1
            The key in df1 to match with key2 in df2.
        key2
            The key in df2 to match with key1 in df1.

        Returns
        -------
        pd.DataFrame
            A pandas dataframe with the merged data.
        """

        # This function automatically identifies columns that need to be exploded because they contain list-like elements, as drop_duplicates can't handle list elements.
        def identify_and_explode(df):
            for col in df.columns:
                if any(isinstance(item, list) for item in df[col]):
                    df = df.explode(col)
            return df

        df1 = identify_and_explode(df1)
        df2 = identify_and_explode(df2)

        # Merge dataframes
        merged_df = pd.merge(df1, df2, left_on=key1, right_on=key2)
        # Drop any duplicated rows
        merged_df.drop_duplicates(keep="first", inplace=True)
        return merged_df

    def build_filter(
        self, attributes: dict[str, str], exact_match: bool = False
    ) -> str:
        """
        Create a MongoDB filter using $regex for each attribute in the input dictionary. For nested attributes, use dot notation.

        Parameters
        ----------
        attributes
            Dictionary of attribute names and their corresponding values to match using regex.
            Example: {"name": "example", "description": "example", "geo_loc_name": "example"}
        exact_match
            This var is used to determine if the inputted attribute value is an exact match or a partial match. Default is False, meaning the user does not need to input an exact match.
            Under the hood this is used to determine if the inputted attribute value should be wrapped in a regex expression.
        Returns
        -------
        str
            A string representing the MongoDB filter.
        """
        filter_dict: dict[str, str | dict[str, str]] = {}
        if exact_match:
            for attribute_name, attribute_value in attributes.items():
                filter_dict[attribute_name] = attribute_value
        else:
            for attribute_name, attribute_value in attributes.items():
                # escape special characters - mongo db filters require special characters to be double escaped ex. GC\\-MS \\(2009\\)
                escaped_value = re.sub(r"([\W])", r"\\\1", attribute_value)
                logging.debug(f"Escaped value: {escaped_value}")
                logging.debug(f"Attribute name: {attribute_name}")
                filter_dict[attribute_name] = {"$regex": escaped_value, "$options": "i"}
                logging.debug(f"Filter dict: {filter_dict}")

        clean = json.dumps(filter_dict)
        logging.debug(f"Filter cleaned: {clean}")
        return clean

    def extract_field(
        self, api_results: list[dict[str, Any]], field_name: str
    ) -> list[Any]:
        """
        Extract a specific field's values from records retrieved via the NMDC API.

        Parameters
        ----------
        api_results
            A list of dictionaries.
        field_name
            The name of the field to extract.

        Returns
        -------
        list
            A list of values for the specified field.
        """
        field_list: list[Any] = []
        for item in api_results:
            if isinstance(item[field_name], str):
                field_list.append(item[field_name])
            elif isinstance(item[field_name], list):
                for another_item in item[field_name]:
                    field_list.append(another_item)
        return field_list
