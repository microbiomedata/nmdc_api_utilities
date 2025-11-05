# -*- coding: utf-8 -*-
from nmdc_api_utilities.minter import Minter
from nmdc_api_utilities.auth import NMDCAuth
import os
import pytest
from nmdc_api_utilities.decorators import AuthenticationError

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")


def test_mint_single(env):
    """Test minting a single ID (default behavior)."""
    auth = NMDCAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    mint = Minter(env=env, auth=auth)
    results = mint.mint("nmdc:DataObject")
    assert results
    assert isinstance(results, str)
    assert "nmdc:dobj" in results


def test_mint_single_explicit(env):
    """Test minting a single ID with explicit count=1."""
    auth = NMDCAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    mint = Minter(env=env, auth=auth)
    results = mint.mint("nmdc:DataObject", count=1)
    assert results
    assert isinstance(results, str)
    assert "nmdc:dobj" in results


def test_mint_multiple(env):
    """Test minting multiple IDs."""
    auth = NMDCAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    mint = Minter(env=env, auth=auth)
    results = mint.mint("nmdc:DataObject", count=3)
    assert results
    assert isinstance(results, list)
    assert len(results) == 3
    for result in results:
        assert isinstance(result, str)
        assert "nmdc:dobj" in result


def test_mint_invalid_count(env):
    """Test that invalid count values raise ValueError."""
    auth = NMDCAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    mint = Minter(env=env, auth=auth)
    with pytest.raises(ValueError, match="count must be at least 1"):
        mint.mint("nmdc:DataObject", count=0)

    with pytest.raises(ValueError, match="count must be at least 1"):
        mint.mint("nmdc:DataObject", count=-1)


def test_mint_no_auth(env):
    """Test that missing authentication raises AuthenticationError."""
    mint = Minter(env=env)
    with pytest.raises(
        AuthenticationError, match="requires authentication"
    ) as exc_info:
        mint.mint("nmdc:DataObject")
    assert exc_info.type is AuthenticationError
    assert "requires authentication" in str(exc_info.value)


def test_old_auth(env):
    """Test that using client_id and client_secret directly works for authentication."""
    mint = Minter(env=env)
    results = mint.mint(
        "nmdc:DataObject", client_id=CLIENT_ID, client_secret=CLIENT_SECRET
    )
    assert results
    assert isinstance(results, str)
    assert "nmdc:dobj" in results
