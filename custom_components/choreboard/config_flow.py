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

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return ChoreboardOptionsFlowHandler(config_entry)

    async def async_step_user(  # noqa: C901
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
                    # Fetch available users from multiple sources
                    try:
                        users_set = set()

                        # 1. Get users from leaderboard (users with points)
                        try:
                            leaderboard = await api_client.get_leaderboard("alltime")
                            for entry in leaderboard:
                                user_data = entry.get("user", entry)
                                username = user_data.get("username", "")
                                display_name = user_data.get("display_name", username)
                                if username:
                                    users_set.add((username, display_name))
                        except ChoreboardAPIError as err:
                            _LOGGER.debug("Could not fetch leaderboard: %s", err)

                        # 2. Get users from outstanding chores
                        try:
                            outstanding = await api_client.get_outstanding_chores()
                            for chore in outstanding:
                                if assigned_to := chore.get("assigned_to"):
                                    if isinstance(assigned_to, dict):
                                        username = assigned_to.get("username", "")
                                        display_name = assigned_to.get(
                                            "display_name", username
                                        )
                                        if username:
                                            users_set.add((username, display_name))
                        except ChoreboardAPIError as err:
                            _LOGGER.debug("Could not fetch outstanding chores: %s", err)

                        # 3. Get users from late chores
                        try:
                            late = await api_client.get_late_chores()
                            for chore in late:
                                if assigned_to := chore.get("assigned_to"):
                                    if isinstance(assigned_to, dict):
                                        username = assigned_to.get("username", "")
                                        display_name = assigned_to.get(
                                            "display_name", username
                                        )
                                        if username:
                                            users_set.add((username, display_name))
                        except ChoreboardAPIError as err:
                            _LOGGER.debug("Could not fetch late chores: %s", err)

                        # Convert to sorted list
                        self._available_users = [
                            {"username": u, "display_name": d}
                            for u, d in sorted(users_set)
                        ]

                        if not self._available_users:
                            _LOGGER.warning(
                                "No users found in leaderboard or chores. User may need to enter manually."
                            )

                    except Exception as err:
                        _LOGGER.warning("Unexpected error fetching user list: %s", err)
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


class ChoreboardOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for ChoreBoard integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__()
        self._available_users: list[dict[str, str]] = []

    async def async_step_init(  # noqa: C901
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options for monitored users."""
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
                # Update the config entry with new monitored users
                return self.async_create_entry(
                    title="",
                    data={CONF_MONITORED_USERS: monitored_users},
                )

        # Fetch available users using existing credentials
        try:
            session = async_get_clientsession(self.hass)
            api_client = ChoreboardAPIClient(
                self.config_entry.data[CONF_URL],
                self.config_entry.data[CONF_USERNAME],
                self.config_entry.data[CONF_SECRET_KEY],
                session,
            )

            # Fetch users from multiple sources (same logic as config flow)
            users_set = set()

            # 1. Get users from leaderboard
            try:
                leaderboard = await api_client.get_leaderboard("alltime")
                for entry in leaderboard:
                    user_data = entry.get("user", entry)
                    username = user_data.get("username", "")
                    display_name = user_data.get("display_name", username)
                    if username:
                        users_set.add((username, display_name))
            except ChoreboardAPIError as err:
                _LOGGER.debug("Could not fetch leaderboard: %s", err)

            # 2. Get users from outstanding chores
            try:
                outstanding = await api_client.get_outstanding_chores()
                for chore in outstanding:
                    if assigned_to := chore.get("assigned_to"):
                        if isinstance(assigned_to, dict):
                            username = assigned_to.get("username", "")
                            display_name = assigned_to.get("display_name", username)
                            if username:
                                users_set.add((username, display_name))
            except ChoreboardAPIError as err:
                _LOGGER.debug("Could not fetch outstanding chores: %s", err)

            # 3. Get users from late chores
            try:
                late = await api_client.get_late_chores()
                for chore in late:
                    if assigned_to := chore.get("assigned_to"):
                        if isinstance(assigned_to, dict):
                            username = assigned_to.get("username", "")
                            display_name = assigned_to.get("display_name", username)
                            if username:
                                users_set.add((username, display_name))
            except ChoreboardAPIError as err:
                _LOGGER.debug("Could not fetch late chores: %s", err)

            # Convert to sorted list
            self._available_users = [
                {"username": u, "display_name": d} for u, d in sorted(users_set)
            ]

        except Exception as err:
            _LOGGER.warning("Error fetching users for options: %s", err)
            self._available_users = []

        # Get current monitored users
        current_users = self.config_entry.data.get(CONF_MONITORED_USERS, [])

        # Build user selection schema
        if self._available_users:
            # Create a multi-select with available users
            user_options = {
                user["username"]: f"{user['display_name']} ({user['username']})"
                for user in self._available_users
            }

            data_schema = vol.Schema(
                {
                    vol.Required(
                        CONF_MONITORED_USERS, default=current_users
                    ): cv.multi_select(user_options),
                }
            )
        else:
            # Fallback: allow manual entry if we couldn't fetch users
            data_schema = vol.Schema(
                {
                    vol.Required(
                        CONF_MONITORED_USERS, default=",".join(current_users)
                    ): cv.string,
                }
            )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "info": "Update which ChoreBoard users to monitor. Changes will be applied immediately."
            },
        )
