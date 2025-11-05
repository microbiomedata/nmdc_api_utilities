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
            backup
        When using CLI commands, this can also be set via the NMDC_ENV environment variable.

    Examples
    --------
    >>> from nmdc_api_utilities.nmdc_search import NMDCSearch
    >>> # Production environment (default)
    >>> search_prod = NMDCSearch(env="prod")
    >>> search_prod.base_url
    'https://api.microbiomedata.org'
    >>> # Development environment
    >>> search_dev = NMDCSearch(env="dev")
    >>> search_dev.base_url
    'https://api-dev.microbiomedata.org'
    >>> # Backup environment
    >>> search_backup = NMDCSearch(env="backup")
    >>> search_backup.base_url
    'https://api-backup.microbiomedata.org'

    """

    def __init__(self, env="prod"):
        if env == "prod":
            self.base_url = "https://api.microbiomedata.org"
        elif env == "dev":
            self.base_url = "https://api-dev.microbiomedata.org"
        elif env == "backup":
            self.base_url = "https://api-backup.microbiomedata.org"
        else:
            raise ValueError("env must be one of the following: prod, dev, backup")
