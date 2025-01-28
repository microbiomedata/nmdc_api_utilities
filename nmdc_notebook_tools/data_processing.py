# -*- coding: utf-8 -*-
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class DataProcessing:
    def __init__(self):
        pass

    def convert_to_df(self, data: list) -> pd.DataFrame:
        """
        Convert a list of dictionaries to a pandas dataframe.
        params:
            data: list
                A list of dictionaries.
        """
        return pd.DataFrame(data)

    def rename_columns(self, df: pd.DataFrame, new_col_names: list) -> pd.DataFrame:
        """
        Rename columns in a pandas dataframe.
        params:
            df: pd.DataFrame
                The pandas dataframe to rename columns.
            new_col_names: list
                A list of new column names. Names MUST be in order of the columns in the dataframe.\n
                Example:
                    If the current column names are - ['old_col1', 'old_col2', 'old_col3']
                    You will need to pass in the new names like - ['new_col1', 'new_col2', 'new_col3']
        """
        df.columns = new_col_names
        return df

    def merge_dataframes(
        self, column: str, df1: pd.DataFrame, df2: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Merge two dataframes.
        params:
            column: str
                The column to merge on.
            df1: pd.DataFrame
                The first dataframe to merge.
            df2: pd.DataFrame
                The second dataframe to merge.
        returns:
            pd.DataFrame
        """
        return pd.merge(df1, df2, on=column, how="inner")

    def merge_df(
        self,
        df1,
        df2,
        key1: str,
        key2: str,
    ):
        """
        Define a merging function to join results
        This function merges new results with the previous results that were used for the new API request. It uses two keys from each result to match on.
        params:
            df1 and df2 are the two dataframes that need to be merged.
            key1 is the column name in df1 that will be used to match with `key2` in `df2`.

        This function automatically identifies columns that need to be exploded because they contain list-like elements, as drop_duplicates can't handle list elements.
        """

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

    def build_filter(self, attributes):
        """
        Create a MongoDB filter using $regex for each attribute in the input dictionary. For nested attributes, use dot notation.

        Parameters:
        attributes (dict): Dictionary of attribute names and their corresponding values to match using regex.
            Example: {"name": "example", "description": "example", "geo_loc_name": "example"}
        Returns:
        dict: A MongoDB filter dictionary.
        """
        filter_dict = {}
        for attribute_name, attribute_value in attributes.items():
            filter_dict[attribute_name] = {"$regex": attribute_value}
        return self.string_mongo_list(filter_dict)
