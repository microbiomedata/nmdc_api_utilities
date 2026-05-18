# -*- coding: utf-8 -*-
"""
This module contains the definitions of variables used throughout the package.
"""

import os
import re

# Base URL of the production instance of the NMDC Runtime API.
PRODUCTION_API_BASE_URL = "https://api.microbiomedata.org"

# (Deprecated) Base URL of the internal development instance of the NMDC Runtime API.
#
# Caution: This instance undergoes spontaneous changes throughout each release cycle
#          and NMDC development team members discourage its use by anyone not on
#          the NMDC development team. It is here for backwards compatibility with
#          previous versions of this Python package.
#
DEVELOPMENT_API_BASE_URL = "https://api-dev.microbiomedata.org"


def _sanitize_api_base_url(api_base_url: str) -> str:
    if isinstance(api_base_url, str) and re.match(
        r"^https?://", api_base_url, flags=re.IGNORECASE
    ):
        return api_base_url.rstrip("/")
    raise ValueError(f"Invalid API base URL: {api_base_url}")


def get_api_base_url(api_base_url: str = PRODUCTION_API_BASE_URL, env: str = "") -> str:
    """
    Get the base URL of the NMDC Runtime API to use for API requests, based upon the specified
    API base URL and environment nickname (each oftentimes obtained from an environment variable).

    The logic for determining the base URL is as follows:
    1. If `env` is set to "prod", use the production NMDC Runtime API base URL.
    2. If `env` is set to "dev", use the development NMDC Runtime API base URL.
    3. If `api_base_url` is set to anything resembling a URL,
       use that after removing any trailing forward slashes from it.
    4. If `api_base_url` is set to anything else, raise an error.

    Parameters:
        api_base_url: The base URL of an instance of the NMDC Runtime API.
        env: The name of the environment hosting an instance of the NMDC Runtime API.

    Returns:
        str: The base URL of the NMDC Runtime API.

    >>> get_api_base_url()
    'https://api.microbiomedata.org'
    >>> get_api_base_url(env="prod")
    'https://api.microbiomedata.org'
    >>> get_api_base_url(env="dev")
    'https://api-dev.microbiomedata.org'
    >>> get_api_base_url(env="potato")  # neither "prod" nor "dev"
    'https://api.microbiomedata.org'
    >>> get_api_base_url(api_base_url="http://localhost:8000/")  # custom URL
    'http://localhost:8000'
    >>> get_api_base_url(api_base_url="potato")
    Traceback (most recent call last):
        ...
    ValueError: Invalid API base URL: potato
    """

    if env == "prod":
        return PRODUCTION_API_BASE_URL
    elif env == "dev":
        return DEVELOPMENT_API_BASE_URL
    else:
        return _sanitize_api_base_url(api_base_url)


API_BASE_URL = get_api_base_url(
    api_base_url=os.getenv("API_BASE_URL", default=PRODUCTION_API_BASE_URL),
    env=os.getenv("ENV", default=""),
)
