"""DataUpdateCoordinator for ChoreBoard integration.

DEVELOPMENT NOTE: The ChoreBoard backend API is available at ../ChoreBoard for local
development and testing. You can modify the ChoreBoard API endpoints as needed to
support this integration. In production, users will configure their own ChoreBoard
backend URL via the integration config flow.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api_client import ChoreboardAPIClient, ChoreboardAPIError
from .const import (
    CONF_MONITORED_USERS,
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
        self.monitored_users: list[str] = entry.data.get(CONF_MONITORED_USERS, [])

        # Handle case where monitored_users might be a comma-separated string
        if isinstance(self.monitored_users, str):
            self.monitored_users = [u.strip() for u in self.monitored_users.split(",")]

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from ChoreBoard API.

        Returns a dictionary with the following structure:
        {
            "outstanding_chores": [...],  # List of all outstanding chores
            "late_chores": [...],          # List of all overdue chores
            "leaderboard_weekly": [...],   # Weekly leaderboard data
            "leaderboard_alltime": [...],  # All-time leaderboard data
            "my_chores": {                 # Per-user chore data
                "username1": [...],
                "username2": [...],
            }
        }
        """
        try:
            _LOGGER.debug("Fetching data from ChoreBoard API")

            # Fetch system-wide data (parallel requests)
            outstanding_chores = await self.api_client.get_outstanding_chores()
            late_chores = await self.api_client.get_late_chores()
            leaderboard_weekly = await self.api_client.get_leaderboard("weekly")
            leaderboard_alltime = await self.api_client.get_leaderboard("alltime")

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

            data = {
                "outstanding_chores": outstanding_chores,
                "late_chores": late_chores,
                "leaderboard_weekly": leaderboard_weekly,
                "leaderboard_alltime": leaderboard_alltime,
                "my_chores": my_chores_data,
            }

            _LOGGER.debug(
                "Successfully fetched data: %d outstanding, %d late, %d users monitored",
                len(outstanding_chores),
                len(late_chores),
                len(self.monitored_users),
            )

            return data

        except ChoreboardAPIError as err:
            _LOGGER.error("Error fetching data from ChoreBoard API: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error fetching data: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err
