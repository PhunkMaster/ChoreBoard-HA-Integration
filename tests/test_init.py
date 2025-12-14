"""Tests for the ChoreBoard integration initialization."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.choreboard.const import CONF_API_KEY, CONF_URL, DOMAIN


@pytest.mark.asyncio
async def test_setup_entry(hass, mock_choreboard_api):
    """Test successful setup of a config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_KEY: "test_api_key",
            CONF_URL: "https://api.choreboard.com",
        },
    )
    entry.add_to_hass(hass)

    # Setup the integration
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Verify the integration is loaded
    assert DOMAIN in hass.data
    assert entry.entry_id in hass.data[DOMAIN]


@pytest.mark.asyncio
async def test_unload_entry(hass, mock_choreboard_api):
    """Test unloading a config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_API_KEY: "test_api_key",
            CONF_URL: "https://api.choreboard.com",
        },
    )
    entry.add_to_hass(hass)

    # Setup the integration
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Unload the integration
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    # Verify the integration is unloaded
    assert entry.entry_id not in hass.data[DOMAIN]
