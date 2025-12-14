"""Config flow for ChoreBoard integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api_client import (
    ChoreboardAPIClient,
    ChoreboardAPIError,
    ChoreboardAuthError,
    ChoreboardConnectionError,
)
from .const import (
    CONF_MONITORED_USERS,
    CONF_SECRET_KEY,
    CONF_URL,
    CONF_USERNAME,
    DEFAULT_NAME,
    DEFAULT_URL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ChoreboardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Handle a config flow for ChoreBoard."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._username: str | None = None
        self._secret_key: str | None = None
        self._url: str | None = None
        self._available_users: list[dict[str, str]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - collect credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Store credentials temporarily
            self._username = user_input[CONF_USERNAME]
            self._secret_key = user_input[CONF_SECRET_KEY]
            self._url = user_input.get(CONF_URL, DEFAULT_URL)

            # Validate credentials
            try:
                session = async_get_clientsession(self.hass)
                api_client = ChoreboardAPIClient(
                    self._url,
                    self._username,
                    self._secret_key,
                    session,
                )

                # Test connection
                is_valid = await api_client.test_connection()
                if not is_valid:
                    errors["base"] = "invalid_auth"
                else:
                    # Fetch available users from leaderboard
                    try:
                        leaderboard = await api_client.get_leaderboard("alltime")
                        self._available_users = []
                        for entry in leaderboard:
                            user_data = entry.get("user", entry)
                            username = user_data.get("username", "")
                            display_name = user_data.get("display_name", username)
                            if username:
                                self._available_users.append(
                                    {"username": username, "display_name": display_name}
                                )

                        if not self._available_users:
                            # If no leaderboard data, try to get from my_chores
                            my_chores = await api_client.get_my_chores()
                            if my_chores:
                                # Extract unique users from chores
                                users_set = set()
                                for chore in my_chores:
                                    if assigned_to := chore.get("assigned_to"):
                                        if isinstance(assigned_to, dict):
                                            username = assigned_to.get("username", "")
                                            display_name = assigned_to.get(
                                                "display_name", username
                                            )
                                        else:
                                            username = assigned_to
                                            display_name = assigned_to

                                        if username:
                                            users_set.add((username, display_name))

                                self._available_users = [
                                    {"username": u, "display_name": d}
                                    for u, d in sorted(users_set)
                                ]

                    except ChoreboardAPIError as err:
                        _LOGGER.warning("Could not fetch user list: %s", err)
                        # Continue anyway - user can enter manually
                        self._available_users = []

                    # Move to user selection step
                    return await self.async_step_select_users()

            except ChoreboardAuthError:
                errors["base"] = "invalid_auth"
            except ChoreboardConnectionError:
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.exception("Unexpected error validating credentials: %s", err)
                errors["base"] = "unknown"

        # Show credential form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_SECRET_KEY): cv.string,
                vol.Optional(CONF_URL, default=DEFAULT_URL): cv.string,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "url_example": "http://localhost:8000 or https://choreboard.example.com"
            },
        )

    async def async_step_select_users(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle user selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            monitored_users = user_input.get(CONF_MONITORED_USERS, [])

            # Handle case where it might be a string (manual entry fallback)
            if isinstance(monitored_users, str):
                monitored_users = [
                    u.strip() for u in monitored_users.split(",") if u.strip()
                ]

            if not monitored_users:
                errors["base"] = "no_users_selected"
            else:
                # Create unique ID based on URL and username
                await self.async_set_unique_id(f"{self._url}_{self._username}")
                self._abort_if_unique_id_configured()

                # Create config entry
                return self.async_create_entry(
                    title=f"{DEFAULT_NAME} ({self._username})",
                    data={
                        CONF_USERNAME: self._username,
                        CONF_SECRET_KEY: self._secret_key,
                        CONF_URL: self._url,
                        CONF_MONITORED_USERS: monitored_users,
                    },
                )

        # Build user selection schema
        if self._available_users:
            # Create a multi-select with available users
            user_options = {
                user["username"]: f"{user['display_name']} ({user['username']})"
                for user in self._available_users
            }

            data_schema = vol.Schema(
                {
                    vol.Required(CONF_MONITORED_USERS): cv.multi_select(user_options),
                }
            )
        else:
            # Fallback: allow manual entry if we couldn't fetch users
            data_schema = vol.Schema(
                {
                    vol.Required(CONF_MONITORED_USERS): cv.string,
                }
            )

        return self.async_show_form(
            step_id="select_users",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "info": "Select which ChoreBoard users to monitor. A 'My Chores' sensor will be created for each selected user."
            },
        )
