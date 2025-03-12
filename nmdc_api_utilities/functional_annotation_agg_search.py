# -*- coding: utf-8 -*-
from nmdc_api_utilities.functional_search import FunctionalSearch
import logging

logger = logging.getLogger(__name__)


class FunctionalAnnotationAggSearch(FunctionalSearch):
    """
    Class to interact with the NMDC API to get functional annotation agg sets. These are most helpful when trying identify workflows associted with a KEGG, COG, or PFAM ids.
    """

    def __init__(self, env="prod"):
        super().__init__(env=env)
