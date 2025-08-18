# -*- coding: utf-8 -*-
import requests
from datetime import datetime, timedelta
from nmdc_api_utilities.nmdc_search import NMDCSearch
import logging

logger = logging.getLogger(__name__)


class NMDCAuth(NMDCSearch):
    """
    Authentication handler for NMDC API operations.
    Manages OAuth2 client credentials flow with token caching and refresh.
    """

    def __init__(self, client_id: str, client_secret: str, env: str = "prod"):
        super().__init__(env=env)
        self.client_id = client_id
        self.client_secret = client_secret
        self._token = None
        self._token_expires_at = None
        self._oauth_session = None

    def get_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        if self._is_token_valid():
            return self._token
        return self._refresh_token()

    def _is_token_valid(self) -> bool:
        """Check if current token is valid and not expired."""
        if not self._token or not self._token_expires_at:
            return False
        return datetime.now() < self._token_expires_at

    def _refresh_token(self) -> str:
        """Refresh the access token."""
        token_request_body = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        response = requests.post(f"{self.base_url}/token", data=token_request_body)
        token_response = response.json()

        if "access_token" not in token_response:
            logger.error(
                f"Token refresh failed: {token_response}, Status: {response.status_code}"
            )
            raise Exception(f"Token refresh failed: {token_response}")

        self._token = token_response["access_token"]
        # Handle expiry format
        expires_info = token_response.get("expires")
        if expires_info:
            days = expires_info.get("days", 0)
            hours = expires_info.get("hours", 0)
            minutes = expires_info.get("minutes", 0)
            expires_delta = timedelta(days=days, hours=hours, minutes=minutes)
            # Subtract 60s buffer
            self._token_expires_at = (
                datetime.now() + expires_delta - timedelta(seconds=60)
            )
        return self._token
