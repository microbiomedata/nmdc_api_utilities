# -*- coding: utf-8 -*-
"""Pytest configuration and fixtures for nmdc_api_utilities tests."""
import os
import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@pytest.fixture(scope="session")
def env():
    """
    Get the test environment from ENV variable.
    Defaults to 'prod' if not set.
    """
    return os.getenv("ENV", "prod")


@pytest.fixture(scope="session")
def client_id():
    """Get CLIENT_ID from environment."""
    return os.getenv("CLIENT_ID")


@pytest.fixture(scope="session")
def client_secret():
    """Get CLIENT_SECRET from environment."""
    return os.getenv("CLIENT_SECRET")
