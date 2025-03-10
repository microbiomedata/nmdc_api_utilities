# -*- coding: utf-8 -*-
from nmdc_api_utilities.minter import Minter
import logging
import os
from dotenv import load_dotenv
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")


def test_mint():
    mint = Minter()
    results = mint.mint("nmdc:DataObject", CLIENT_ID, CLIENT_SECRET)
    assert results
    assert "nmdc:dobj" in results