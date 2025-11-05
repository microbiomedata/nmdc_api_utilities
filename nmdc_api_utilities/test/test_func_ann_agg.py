# -*- coding: utf-8 -*-
from nmdc_api_utilities.functional_annotation_agg_search import (
    FunctionalAnnotationAggSearch,
)
import logging
import unittest
import os


class TestFunctionalAnnotation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.env = os.getenv("ENV", "prod")

    def test_func_ann_id(self):
        fannagg = FunctionalAnnotationAggSearch(env=self.env)
        results = fannagg.get_functional_annotations("K01426", "KEGG")
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["gene_function_id"], "KEGG.ORTHOLOGY:K01426")

    def test_func_ann_id_fail(self):
        fannagg = FunctionalAnnotationAggSearch(env=self.env)
        with self.assertRaises(ValueError):
            fannagg.get_functional_annotations("K01426", "nfjbg")

    def test_get_records(self):
        fannagg = FunctionalAnnotationAggSearch(env=self.env)
        results = fannagg.get_records(max_page_size=10)
        self.assertEqual(len(results), 10)
