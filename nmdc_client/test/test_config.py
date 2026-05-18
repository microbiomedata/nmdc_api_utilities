# -*- coding: utf-8 -*-
import importlib

import pytest

import nmdc_client.config as config_module


def test_api_base_url_variable_defaults_to_production_api_base_url():
    with pytest.MonkeyPatch.context() as monkeypatch:
        # Unset both environment variables.
        monkeypatch.delenv("API_BASE_URL", raising=False)
        monkeypatch.delenv("ENV", raising=False)
        config = importlib.reload(config_module)

        assert config.API_BASE_URL == "https://api.microbiomedata.org"

    importlib.reload(config_module)


def test_api_base_url_variable_has_value_of_api_base_url_environment_variable():
    with pytest.MonkeyPatch.context() as monkeypatch:
        # Set only `API_BASE_URL`.
        monkeypatch.setenv("API_BASE_URL", "https://localhost:8000")
        monkeypatch.delenv("ENV", raising=False)
        config = importlib.reload(config_module)

        assert config.API_BASE_URL == "https://localhost:8000"

    importlib.reload(config_module)


def test_api_base_url_env_environment_variable_overrides_api_base_url_environment_variable():
    with pytest.MonkeyPatch.context() as monkeypatch:
        # Set both environment variables (`env="dev"`).
        monkeypatch.setenv("API_BASE_URL", "https://localhost:8000")
        monkeypatch.setenv("ENV", "dev")
        config = importlib.reload(config_module)

        assert config.API_BASE_URL == "https://api-dev.microbiomedata.org"

        # Set both environment variables (`env="prod"`).
        monkeypatch.setenv("API_BASE_URL", "https://localhost:8000")
        monkeypatch.setenv("ENV", "prod")
        config = importlib.reload(config_module)

        assert config.API_BASE_URL == "https://api.microbiomedata.org"

    importlib.reload(config_module)
