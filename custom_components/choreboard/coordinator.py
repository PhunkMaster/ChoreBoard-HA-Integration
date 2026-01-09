"""DataUpdateCoordinator for ChoreBoard integration.

DEVELOPMENT NOTE: The ChoreBoard backend API is available at ../ChoreBoard for local
development and testing. You can modify the ChoreBoard API endpoints as needed to
support this integration. In production, users will configure their own ChoreBoard
backend URL via the integration config flow.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import homeassistant.util.dt as dt_util
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api_client import ChoreboardAPIClient, ChoreboardAPIError
from .const import (
    CONF_MONITORED_USERS,
    CONF_SCAN_INTERVAL,
    CONF_SECRET_KEY,
    CONF_URL,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ChoreboardCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching ChoreBoard data from the API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.api_client = ChoreboardAPIClient(
            base_url=entry.data[CONF_URL],
            username=entry.data[CONF_USERNAME],
            secret_key=entry.data[CONF_SECRET_KEY],
            session=async_get_clientsession(hass),
        )

        # Get monitored users from options (if set) or fall back to data
        self.monitored_users: list[str] = entry.options.get(
            CONF_MONITORED_USERS, entry.data.get(CONF_MONITORED_USERS, [])
        )

        # Handle case where monitored_users might be a comma-separated string
        if isinstance(self.monitored_users, str):
            self.monitored_users = [u.strip() for u in self.monitored_users.split(",")]

        # Get scan interval from options or data (in seconds), convert to timedelta
        scan_interval_seconds = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval_seconds),
        )

    async def async_refresh_immediately(self) -> None:
        """Trigger immediate data refresh after user action.

        This bypasses the normal update interval to provide
        instant feedback after service calls (claim, complete, undo).
        """
        await self.async_request_refresh()

    @staticmethod
    def _is_due_today(due_at_str: str | None) -> bool:
        """Check if a chore is due by today at 23:59:59.

        Args:
            due_at_str: ISO 8601 datetime string (e.g., "2025-12-15T10:00:00Z")

        Returns:
            True if the chore is due by end of today, False otherwise
        """
        if not due_at_str:
            return False

        try:
            # Parse the due date string
            due_date = dt_util.parse_datetime(due_at_str)
            if not due_date:
                return False

            # Get end of today (23:59:59) in local timezone
            now = dt_util.now()
            end_of_today = now.replace(
                hour=23, minute=59, second=59, microsecond=999999
            )

            # Compare
            return due_date <= end_of_today

        except (ValueError, TypeError) as err:
            _LOGGER.debug("Failed to parse due_at '%s': %s", due_at_str, err)
            return False

    @staticmethod
    def _normalize_datetime(dt_str: str | None) -> str | None:
        """Normalize datetime string to YYYY-MM-DD HH:MM format (no seconds).

        Args:
            dt_str: ISO 8601 datetime string

        Returns:
            Formatted datetime string without seconds, or None if parsing fails
        """
        if not dt_str:
            return None

        try:
            dt_obj = dt_util.parse_datetime(dt_str)
            if not dt_obj:
                return None

            # Convert to local timezone
            dt_local = dt_util.as_local(dt_obj)

            # Format without seconds
            return dt_local.strftime("%Y-%m-%d %H:%M")

        except (ValueError, TypeError) as err:
            _LOGGER.debug("Failed to normalize datetime '%s': %s", dt_str, err)
            return dt_str

    def _filter_chores_by_due_date(
        self, chores: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Filter chores to only include those due by today at 23:59.

        Also normalizes datetime fields to remove seconds/microseconds.

        Args:
            chores: List of chore dictionaries

        Returns:
            Filtered list of chores due by today
        """
        filtered = []
        for chore in chores:
            # Check if chore is due by today
            if self._is_due_today(chore.get("due_at")):
                # Normalize datetime fields
                if "due_at" in chore:
                    chore["due_at"] = self._normalize_datetime(chore["due_at"])
                if "completed_at" in chore:
                    chore["completed_at"] = self._normalize_datetime(
                        chore["completed_at"]
                    )

                filtered.append(chore)

        return filtered

    async def _async_update_data(self) -> dict[str, Any]:  # noqa: C901
        """Fetch data from ChoreBoard API.

        Returns a dictionary with the following structure:
        {
            "outstanding_chores": [...],  # List of all outstanding chores
            "late_chores": [...],          # List of all overdue chores
            "pool_chores": [...],          # List of unassigned pool chores
            "users": [...],                # List of all users with points data
            "points_label": "points",      # Custom points label from site settings
            "recent_completions": [...],   # Recent completion history
            "chore_leaderboards": [...],   # Arcade mode leaderboards for chores
            "leaderboard_weekly": [...],   # Weekly leaderboard data
            "leaderboard_alltime": [...],  # All-time leaderboard data
            "my_chores": {                 # Per-user chore data
                "username1": [...],
                "username2": [...],
            },
            "arcade_sessions": {           # Active arcade sessions per user
                "username1": {...},        # Session object if active, omitted if none
                "username2": {...},
            }
        }
        """
        try:
            _LOGGER.debug("Fetching data from ChoreBoard API")

            # Fetch system-wide data (parallel requests)
            outstanding_chores_raw = await self.api_client.get_outstanding_chores()
            late_chores_raw = await self.api_client.get_late_chores()
            users = await self.api_client.get_users()
            settings = await self.api_client.get_settings()
            recent_completions = await self.api_client.get_recent_completions(limit=20)
            chore_leaderboards = await self.api_client.get_chore_leaderboards()
            leaderboard_weekly = await self.api_client.get_leaderboard("weekly")
            leaderboard_alltime = await self.api_client.get_leaderboard("alltime")

            # Filter chores to only include those due by today at 23:59
            outstanding_chores = self._filter_chores_by_due_date(outstanding_chores_raw)
            late_chores = self._filter_chores_by_due_date(late_chores_raw)

            # Extract pool chores (unassigned chores available for claiming)
            pool_chores = [
                chore
                for chore in outstanding_chores
                if chore.get("status") == "POOL"
                or (
                    chore.get("chore", {}).get("is_pool", False)
                    and not chore.get("assigned_to")
                )
            ]

            # Fetch per-user data by filtering outstanding/late chores
            my_chores_data = {}

            if self.monitored_users:
                for username in self.monitored_users:
                    # Filter chores assigned to this user
                    user_chores = []

                    # Check outstanding chores
                    for chore in outstanding_chores:
                        assigned_to = chore.get("assigned_to", {})
                        if isinstance(assigned_to, dict):
                            assigned_username = assigned_to.get("username", "")
                        else:
                            assigned_username = str(assigned_to)

                        if assigned_username == username:
                            user_chores.append(chore)

                    # Check late chores
                    for chore in late_chores:
                        assigned_to = chore.get("assigned_to", {})
                        if isinstance(assigned_to, dict):
                            assigned_username = assigned_to.get("username", "")
                        else:
                            assigned_username = str(assigned_to)

                        if assigned_username == username:
                            # Avoid duplicates if a chore is both outstanding and late
                            if not any(
                                c.get("id") == chore.get("id") for c in user_chores
                            ):
                                user_chores.append(chore)

                    my_chores_data[username] = user_chores

            # Fetch arcade session status for each monitored user
            arcade_sessions = {}
            if self.monitored_users:
                for username in self.monitored_users:
                    # Find user ID by username
                    user = next((u for u in users if u.get("username") == username), None)
                    if user:
                        user_id = user.get("id")
                        if user_id:
                            try:
                                arcade_status = await self.api_client.get_arcade_status(user_id)
                                if arcade_status.get("has_active_session"):
                                    # Backend returns session data at top level, not nested
                                    arcade_sessions[username] = {
                                        "id": arcade_status.get("session_id"),
                                        "chore_id": arcade_status.get("instance_id"),
                                        "chore_name": arcade_status.get("chore_name"),
                                        "user_id": user_id,
                                        "user_name": username,
                                        "start_time": arcade_status.get("started_at"),
                                        "elapsed_seconds": arcade_status.get("elapsed_seconds", 0),
                                        "status": arcade_status.get("status", "active"),
                                    }
                            except ChoreboardAPIError as err:
                                _LOGGER.debug("Failed to fetch arcade status for %s: %s", username, err)
                                # Don't fail the entire update if arcade status fails

            data = {
                "outstanding_chores": outstanding_chores,
                "late_chores": late_chores,
                "pool_chores": pool_chores,
                "users": users,
                "points_label": settings.get("points_label", "points"),
                "recent_completions": recent_completions,
                "chore_leaderboards": chore_leaderboards,
                "leaderboard_weekly": leaderboard_weekly,
                "leaderboard_alltime": leaderboard_alltime,
                "my_chores": my_chores_data,
                "arcade_sessions": arcade_sessions,
            }

            _LOGGER.debug(
                "Successfully fetched data: %d outstanding, %d late, %d pool, %d users, %d completions, %d chore leaderboards, %d monitored",
                len(outstanding_chores),
                len(late_chores),
                len(pool_chores),
                len(users),
                len(recent_completions),
                len(chore_leaderboards),
                len(self.monitored_users),
            )

            return data

        except ChoreboardAPIError as err:
            _LOGGER.error("Error fetching data from ChoreBoard API: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error fetching data: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err
