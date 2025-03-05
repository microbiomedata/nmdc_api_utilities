# -*- coding: utf-8 -*-
import logging

logger = logging.getLogger(__name__)


class NMDCSearch:
    def __init__(self):
        self.base_url = "https://api.microbiomedata.org"
