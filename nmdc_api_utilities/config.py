# -*- coding: utf-8 -*-
"""
This module contains the definitions of variables used throughout the package.
"""

import os
import re


# Populate the `API_BASE_URL` configuration variable based upon the `API_BASE_URL` environment
# variable, falling back to the URL of the production instance of the NMDC Runtime API if the
# environment variable is not defined. Also validate that the value resembles a URL. The end
# result is that this module will export a validated `API_BASE_URL` with trailing slashes removed.
PRODUCTION_API_BASE_URL = "https://api.microbiomedata.org"
api_base_url_raw = os.getenv("API_BASE_URL", default=PRODUCTION_API_BASE_URL)
if not isinstance(api_base_url_raw, str) or not re.match(
    r"^https?://", api_base_url_raw
):
    raise ValueError(f"Invalid API_BASE_URL: {api_base_url_raw}")
API_BASE_URL = api_base_url_raw.rstrip(
    "/"
)  # e.g. "http://host:8000/" -> "http://host:8000"
