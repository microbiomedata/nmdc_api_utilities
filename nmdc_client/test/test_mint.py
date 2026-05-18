# -*- coding: utf-8 -*-
import os

import pytest
from dotenv import load_dotenv

from nmdc_client.auth import NMDCAuth
from nmdc_client.config import API_BASE_URL
from nmdc_client.decorators import AuthenticationError
from nmdc_client.minter import Minter

load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")


def test_mint_single():
    """Test minting a single ID (default behavior)."""
    auth = NMDCAuth(
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET, api_base_url=API_BASE_URL
    )
    mint = Minter(api_base_url=API_BASE_URL, auth=auth)
    results = mint.mint("nmdc:DataObject")
    assert results
    assert isinstance(results, str)
    assert "nmdc:dobj" in results


def test_mint_single_explicit():
    """Test minting a single ID with explicit count=1."""
    auth = NMDCAuth(
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET, api_base_url=API_BASE_URL
    )
    mint = Minter(api_base_url=API_BASE_URL, auth=auth)
    results = mint.mint("nmdc:DataObject", count=1)
    assert results
    assert isinstance(results, str)
    assert "nmdc:dobj" in results


def test_mint_multiple():
    """Test minting multiple IDs."""
    auth = NMDCAuth(
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET, api_base_url=API_BASE_URL
    )
    mint = Minter(api_base_url=API_BASE_URL, auth=auth)
    results = mint.mint("nmdc:DataObject", count=3)
    assert results
    assert isinstance(results, list)
    assert len(results) == 3
    for result in results:
        assert isinstance(result, str)
        assert "nmdc:dobj" in result


def test_mint_invalid_count():
    """Test that invalid count values raise ValueError."""
    auth = NMDCAuth(
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET, api_base_url=API_BASE_URL
    )
    mint = Minter(api_base_url=API_BASE_URL, auth=auth)
    with pytest.raises(ValueError, match="count must be at least 1"):
        mint.mint("nmdc:DataObject", count=0)

    with pytest.raises(ValueError, match="count must be at least 1"):
        mint.mint("nmdc:DataObject", count=-1)


def test_mint_no_auth():
    """Test that missing authentication raises AuthenticationError."""
    mint = Minter(api_base_url=API_BASE_URL)
    with pytest.raises(
        AuthenticationError, match="requires authentication"
    ) as exc_info:
        mint.mint("nmdc:DataObject")
    assert exc_info.type is AuthenticationError
    assert "requires authentication" in str(exc_info.value)


def test_old_auth():
    """Test that using client_id and client_secret directly works for authentication."""
    mint = Minter(api_base_url=API_BASE_URL)
    results = mint.mint(
        "nmdc:DataObject", client_id=CLIENT_ID, client_secret=CLIENT_SECRET
    )
    assert results
    assert isinstance(results, str)
    assert "nmdc:dobj" in results
