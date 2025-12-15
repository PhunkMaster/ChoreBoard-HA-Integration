"""ChoreBoard API Client with HMAC authentication.

DEVELOPMENT NOTE: The ChoreBoard backend API is available at ../ChoreBoard for local
development and testing. You can modify the ChoreBoard API endpoints as needed to
support this integration. In production, users will configure their own ChoreBoard
backend URL via the integration config flow.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any

import aiohttp
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)


class ChoreboardAPIError(HomeAssistantError):
    """Base exception for ChoreBoard API errors."""


class ChoreboardAuthError(ChoreboardAPIError):
    """Exception for authentication errors."""


class ChoreboardConnectionError(ChoreboardAPIError):
    """Exception for connection errors."""


class ChoreboardAPIClient:
    """Client for interacting with ChoreBoard API."""

    def __init__(
        self,
        base_url: str,
        username: str,
        secret_key: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the API client.

        Args:
            base_url: Base URL of the ChoreBoard instance
            username: ChoreBoard username for authentication
            secret_key: Django SECRET_KEY for HMAC token generation
            session: aiohttp ClientSession for making requests
        """
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.secret_key = secret_key
        self.session = session
        self._cached_token: str | None = None
        self._token_timestamp: float | None = None

    def _generate_token(self) -> str:
        """Generate HMAC-SHA256 authentication token.

        Token format: username:timestamp:signature
        where signature = HMAC-SHA256(username:timestamp, SECRET_KEY)

        Returns:
            Authentication token string
        """
        timestamp = str(int(time.time()))
        message = f"{self.username}:{timestamp}"
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        token = f"{self.username}:{timestamp}:{signature}"
        _LOGGER.debug(
            "Generated token for user %s at timestamp %s", self.username, timestamp
        )
        return token

    def _get_token(self) -> str:
        """Get authentication token, using cached token if valid.

        Tokens are cached and refreshed after 23 hours to avoid expiration.

        Returns:
            Valid authentication token
        """
        current_time = time.time()

        # Check if cached token is still valid (less than 23 hours old)
        if (
            self._cached_token is not None
            and self._token_timestamp is not None
            and (current_time - self._token_timestamp) < (23 * 3600)
        ):
            _LOGGER.debug("Using cached token")
            return self._cached_token

        # Generate new token
        self._cached_token = self._generate_token()
        self._token_timestamp = current_time
        _LOGGER.debug("Generated new token")
        return self._cached_token

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Make an authenticated request to the ChoreBoard API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            json_data: JSON data for request body
            params: Query parameters

        Returns:
            API response data

        Raises:
            ChoreboardAuthError: Authentication failed
            ChoreboardConnectionError: Connection failed
            ChoreboardAPIError: Other API errors
        """
        url = f"{self.base_url}{endpoint}"
        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}

        _LOGGER.debug("Making %s request to %s", method, url)

        try:
            async with self.session.request(
                method,
                url,
                headers=headers,
                json=json_data,
                params=params,
            ) as response:
                if response.status == 401:
                    # Token expired or invalid, clear cache and retry once
                    _LOGGER.warning("Authentication failed, regenerating token")
                    self._cached_token = None
                    self._token_timestamp = None
                    raise ChoreboardAuthError("Authentication failed")

                if response.status == 404:
                    _LOGGER.error("Endpoint not found: %s", url)
                    raise ChoreboardAPIError(f"Endpoint not found: {endpoint}")

                if response.status >= 500:
                    _LOGGER.error("Server error: %s", response.status)
                    raise ChoreboardAPIError(f"Server error: {response.status}")

                response.raise_for_status()

                # Parse response
                data = await response.json()
                _LOGGER.debug("Request successful, received data")
                return data

        except aiohttp.ClientConnectionError as err:
            _LOGGER.error("Connection error: %s", err)
            raise ChoreboardConnectionError(f"Connection failed: {err}") from err
        except aiohttp.ClientError as err:
            _LOGGER.error("Client error: %s", err)
            raise ChoreboardAPIError(f"Request failed: {err}") from err

    async def get_outstanding_chores(self) -> list[dict[str, Any]]:
        """Get all outstanding (incomplete, non-overdue) chores.

        Returns:
            List of chore dictionaries
        """
        data = await self._request("GET", "/api/outstanding/")
        return data if isinstance(data, list) else []

    async def get_late_chores(self) -> list[dict[str, Any]]:
        """Get all overdue chores.

        Returns:
            List of chore dictionaries
        """
        data = await self._request("GET", "/api/late-chores/")
        return data if isinstance(data, list) else []

    async def get_my_chores(self) -> list[dict[str, Any]]:
        """Get chores for the authenticated user.

        Returns:
            List of chore dictionaries
        """
        data = await self._request("GET", "/api/my-chores/")
        return data if isinstance(data, list) else []

    async def get_users(self) -> list[dict[str, Any]]:
        """Get all active, assignable users.

        Returns:
            List of user dictionaries with points and other data
        """
        data = await self._request("GET", "/api/users/")
        return data if isinstance(data, list) else []

    async def get_recent_completions(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent chore completions.

        Args:
            limit: Maximum number of completions to return (default: 10)

        Returns:
            List of completion dictionaries with chore and user data
        """
        params = {"limit": str(limit)}
        data = await self._request("GET", "/api/completions/recent/", params=params)
        return data if isinstance(data, list) else []

    async def get_leaderboard(
        self, leaderboard_type: str = "weekly"
    ) -> list[dict[str, Any]]:
        """Get leaderboard data.

        Args:
            leaderboard_type: "weekly" or "alltime"

        Returns:
            List of user leaderboard entries
        """
        params = {"type": leaderboard_type}
        data = await self._request("GET", "/api/leaderboard/", params=params)
        return data if isinstance(data, list) else []

    async def get_chore_leaderboards(self) -> list[dict[str, Any]]:
        """Get arcade mode leaderboards for all chores.

        Returns:
            List of chore leaderboard dictionaries with high scores
        """
        data = await self._request("GET", "/api/chore-leaderboards/")
        return data if isinstance(data, list) else []

    async def claim_chore(
        self, instance_id: int, assign_to_user_id: int | None = None
    ) -> dict[str, Any]:
        """Claim a pool chore.

        Args:
            instance_id: ID of the chore instance to claim
            assign_to_user_id: Optional user ID to assign the chore to

        Returns:
            Updated chore data
        """
        json_data: dict[str, Any] = {"instance_id": instance_id}
        if assign_to_user_id is not None:
            json_data["assign_to_user_id"] = assign_to_user_id

        data = await self._request("POST", "/api/claim/", json_data=json_data)
        return data if isinstance(data, dict) else {}

    async def complete_chore(
        self,
        instance_id: int,
        helper_ids: list[int] | None = None,
        completed_by_user_id: int | None = None,
    ) -> dict[str, Any]:
        """Mark a chore as complete.

        Args:
            instance_id: ID of the chore instance to complete
            helper_ids: Optional list of helper user IDs
            completed_by_user_id: Optional user ID of who completed the chore

        Returns:
            Updated chore data
        """
        json_data: dict[str, Any] = {"instance_id": instance_id}
        if helper_ids:
            json_data["helper_ids"] = helper_ids
        if completed_by_user_id is not None:
            json_data["completed_by_user_id"] = completed_by_user_id

        data = await self._request("POST", "/api/complete/", json_data=json_data)
        return data if isinstance(data, dict) else {}

    async def undo_completion(self, completion_id: int) -> dict[str, Any]:
        """Undo a chore completion (admin only).

        Args:
            completion_id: ID of the completion to undo

        Returns:
            Updated chore data
        """
        data = await self._request(
            "POST", "/api/undo/", json_data={"completion_id": completion_id}
        )
        return data if isinstance(data, dict) else {}

    async def test_connection(self) -> bool:
        """Test the API connection and authentication.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            await self.get_outstanding_chores()
            return True
        except ChoreboardAPIError:
            return False
