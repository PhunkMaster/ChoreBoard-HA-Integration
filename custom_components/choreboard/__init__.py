"""The ChoreBoard integration."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .api_client import ChoreboardAPIError
from .const import (
    ATTR_ASSIGN_TO_USER_ID,
    ATTR_CHORE_ID,
    ATTR_COMPLETED_BY_USER_ID,
    ATTR_HELPERS,
    DOMAIN,
    PLATFORMS,
    SERVICE_CLAIM_CHORE,
    SERVICE_MARK_COMPLETE,
    SERVICE_UNDO_COMPLETION,
)
from .coordinator import ChoreboardCoordinator

_LOGGER = logging.getLogger(__name__)

# Service schemas
SERVICE_MARK_COMPLETE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CHORE_ID): cv.positive_int,
        vol.Optional(ATTR_HELPERS): vol.All(cv.ensure_list, [cv.positive_int]),
        vol.Optional(ATTR_COMPLETED_BY_USER_ID): cv.positive_int,
    }
)

SERVICE_CLAIM_CHORE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CHORE_ID): cv.positive_int,
        vol.Optional(ATTR_ASSIGN_TO_USER_ID): cv.positive_int,
    }
)

SERVICE_UNDO_COMPLETION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CHORE_ID): cv.positive_int,
    }
)


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    # Reload the config entry to apply new monitored users
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ChoreBoard from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create coordinator
    coordinator = ChoreboardCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Add update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    # Register services
    async def handle_mark_complete(call: ServiceCall) -> None:
        """Handle the mark_complete service call."""
        instance_id = call.data[ATTR_CHORE_ID]
        helper_ids = call.data.get(ATTR_HELPERS)
        completed_by_user_id = call.data.get(ATTR_COMPLETED_BY_USER_ID)

        _LOGGER.debug(
            "Mark complete service called for chore instance %s (completed_by: %s, helpers: %s)",
            instance_id,
            completed_by_user_id,
            helper_ids,
        )

        try:
            await coordinator.api_client.complete_chore(
                instance_id, helper_ids, completed_by_user_id
            )
            # Immediate refresh after user action for instant feedback
            await coordinator.async_refresh_immediately()
            _LOGGER.info("Successfully completed chore instance %s", instance_id)
        except ChoreboardAPIError as err:
            _LOGGER.error("Failed to complete chore instance %s: %s", instance_id, err)
            raise HomeAssistantError(f"Failed to complete chore: {err}") from err

    async def handle_claim_chore(call: ServiceCall) -> None:
        """Handle the claim_chore service call."""
        instance_id = call.data[ATTR_CHORE_ID]
        assign_to_user_id = call.data.get(ATTR_ASSIGN_TO_USER_ID)

        _LOGGER.debug(
            "Claim chore service called for chore instance %s (assign_to: %s)",
            instance_id,
            assign_to_user_id,
        )

        try:
            await coordinator.api_client.claim_chore(instance_id, assign_to_user_id)
            # Immediate refresh after user action for instant feedback
            await coordinator.async_refresh_immediately()
            _LOGGER.info("Successfully claimed chore instance %s", instance_id)
        except ChoreboardAPIError as err:
            _LOGGER.error("Failed to claim chore instance %s: %s", instance_id, err)
            raise HomeAssistantError(f"Failed to claim chore: {err}") from err

    async def handle_undo_completion(call: ServiceCall) -> None:
        """Handle the undo_completion service call."""
        completion_id = call.data[ATTR_CHORE_ID]

        _LOGGER.debug("Undo completion service called for completion %s", completion_id)

        try:
            await coordinator.api_client.undo_completion(completion_id)
            # Immediate refresh after user action for instant feedback
            await coordinator.async_refresh_immediately()
            _LOGGER.info("Successfully undid completion %s", completion_id)
        except ChoreboardAPIError as err:
            _LOGGER.error("Failed to undo completion %s: %s", completion_id, err)
            raise HomeAssistantError(f"Failed to undo completion: {err}") from err

    # Register all services
    hass.services.async_register(
        DOMAIN,
        SERVICE_MARK_COMPLETE,
        handle_mark_complete,
        schema=SERVICE_MARK_COMPLETE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CLAIM_CHORE,
        handle_claim_chore,
        schema=SERVICE_CLAIM_CHORE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_UNDO_COMPLETION,
        handle_undo_completion,
        schema=SERVICE_UNDO_COMPLETION_SCHEMA,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
