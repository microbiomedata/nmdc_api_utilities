# -*- coding: utf-8 -*-
import logging
import warnings
from abc import ABC

from nmdc_api_utilities.config import API_BASE_URL, get_api_base_url

logger = logging.getLogger(__name__)


class NMDCAPIClient(ABC):
    """
    Abstract base class for interacting with NMDC runtime API.

    Parameters
    ----------
    api_base_url: str
        The base URL of an instance of the NMDC Runtime API. By default, this is the base URL of
        the production instance. NMDC team members will occasionally set this to the base URL of
        a different instance; for example, a self-hosted instance used for testing.
    """

    def __init__(self, api_base_url: str = API_BASE_URL, env: str = ""):
        if env != "":
            warnings.warn(
                "`env` is deprecated and will be removed in a future release. "
                "Use `api_base_url` instead.",
                DeprecationWarning,
            )
        self.api_base_url = get_api_base_url(api_base_url=api_base_url, env=env)
