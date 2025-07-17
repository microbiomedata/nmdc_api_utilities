# -*- coding: utf-8 -*-
from nmdc_api_utilities.minter import Minter
import logging
import os
from dotenv import load_dotenv
import pytest

load_dotenv()
ENV = os.getenv("ENV")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")


def test_mint_single():
    """Test minting a single ID (default behavior)."""
    mint = Minter(env=ENV)
    results = mint.mint("nmdc:DataObject", CLIENT_ID, CLIENT_SECRET)
    assert results
    assert isinstance(results, str)
    assert "nmdc:dobj" in results


def test_mint_single_explicit():
    """Test minting a single ID with explicit count=1."""
    mint = Minter(env=ENV)
    results = mint.mint("nmdc:DataObject", CLIENT_ID, CLIENT_SECRET, count=1)
    assert results
    assert isinstance(results, str)
    assert "nmdc:dobj" in results


def test_mint_multiple():
    """Test minting multiple IDs."""
    mint = Minter(env=ENV)
    results = mint.mint("nmdc:DataObject", CLIENT_ID, CLIENT_SECRET, count=3)
    assert results
    assert isinstance(results, list)
    assert len(results) == 3
    for result in results:
        assert isinstance(result, str)
        assert "nmdc:dobj" in result


def test_mint_invalid_count():
    """Test that invalid count values raise ValueError."""
    mint = Minter(env=ENV)
    with pytest.raises(ValueError, match="count must be at least 1"):
        mint.mint("nmdc:DataObject", CLIENT_ID, CLIENT_SECRET, count=0)

    with pytest.raises(ValueError, match="count must be at least 1"):
        mint.mint("nmdc:DataObject", CLIENT_ID, CLIENT_SECRET, count=-1)


# Keep the old test name for backward compatibility
def test_mint():
    """Original test for backward compatibility."""
    test_mint_single()
