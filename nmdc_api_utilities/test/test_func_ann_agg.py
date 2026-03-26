# -*- coding: utf-8 -*-
from nmdc_api_utilities.constants import DEFAULT_API_BASE_URL
from nmdc_api_utilities.functional_annotation_agg_search import (
    FunctionalAnnotationAggSearch,
)
import logging
import unittest
from dotenv import load_dotenv
import os

load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL)


class TestFunctionalAnnotation(unittest.TestCase):
    def test_func_ann_id(self):
        fannagg = FunctionalAnnotationAggSearch(api_base_url=API_BASE_URL)
        results = fannagg.get_functional_annotations("K01426", "KEGG")
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["gene_function_id"], "KEGG.ORTHOLOGY:K01426")

    def test_func_ann_id_fail(self):
        fannagg = FunctionalAnnotationAggSearch(api_base_url=API_BASE_URL)
        with self.assertRaises(ValueError):
            fannagg.get_functional_annotations("K01426", "nfjbg")

    def test_get_records(self):
        fannagg = FunctionalAnnotationAggSearch(api_base_url=API_BASE_URL)
        results = fannagg.get_records(max_page_size=10)
        self.assertEqual(len(results), 10)
