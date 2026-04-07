# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

import pytest

from nmdc_api_utilities.auth import NMDCAuth
from nmdc_api_utilities.data_staging import JGISequencingProjectAPI
from nmdc_api_utilities.nmdc_search import NMDCSearch


def test_legacy_env_kwarg_is_supported_with_warning():
    with pytest.warns(DeprecationWarning, match="`env` is deprecated"):
        client = NMDCSearch(env="dev")

    assert client.api_base_url == "https://api-dev.microbiomedata.org"


def test_env_takes_priority_over_api_base_url():
    with pytest.warns(DeprecationWarning, match="`env` is deprecated"):
        client = NMDCSearch(api_base_url="http://localhost:8000/", env="dev")

    assert client.api_base_url == "https://api-dev.microbiomedata.org"


def test_api_base_url_is_used_when_env_is_not_provided():
    client = NMDCSearch(api_base_url="http://localhost:8000/")

    assert client.api_base_url == "http://localhost:8000"


def test_auth_accepts_legacy_env_kwarg():
    with pytest.warns(DeprecationWarning, match="`env` is deprecated"):
        auth = NMDCAuth(client_id="client", client_secret="secret", env="dev")

    assert auth.api_base_url == "https://api-dev.microbiomedata.org"


def test_staging_client_accepts_legacy_env_kwarg():
    auth = MagicMock()
    auth.api_base_url = "https://api-dev.microbiomedata.org"
    auth.has_credentials.return_value = True

    with pytest.warns(DeprecationWarning, match="`env` is deprecated"):
        client = JGISequencingProjectAPI(auth=auth, env="dev")

    assert client.api_base_url == auth.api_base_url
