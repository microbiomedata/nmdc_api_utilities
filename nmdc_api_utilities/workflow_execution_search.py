# -*- coding: utf-8 -*-
from nmdc_api_utilities.collection_search import CollectionSearch
import logging

logger = logging.getLogger(__name__)


class WorkflowExecutionSearch(CollectionSearch):
    """
    Class to interact with the NMDC API to get workflow execution sets.
    """

    def __init__(self):
        super().__init__("workflow_execution_set")
