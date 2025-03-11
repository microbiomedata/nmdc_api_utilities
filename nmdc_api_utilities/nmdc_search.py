# -*- coding: utf-8 -*-
import logging

logger = logging.getLogger(__name__)


class NMDCSearch:
    def __init__(self, env="Production"):
        if env == "Production":
            self.base_url = "https://api.microbiomedata.org"
        elif env == "Development":
            self.base_url = "https://api-dev.microbiomedata.org"
