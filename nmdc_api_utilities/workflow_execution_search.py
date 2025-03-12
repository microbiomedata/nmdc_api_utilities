# -*- coding: utf-8 -*-
from nmdc_api_utilities.collection_search import CollectionSearch
import logging

logger = logging.getLogger(__name__)


class WorkflowExecutionSearch(CollectionSearch):
    """
    Class to interact with the NMDC API to get workflow execution sets.
    """

    def __init__(self, env="prod"):
        super().__init__(collection_name="workflow_execution_set", env=env)
