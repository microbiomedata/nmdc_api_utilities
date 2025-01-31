# -*- coding: utf-8 -*-
from nmdc_notebook_tools.functional_annotation_agg_search import (
    FunctionalAnnotationAggSearch,
)
import logging
import unittest
from nmdc_notebook_tools.utils import Utils


class TestFunctionalAnnotation(unittest.TestCase):
    def test_func_ann_id(self):
        fannagg = FunctionalAnnotationAggSearch()
        results = fannagg.get_functional_annotation_id("K01426", "KEGG")
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["gene_function_id"], "KEGG.ORTHOLOGY:K01426")

    def test_func_ann_id_fail(self):
        fannagg = FunctionalAnnotationAggSearch()
        with self.assertRaises(ValueError):
            fannagg.get_functional_annotation_id("K01426", "nfjbg")
