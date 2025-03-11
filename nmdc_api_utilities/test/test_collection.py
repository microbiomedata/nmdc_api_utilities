# -*- coding: utf-8 -*-
from nmdc_api_utilities.collection_search import CollectionSearch
import unittest

from dotenv import load_dotenv
import os
load_dotenv()
ENV = os.getenv("ENV")
class TestCollection(unittest.TestCase):
    """
    A class to test each endpoint in the CollectionSearch class.
    """
    def test_get_records(self):
        # simple test to check if the get_records method returns a list of records
        collection = CollectionSearch("study_set", env=ENV)
        results = collection.get_records(max_page_size=10)
        assert len(results) == 10


    def test_get_record_by_filter(self):
        # simple test to check if the get_record_by_filter method returns a record
        collection = CollectionSearch("study_set", env=ENV)
        results = collection.get_record_by_filter(filter='{"id": "nmdc:sty-11-8fb6t785"}')
        assert results[0]["id"] == "nmdc:sty-11-8fb6t785"
        assert len(results) == 1
    
    def test_get_record_by_attribute(self):
        # simple test to check if the get_record_by_attribute method returns a record
        collection = CollectionSearch("study_set", env=ENV)
        results = collection.get_record_by_attribute("name", "Lab enrichment of tropical soil microbial communities from Luquillo Experimental Forest, Puerto Rico")
        assert len(results) == 1
    
    def test_get_record_by_id(self):
        # simple test to check if the get_record_by_id method returns a record
        collection = CollectionSearch("study_set", env=ENV)
        results = collection.get_record_by_id("nmdc:sty-11-8fb6t785")
        assert results["id"] == "nmdc:sty-11-8fb6t785"
    
    def test_check_ids_exist(self):
        # simple test to check if the check_ids_exist method returns a boolean
        collection = CollectionSearch("study_set",env=ENV)
        results = collection.check_ids_exist(["nmdc:sty-11-8fb6t785"])
        assert results == True