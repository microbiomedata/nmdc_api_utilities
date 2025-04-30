# -*- coding: utf-8 -*-
import logging

logger = logging.getLogger(__name__)


class NMDCSearch:
    """
    Base class for interacting with the NMDC API. Sets the base URL for the API based on the environment.
    Environment is defaulted to the production isntance of the API. This functionality is in place for monthly testing of the runtime updates to the API.

    Parameters
    ----------
    env: str
        The environment to use. Default is prod. Must be one of the following:
            prod
            dev

    """

    def __init__(self, env="prod"):
        if env == "prod":
            self.base_url = "https://api.microbiomedata.org"
        elif env == "dev":
            self.base_url = "https://api-dev.microbiomedata.org"
        else:
            raise ValueError("env must be one of the following: prod, dev")
