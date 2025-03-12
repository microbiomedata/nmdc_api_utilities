# -*- coding: utf-8 -*-
import logging
from nmdc_api_utilities.collection_search import CollectionSearch

logger = logging.getLogger(__name__)


class StudySearch(CollectionSearch):
    """
    Class to interact with the NMDC API to get studies.
    """

    def __init__(self, env="prod"):
        super().__init__(collection_name="study_set", env=env)
