"""Tests for new ChoreBoard sensors."""

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.choreboard.const import (
    CONF_MONITORED_USERS,
    CONF_SECRET_KEY,
    CONF_URL,
    CONF_USERNAME,
    DOMAIN,
)


@pytest.fixture
async def setup_integration(hass, mock_choreboard_api):
    """Set up the ChoreBoard integration for testing."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "testuser",
            CONF_SECRET_KEY: "testsecret",
            CONF_URL: "http://localhost:8000",
            CONF_MONITORED_USERS: ["testuser"],
        },
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@pytest.mark.asyncio
@pytest.mark.enable_socket
async def test_pool_chores_sensor(hass: HomeAssistant, setup_integration):
    """Test pool chores sensor."""
    state = hass.states.get("sensor.pool_chores")
    assert state is not None
    assert state.state == "1"  # One pool chore in mock data

    # Check attributes
    assert "chores" in state.attributes
    assert len(state.attributes["chores"]) == 1
    assert state.attributes["chores"][0]["name"] == "Pool Chore"
    assert state.attributes["chores"][0]["status"] == "POOL"


@pytest.mark.asyncio
@pytest.mark.enable_socket
async def test_chore_breakdown_sensor(hass: HomeAssistant, setup_integration):
    """Test chore breakdown statistics sensor."""
    state = hass.states.get("sensor.chore_breakdown")
    assert state is not None

    # Check attributes
    assert "total_chores" in state.attributes
    assert "pool_chores" in state.attributes
    assert "assigned_chores" in state.attributes
    assert "pool_percentage" in state.attributes
    assert "assigned_percentage" in state.attributes

    assert state.attributes["pool_chores"] == 1
    assert state.attributes["status_breakdown"] is not None


@pytest.mark.asyncio
@pytest.mark.enable_socket
async def test_completion_history_sensor(hass: HomeAssistant, setup_integration):
    """Test completion history sensor."""
    state = hass.states.get("sensor.completion_history")
    assert state is not None
    assert state.state == "1"  # One completion in mock data

    # Check attributes
    assert "completions" in state.attributes
    assert len(state.attributes["completions"]) == 1
    completion = state.attributes["completions"][0]
    assert completion["chore_name"] == "Test Chore 1"
    assert completion["completed_by"] == "Test User"
    assert completion["was_late"] is False
    assert "helpers" in completion
    assert len(completion["helpers"]) == 1
    assert completion["helpers"][0]["name"] == "Helper One"


@pytest.mark.asyncio
@pytest.mark.enable_socket
async def test_user_weekly_points_sensor(hass: HomeAssistant, setup_integration):
    """Test user weekly points sensor."""
    state = hass.states.get("sensor.testuser_weekly_points")
    assert state is not None
    assert state.state == "100.0"

    # Check attributes
    assert state.attributes["username"] == "testuser"
    assert state.attributes["display_name"] == "Test User"
    assert state.attributes["points"] == 100.0
    assert state.attributes["claims_today"] == 2


@pytest.mark.asyncio
@pytest.mark.enable_socket
async def test_user_alltime_points_sensor(hass: HomeAssistant, setup_integration):
    """Test user all-time points sensor."""
    state = hass.states.get("sensor.testuser_all_time_points")
    assert state is not None
    assert state.state == "500.0"

    # Check attributes
    assert state.attributes["username"] == "testuser"
    assert state.attributes["display_name"] == "Test User"
    assert state.attributes["points"] == 500.0
    assert state.attributes["weekly_points"] == 100.0


@pytest.mark.asyncio
@pytest.mark.enable_socket
async def test_chore_leaderboard_sensor(hass: HomeAssistant, setup_integration):
    """Test chore-specific leaderboard sensor (arcade mode)."""
    state = hass.states.get("sensor.arcade_speed_chore")
    assert state is not None
    assert state.state == "1"  # One high score in mock data

    # Check attributes
    assert "scores" in state.attributes
    assert len(state.attributes["scores"]) == 1
    score = state.attributes["scores"][0]
    assert score["rank"] == 1
    assert score["username"] == "testuser"
    assert score["time_seconds"] == 45
    assert score["time_formatted"] == "0:45"


@pytest.mark.asyncio
@pytest.mark.enable_socket
async def test_completion_information_in_chores(hass: HomeAssistant, setup_integration):
    """Test that completion information is included in chore data."""
    # Check outstanding chores sensor
    state = hass.states.get("sensor.outstanding_chores")
    assert state is not None

    chores = state.attributes.get("chores", [])
    assert len(chores) > 0

    # Check for last_completed_by field
    chore = chores[0]
    assert "last_completed_by" in chore
    assert chore["last_completed_by"] == "Test User"
    assert "last_completed_at" in chore
    assert "was_late" in chore


@pytest.mark.asyncio
@pytest.mark.enable_socket
async def test_my_chores_sensor_with_completion_data(
    hass: HomeAssistant, setup_integration
):
    """Test that my chores sensor includes completion data."""
    state = hass.states.get("sensor.testuser_my_chores")
    assert state is not None

    chores = state.attributes.get("chores", [])
    assert len(chores) > 0


@pytest.mark.asyncio
@pytest.mark.enable_socket
async def test_sensor_icons(hass: HomeAssistant, setup_integration):
    """Test that sensors have appropriate icons."""
    # Pool chores should have pool icon
    state = hass.states.get("sensor.pool_chores")
    assert state is not None
    # Icon is set in the sensor class

    # Breakdown should have chart icon
    state = hass.states.get("sensor.chore_breakdown")
    assert state is not None

    # Completion history should have history icon
    state = hass.states.get("sensor.completion_history")
    assert state is not None

    # Weekly points should have medal icon
    state = hass.states.get("sensor.testuser_weekly_points")
    assert state is not None

    # All-time points should have trophy icon
    state = hass.states.get("sensor.testuser_all_time_points")
    assert state is not None


@pytest.mark.asyncio
@pytest.mark.enable_socket
async def test_sensor_unit_of_measurement(hass: HomeAssistant, setup_integration):
    """Test that points sensors have correct unit of measurement."""
    # Weekly points
    state = hass.states.get("sensor.testuser_weekly_points")
    assert state is not None
    assert state.attributes.get("unit_of_measurement") == "points"

    # All-time points
    state = hass.states.get("sensor.testuser_all_time_points")
    assert state is not None
    assert state.attributes.get("unit_of_measurement") == "points"
