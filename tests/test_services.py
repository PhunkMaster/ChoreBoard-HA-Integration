"""Tests for ChoreBoard services."""

from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.choreboard.const import (
    ATTR_ASSIGN_TO_USER_ID,
    ATTR_CHORE_ID,
    ATTR_COMPLETED_BY_USER_ID,
    ATTR_HELPERS,
    CONF_MONITORED_USERS,
    CONF_SECRET_KEY,
    CONF_URL,
    CONF_USERNAME,
    DOMAIN,
    SERVICE_CLAIM_CHORE,
    SERVICE_MARK_COMPLETE,
    SERVICE_UNDO_COMPLETION,
)


@pytest.fixture
async def setup_integration(hass):
    """Set up the ChoreBoard integration for testing."""
    with patch("custom_components.choreboard.coordinator.ChoreboardCoordinator._async_update_data"):
        entry = config_entries.ConfigEntry(
            version=1,
            minor_version=1,
            domain=DOMAIN,
            title="Test ChoreBoard",
            data={
                CONF_USERNAME: "testuser",
                CONF_SECRET_KEY: "testsecret",
                CONF_URL: "http://localhost:8000",
                CONF_MONITORED_USERS: ["testuser"],
            },
            source="user",
            entry_id="test_entry_id",
            unique_id="test_unique_id",
        )
        entry.add_to_hass(hass)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        return entry


@pytest.mark.asyncio
async def test_mark_complete_basic(hass: HomeAssistant, setup_integration):
    """Test mark_complete service with basic parameters."""
    with patch(
        "custom_components.choreboard.api_client.ChoreboardAPIClient.complete_chore"
    ) as mock_complete:
        mock_complete.return_value = {"success": True}

        await hass.services.async_call(
            DOMAIN,
            SERVICE_MARK_COMPLETE,
            {ATTR_CHORE_ID: 42},
            blocking=True,
        )

        # Verify API was called with correct parameters
        mock_complete.assert_called_once_with(42, None, None)


@pytest.mark.asyncio
async def test_mark_complete_with_helpers(hass: HomeAssistant, setup_integration):
    """Test mark_complete service with helpers."""
    with patch(
        "custom_components.choreboard.api_client.ChoreboardAPIClient.complete_chore"
    ) as mock_complete:
        mock_complete.return_value = {"success": True}

        await hass.services.async_call(
            DOMAIN,
            SERVICE_MARK_COMPLETE,
            {ATTR_CHORE_ID: 42, ATTR_HELPERS: [2, 3]},
            blocking=True,
        )

        # Verify API was called with helpers
        mock_complete.assert_called_once_with(42, [2, 3], None)


@pytest.mark.asyncio
async def test_mark_complete_with_completed_by_user_id(hass: HomeAssistant, setup_integration):
    """Test mark_complete service with completed_by_user_id."""
    with patch(
        "custom_components.choreboard.api_client.ChoreboardAPIClient.complete_chore"
    ) as mock_complete:
        mock_complete.return_value = {"success": True}

        await hass.services.async_call(
            DOMAIN,
            SERVICE_MARK_COMPLETE,
            {ATTR_CHORE_ID: 42, ATTR_COMPLETED_BY_USER_ID: 5},
            blocking=True,
        )

        # Verify API was called with completed_by_user_id
        mock_complete.assert_called_once_with(42, None, 5)


@pytest.mark.asyncio
async def test_mark_complete_with_all_parameters(hass: HomeAssistant, setup_integration):
    """Test mark_complete service with all optional parameters."""
    with patch(
        "custom_components.choreboard.api_client.ChoreboardAPIClient.complete_chore"
    ) as mock_complete:
        mock_complete.return_value = {"success": True}

        await hass.services.async_call(
            DOMAIN,
            SERVICE_MARK_COMPLETE,
            {
                ATTR_CHORE_ID: 42,
                ATTR_HELPERS: [2, 3, 4],
                ATTR_COMPLETED_BY_USER_ID: 5,
            },
            blocking=True,
        )

        # Verify API was called with all parameters
        mock_complete.assert_called_once_with(42, [2, 3, 4], 5)


@pytest.mark.asyncio
async def test_claim_chore_basic(hass: HomeAssistant, setup_integration):
    """Test claim_chore service with basic parameters."""
    with patch(
        "custom_components.choreboard.api_client.ChoreboardAPIClient.claim_chore"
    ) as mock_claim:
        mock_claim.return_value = {"success": True}

        await hass.services.async_call(
            DOMAIN,
            SERVICE_CLAIM_CHORE,
            {ATTR_CHORE_ID: 42},
            blocking=True,
        )

        # Verify API was called with correct parameters
        mock_claim.assert_called_once_with(42, None)


@pytest.mark.asyncio
async def test_claim_chore_with_assign_to_user_id(hass: HomeAssistant, setup_integration):
    """Test claim_chore service with assign_to_user_id."""
    with patch(
        "custom_components.choreboard.api_client.ChoreboardAPIClient.claim_chore"
    ) as mock_claim:
        mock_claim.return_value = {"success": True}

        await hass.services.async_call(
            DOMAIN,
            SERVICE_CLAIM_CHORE,
            {ATTR_CHORE_ID: 42, ATTR_ASSIGN_TO_USER_ID: 3},
            blocking=True,
        )

        # Verify API was called with assign_to_user_id
        mock_claim.assert_called_once_with(42, 3)


@pytest.mark.asyncio
async def test_undo_completion(hass: HomeAssistant, setup_integration):
    """Test undo_completion service."""
    with patch(
        "custom_components.choreboard.api_client.ChoreboardAPIClient.undo_completion"
    ) as mock_undo:
        mock_undo.return_value = {"success": True}

        await hass.services.async_call(
            DOMAIN,
            SERVICE_UNDO_COMPLETION,
            {ATTR_CHORE_ID: 123},
            blocking=True,
        )

        # Verify API was called
        mock_undo.assert_called_once_with(123)


@pytest.mark.asyncio
async def test_service_error_handling(hass: HomeAssistant, setup_integration):
    """Test service error handling."""
    from custom_components.choreboard.api_client import ChoreboardAPIError

    with patch(
        "custom_components.choreboard.api_client.ChoreboardAPIClient.complete_chore"
    ) as mock_complete:
        mock_complete.side_effect = ChoreboardAPIError("API Error")

        with pytest.raises(HomeAssistantError):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_MARK_COMPLETE,
                {ATTR_CHORE_ID: 42},
                blocking=True,
            )


@pytest.mark.asyncio
async def test_service_triggers_refresh(hass: HomeAssistant, setup_integration):
    """Test that services trigger coordinator refresh."""
    with patch(
        "custom_components.choreboard.api_client.ChoreboardAPIClient.complete_chore"
    ) as mock_complete, patch(
        "custom_components.choreboard.coordinator.ChoreboardCoordinator.async_request_refresh"
    ) as mock_refresh:
        mock_complete.return_value = {"success": True}

        await hass.services.async_call(
            DOMAIN,
            SERVICE_MARK_COMPLETE,
            {ATTR_CHORE_ID: 42},
            blocking=True,
        )

        # Verify refresh was requested
        mock_refresh.assert_called_once()
