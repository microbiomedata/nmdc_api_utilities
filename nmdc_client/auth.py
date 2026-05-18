# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta
from typing import Any

import requests

from nmdc_client.api_client import NMDCAPIClient
from nmdc_client.config import API_BASE_URL

logger = logging.getLogger(__name__)


class NMDCAuth(NMDCAPIClient):
    """
    Authentication handler for NMDC API operations.

    Parameters
    ----------
    client_id
        The client ID for NMDC API authentication. See Notes for further details.
    client_secret
        The client secret for NMDC API authentication. See Notes for further details.
    username
        The username for NMDC API authentication. See Notes for further details.
    password
        The password for NMDC API authentication. See Notes for further details.
    api_base_url
        The base URL of an instance of the NMDC Runtime API. By default, this is the base URL of
        the production instance.
    env
        Deprecated. Use `api_base_url` instead. Previously used to specify the API environment
        (e.g., "prod", "dev").

    Notes
    -----
    Security Warning - your credentials should be stored in a secure location. Do not hard-code these values in your code; we recommend using environment variables.

    You must provide either:

    - ``client_id`` and ``client_secret`` (for client credentials grant), OR
    - ``username`` and ``password`` (for password grant).


    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        username: str | None = None,
        password: str | None = None,
        api_base_url: str = API_BASE_URL,
        env: str = "",
    ):
        super().__init__(
            api_base_url=api_base_url,
            env=env,
        )
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self._token: str | None = None
        self._token_expires_at: datetime | None = None
        self._oauth_session: Any | None = None
        self.grant_type: str | None = (
            "client_credentials"
            if (self.client_id and self.client_secret)
            else "password"
            if (self.username and self.password)
            else None
        )

    def has_credentials(self) -> bool:
        """Check if the credentials are passed in properly."""
        if self.client_id and self.client_secret:
            return True
        elif self.username and self.password:
            return True
        return False

    def get_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        if self._is_token_valid():
            assert isinstance(self._token, str)  # to appease mypy
            return self._token
        return self._refresh_token()

    def _is_token_valid(self) -> bool:
        """Check if current token is valid and not expired."""
        if not self._token or not self._token_expires_at:
            return False
        return datetime.now() < self._token_expires_at

    def _refresh_token(self) -> str:
        """Refresh the access token."""
        if self.grant_type == "client_credentials":
            token_request_body = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
        elif self.grant_type == "password":
            token_request_body = {
                "grant_type": "password",
                "username": self.username,
                "password": self.password,
            }
        else:
            raise ValueError(
                "Refreshing a token requires that credentials be specified."
            )

        response = requests.post(
            f"{self.api_base_url}/token",
            headers=self._build_http_request_headers(),
            data=token_request_body,
        )
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
        assert isinstance(self._token, str)  # to appease mypy
        return self._token
