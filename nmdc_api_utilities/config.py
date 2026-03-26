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
_DEVELOPMENT_API_BASE_URL = "https://api-dev.microbiomedata.org"

# (Deprecated) Consider the value of the `ENV` environment variable, whose valid values
#              are "prod" and "dev".
env_raw = os.getenv("ENV", default="prod")

# Derive an `api_base_url` value from the `API_BASE_URL` environment variable.
# Note: The `API_BASE_URL` is the successor to the deprecated `ENV` environment variable.
api_base_url_raw = os.getenv("API_BASE_URL", default=PRODUCTION_API_BASE_URL)
if not isinstance(api_base_url_raw, str) or not re.match(r"^https?://", api_base_url_raw):
    raise ValueError(f"Invalid API_BASE_URL: {api_base_url_raw}")
api_base_url = api_base_url_raw.rstrip("/")

# The `API_BASE_URL` environment variable allows users to specify any URL for the
# NMDC Runtime API, whereas the `ENV` environment variable only allows users to select
# between the production and development instances. The logic below prioritizes the `ENV`
# environment variable for backwards compatibility.
API_BASE_URL = PRODUCTION_API_BASE_URL if env_raw == "prod" else \
    _DEVELOPMENT_API_BASE_URL if env_raw == "dev" else \
    api_base_url
