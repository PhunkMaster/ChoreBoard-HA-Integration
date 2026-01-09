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
    ATTR_INSTANCE_ID,
    ATTR_JUDGE_ID,
    ATTR_NOTES,
    ATTR_SESSION_ID,
    ATTR_USER_ID,
    DOMAIN,
    PLATFORMS,
    SERVICE_APPROVE_ARCADE,
    SERVICE_CANCEL_ARCADE,
    SERVICE_CLAIM_CHORE,
    SERVICE_CONTINUE_ARCADE,
    SERVICE_DENY_ARCADE,
    SERVICE_MARK_COMPLETE,
    SERVICE_START_ARCADE,
    SERVICE_STOP_ARCADE,
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

SERVICE_UNCLAIM_CHORE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CHORE_ID): cv.positive_int,
    }
)

SERVICE_UNDO_COMPLETION_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CHORE_ID): cv.positive_int,
    }
)

SERVICE_START_ARCADE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_INSTANCE_ID): cv.positive_int,
        vol.Optional(ATTR_USER_ID): cv.positive_int,
    }
)

SERVICE_STOP_ARCADE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_SESSION_ID): cv.positive_int,
    }
)

SERVICE_APPROVE_ARCADE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_SESSION_ID): cv.positive_int,
        vol.Optional(ATTR_JUDGE_ID): cv.positive_int,
        vol.Optional(ATTR_NOTES): cv.string,
    }
)

SERVICE_DENY_ARCADE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_SESSION_ID): cv.positive_int,
        vol.Optional(ATTR_JUDGE_ID): cv.positive_int,
        vol.Optional(ATTR_NOTES): cv.string,
    }
)

SERVICE_CONTINUE_ARCADE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_SESSION_ID): cv.positive_int,
    }
)

SERVICE_CANCEL_ARCADE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_SESSION_ID): cv.positive_int,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:  # noqa: C901
    """Set up ChoreBoard from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create coordinator
    coordinator = ChoreboardCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

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

    async def handle_unclaim_chore(call: ServiceCall) -> None:
        """Handle the unclaim_chore service call."""
        instance_id = call.data[ATTR_CHORE_ID]

        _LOGGER.debug("Unclaim chore service called for instance %s", instance_id)

        try:
            await coordinator.api_client.unclaim_chore(instance_id)
            await coordinator.async_refresh_immediately()
            _LOGGER.info("Successfully unclaimed chore instance %s", instance_id)
        except ChoreboardAPIError as err:
            _LOGGER.error("Failed to unclaim chore instance %s: %s", instance_id, err)
            raise HomeAssistantError(f"Failed to unclaim chore: {err}") from err

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

    async def handle_start_arcade(call: ServiceCall) -> None:
        """Handle the start_arcade service call."""
        instance_id = call.data[ATTR_INSTANCE_ID]
        user_id = call.data.get(ATTR_USER_ID)

        _LOGGER.debug(
            "Start arcade service called for instance %s (user_id: %s)",
            instance_id,
            user_id,
        )

        try:
            await coordinator.api_client.start_arcade(instance_id, user_id)
            # Immediate refresh after user action for instant feedback
            await coordinator.async_refresh_immediately()
            _LOGGER.info("Successfully started arcade for instance %s", instance_id)
        except ChoreboardAPIError as err:
            _LOGGER.error(
                "Failed to start arcade for instance %s: %s", instance_id, err
            )
            raise HomeAssistantError(f"Failed to start arcade: {err}") from err

    async def handle_stop_arcade(call: ServiceCall) -> None:
        """Handle the stop_arcade service call."""
        session_id = call.data[ATTR_SESSION_ID]

        _LOGGER.debug("Stop arcade service called for session %s", session_id)

        try:
            await coordinator.api_client.stop_arcade(session_id)
            # Immediate refresh after user action for instant feedback
            await coordinator.async_refresh_immediately()
            _LOGGER.info("Successfully stopped arcade session %s", session_id)
        except ChoreboardAPIError as err:
            _LOGGER.error("Failed to stop arcade session %s: %s", session_id, err)
            raise HomeAssistantError(f"Failed to stop arcade: {err}") from err

    async def handle_approve_arcade(call: ServiceCall) -> None:
        """Handle the approve_arcade service call."""
        session_id = call.data[ATTR_SESSION_ID]
        judge_id = call.data.get(ATTR_JUDGE_ID)
        notes = call.data.get(ATTR_NOTES, "")

        _LOGGER.debug(
            "Approve arcade service called for session %s (judge_id: %s)",
            session_id,
            judge_id,
        )

        try:
            await coordinator.api_client.approve_arcade(session_id, judge_id, notes)
            # Immediate refresh after user action for instant feedback
            await coordinator.async_refresh_immediately()
            _LOGGER.info("Successfully approved arcade session %s", session_id)
        except ChoreboardAPIError as err:
            _LOGGER.error("Failed to approve arcade session %s: %s", session_id, err)
            raise HomeAssistantError(f"Failed to approve arcade: {err}") from err

    async def handle_deny_arcade(call: ServiceCall) -> None:
        """Handle the deny_arcade service call."""
        session_id = call.data[ATTR_SESSION_ID]
        judge_id = call.data.get(ATTR_JUDGE_ID)
        notes = call.data.get(ATTR_NOTES, "")

        _LOGGER.debug(
            "Deny arcade service called for session %s (judge_id: %s)",
            session_id,
            judge_id,
        )

        try:
            await coordinator.api_client.deny_arcade(session_id, judge_id, notes)
            # Immediate refresh after user action for instant feedback
            await coordinator.async_refresh_immediately()
            _LOGGER.info("Successfully denied arcade session %s", session_id)
        except ChoreboardAPIError as err:
            _LOGGER.error("Failed to deny arcade session %s: %s", session_id, err)
            raise HomeAssistantError(f"Failed to deny arcade: {err}") from err

    async def handle_continue_arcade(call: ServiceCall) -> None:
        """Handle the continue_arcade service call."""
        session_id = call.data[ATTR_SESSION_ID]

        _LOGGER.debug("Continue arcade service called for session %s", session_id)

        try:
            await coordinator.api_client.continue_arcade(session_id)
            # Immediate refresh after user action for instant feedback
            await coordinator.async_refresh_immediately()
            _LOGGER.info("Successfully continued arcade session %s", session_id)
        except ChoreboardAPIError as err:
            _LOGGER.error("Failed to continue arcade session %s: %s", session_id, err)
            raise HomeAssistantError(f"Failed to continue arcade: {err}") from err

    async def handle_cancel_arcade(call: ServiceCall) -> None:
        """Handle the cancel_arcade service call."""
        session_id = call.data[ATTR_SESSION_ID]

        _LOGGER.debug("Cancel arcade service called for session %s", session_id)

        try:
            await coordinator.api_client.cancel_arcade(session_id)
            # Immediate refresh after user action for instant feedback
            await coordinator.async_refresh_immediately()
            _LOGGER.info("Successfully cancelled arcade session %s", session_id)
        except ChoreboardAPIError as err:
            _LOGGER.error("Failed to cancel arcade session %s: %s", session_id, err)
            raise HomeAssistantError(f"Failed to cancel arcade: {err}") from err

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
        SERVICE_UNCLAIM_CHORE,
        handle_unclaim_chore,
        schema=SERVICE_UNCLAIM_CHORE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_UNDO_COMPLETION,
        handle_undo_completion,
        schema=SERVICE_UNDO_COMPLETION_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_START_ARCADE,
        handle_start_arcade,
        schema=SERVICE_START_ARCADE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP_ARCADE,
        handle_stop_arcade,
        schema=SERVICE_STOP_ARCADE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_APPROVE_ARCADE,
        handle_approve_arcade,
        schema=SERVICE_APPROVE_ARCADE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DENY_ARCADE,
        handle_deny_arcade,
        schema=SERVICE_DENY_ARCADE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CONTINUE_ARCADE,
        handle_continue_arcade,
        schema=SERVICE_CONTINUE_ARCADE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CANCEL_ARCADE,
        handle_cancel_arcade,
        schema=SERVICE_CANCEL_ARCADE_SCHEMA,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
