# -*- coding: utf-8 -*-
"""
This module contains the definitions of variables used throughout the package.
"""

import os
import re


# Populate the `API_BASE_URL` configuration variable based upon the `API_BASE_URL` environment
# variable, falling back to the URL of the production instance of the NMDC Runtime API if the
# environment variable is not defined. Also validate that the value resembles a URL. The end
# result is that this module will export a validated `API_BASE_URL`.
PRODUCTION_API_BASE_URL = "https://api.microbiomedata.org"
API_BASE_URL = os.getenv("API_BASE_URL", PRODUCTION_API_BASE_URL)
if not isinstance(API_BASE_URL, str) or not re.match(r"^https?://", API_BASE_URL):
    raise ValueError(f"Invalid API_BASE_URL: {API_BASE_URL}")
