# -*- coding: utf-8 -*-
import pandas as pd
import logging
import re
logger = logging.getLogger(__name__)


class DataProcessing:
    def __init__(self):
        pass

    def _string_mongo_list(self, data: list) -> str:
        """
        Convert elements in a list to use double quotes instead of single quotes.
        This is required for mongo queries.
        """
        return str(data).replace("'", '"')

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

    def build_filter(self, attributes, exact_match=False):
        """
        Create a MongoDB filter using $regex for each attribute in the input dictionary. For nested attributes, use dot notation.

        Parameters:
            attributes (dict): Dictionary of attribute names and their corresponding values to match using regex.
                Example: {"name": "example", "description": "example", "geo_loc_name": "example"}
            exact_match: bool
                This var is used to determine if the inputted attribute value is an exact match or a partial match. Default is False, meaning the user does not need to input an exact match.
                Under the hood this is used to determine if the inputted attribute value should be wrapped in a regex expression.
        Returns:
        dict: A MongoDB filter dictionary.
        """
        filter_dict = {}
        if exact_match:
            for attribute_name, attribute_value in attributes.items():
                filter_dict[attribute_name] = attribute_value
        else:
            for attribute_name, attribute_value in attributes.items():
                # escape special characters - mongo db filters require special characters to be double escaped ex. GC\\-MS \\(2009\\)
                escaped_value = re.sub(r'([\W])', r'\\\1', attribute_value)
                logging.debug(f"Escaped value: {escaped_value}")
                logging.debug(f"Attribute name: {attribute_name}")
                filter_dict[attribute_name] = {"$regex": escaped_value,"$options":"i"}
                logging.debug(f"Filter dict: {filter_dict}")
        clean = self._string_mongo_list(filter_dict)
        logging.debug(f"Filter cleaned: {clean}")
        return clean
    
    def extract_field(self, api_results:list, field_name:str) -> list:
        """
        This function is used to extract a field from the API results.
        params:
            api_results: list
                A list of dictionaries.
            field_name: str
                The name of the field to extract.
        returns:
            list: A list of IDs.
        """
        field_list = []
        for item in api_results:
            if type(item[field_name]) == str:
                field_list.append(item[field_name])
            elif type(item[field_name]) == list:
                for another_item in item[field_name]:
                    field_list.append(another_item)
        return field_list
