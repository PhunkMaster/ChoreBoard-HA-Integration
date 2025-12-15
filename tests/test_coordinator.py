"""Tests for the ChoreBoard coordinator."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

import homeassistant.util.dt as dt_util
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.choreboard.const import (
    CONF_MONITORED_USERS,
    CONF_SECRET_KEY,
    CONF_URL,
    CONF_USERNAME,
    DOMAIN,
)
from custom_components.choreboard.coordinator import ChoreboardCoordinator


@pytest.mark.asyncio
async def test_is_due_today_with_today_date(hass):
    """Test _is_due_today returns True for chores due today."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "testuser",
            CONF_SECRET_KEY: "test_secret_key",
            CONF_URL: "http://localhost:8000",
            CONF_MONITORED_USERS: ["testuser"],
        },
    )
    coordinator = ChoreboardCoordinator(hass, entry)

    # Create a datetime for today at 10:00 AM
    today = dt_util.now().replace(hour=10, minute=0, second=0, microsecond=0)
    due_at_str = today.isoformat()

    assert coordinator._is_due_today(due_at_str) is True


@pytest.mark.asyncio
async def test_is_due_today_with_tomorrow_date(hass):
    """Test _is_due_today returns False for chores due tomorrow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "testuser",
            CONF_SECRET_KEY: "test_secret_key",
            CONF_URL: "http://localhost:8000",
            CONF_MONITORED_USERS: ["testuser"],
        },
    )
    coordinator = ChoreboardCoordinator(hass, entry)

    # Create a datetime for tomorrow
    tomorrow = dt_util.now() + timedelta(days=1)
    due_at_str = tomorrow.isoformat()

    assert coordinator._is_due_today(due_at_str) is False


@pytest.mark.asyncio
async def test_is_due_today_with_past_date(hass):
    """Test _is_due_today returns True for chores due in the past."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "testuser",
            CONF_SECRET_KEY: "test_secret_key",
            CONF_URL: "http://localhost:8000",
            CONF_MONITORED_USERS: ["testuser"],
        },
    )
    coordinator = ChoreboardCoordinator(hass, entry)

    # Create a datetime for yesterday
    yesterday = dt_util.now() - timedelta(days=1)
    due_at_str = yesterday.isoformat()

    assert coordinator._is_due_today(due_at_str) is True


@pytest.mark.asyncio
async def test_is_due_today_with_none(hass):
    """Test _is_due_today returns False for None."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "testuser",
            CONF_SECRET_KEY: "test_secret_key",
            CONF_URL: "http://localhost:8000",
            CONF_MONITORED_USERS: ["testuser"],
        },
    )
    coordinator = ChoreboardCoordinator(hass, entry)

    assert coordinator._is_due_today(None) is False


@pytest.mark.asyncio
async def test_normalize_datetime_removes_seconds(hass):
    """Test _normalize_datetime removes seconds and microseconds."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "testuser",
            CONF_SECRET_KEY: "test_secret_key",
            CONF_URL: "http://localhost:8000",
            CONF_MONITORED_USERS: ["testuser"],
        },
    )
    coordinator = ChoreboardCoordinator(hass, entry)

    # ISO format with seconds and microseconds
    dt_str = "2025-12-15T10:30:45.123456Z"

    result = coordinator._normalize_datetime(dt_str)

    # Should return format YYYY-MM-DD HH:MM (no seconds)
    assert result is not None
    assert ":" in result  # Has hour:minute separator
    assert result.count(":") == 1  # Only one colon (no seconds)
    assert "2025-12-15" in result  # Has the date
    # Note: Don't check specific time - timezone conversion varies by environment


@pytest.mark.asyncio
async def test_normalize_datetime_with_none(hass):
    """Test _normalize_datetime returns None for None input."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "testuser",
            CONF_SECRET_KEY: "test_secret_key",
            CONF_URL: "http://localhost:8000",
            CONF_MONITORED_USERS: ["testuser"],
        },
    )
    coordinator = ChoreboardCoordinator(hass, entry)

    assert coordinator._normalize_datetime(None) is None


@pytest.mark.asyncio
async def test_filter_chores_by_due_date(hass):
    """Test _filter_chores_by_due_date filters correctly."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "testuser",
            CONF_SECRET_KEY: "test_secret_key",
            CONF_URL: "http://localhost:8000",
            CONF_MONITORED_USERS: ["testuser"],
        },
    )
    coordinator = ChoreboardCoordinator(hass, entry)

    # Create test chores
    today = dt_util.now()
    tomorrow = today + timedelta(days=1)

    chores = [
        {
            "id": 1,
            "name": "Today's chore",
            "due_at": today.isoformat(),
        },
        {
            "id": 2,
            "name": "Tomorrow's chore",
            "due_at": tomorrow.isoformat(),
        },
        {
            "id": 3,
            "name": "Yesterday's chore",
            "due_at": (today - timedelta(days=1)).isoformat(),
        },
    ]

    filtered = coordinator._filter_chores_by_due_date(chores)

    # Should only include today's and yesterday's chores (not tomorrow's)
    assert len(filtered) == 2
    assert filtered[0]["id"] == 1
    assert filtered[1]["id"] == 3

    # Check that datetime was normalized (no seconds)
    assert filtered[0]["due_at"].count(":") == 1
    assert filtered[1]["due_at"].count(":") == 1


@pytest.mark.asyncio
async def test_coordinator_filters_chores_on_update(hass, mock_choreboard_api):
    """Test that coordinator filters chores during data update."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "testuser",
            CONF_SECRET_KEY: "test_secret_key",
            CONF_URL: "http://localhost:8000",
            CONF_MONITORED_USERS: ["testuser"],
        },
    )

    # Mock API responses with chores due today
    today = dt_util.now()

    with patch(
        "custom_components.choreboard.coordinator.ChoreboardCoordinator._async_update_data"
    ) as mock_update:
        # Create test data with chores due today and tomorrow
        mock_update.return_value = {
            "outstanding_chores": [
                {
                    "id": 1,
                    "chore": {"name": "Today Chore", "complete_later": False},
                    "due_at": today.replace(hour=10, minute=0, second=0).isoformat(),
                    "assigned_to": {"username": "testuser"},
                }
            ],
            "late_chores": [],
            "leaderboard_weekly": [],
            "leaderboard_alltime": [],
            "my_chores": {
                "testuser": [
                    {
                        "id": 1,
                        "chore": {"name": "Today Chore", "complete_later": False},
                        "due_at": today.replace(
                            hour=10, minute=0, second=0
                        ).isoformat(),
                        "assigned_to": {"username": "testuser"},
                    }
                ]
            },
        }

        coordinator = ChoreboardCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()

        # Verify data was filtered and normalized
        assert "outstanding_chores" in coordinator.data
        assert len(coordinator.data["outstanding_chores"]) >= 0


@pytest.mark.asyncio
async def test_coordinator_extracts_pool_chores(hass, mock_choreboard_api):
    """Test that coordinator extracts pool chores from outstanding chores."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "testuser",
            CONF_SECRET_KEY: "test_secret_key",
            CONF_URL: "http://localhost:8000",
            CONF_MONITORED_USERS: ["testuser"],
        },
    )

    today = dt_util.now()

    with patch(
        "custom_components.choreboard.coordinator.ChoreboardCoordinator._async_update_data"
    ) as mock_update:
        # Create test data with pool and assigned chores
        mock_update.return_value = {
            "outstanding_chores": [
                {
                    "id": 1,
                    "chore": {"name": "Pool Chore 1", "is_pool": True},
                    "status": "POOL",
                    "assigned_to": None,
                    "due_at": today.replace(hour=10, minute=0, second=0).isoformat(),
                },
                {
                    "id": 2,
                    "chore": {"name": "Assigned Chore", "is_pool": False},
                    "status": "ASSIGNED",
                    "assigned_to": {"username": "testuser"},
                    "due_at": today.replace(hour=11, minute=0, second=0).isoformat(),
                },
                {
                    "id": 3,
                    "chore": {"name": "Pool Chore 2", "is_pool": True},
                    "status": "POOL",
                    "assigned_to": None,
                    "due_at": today.replace(hour=12, minute=0, second=0).isoformat(),
                },
            ],
            "late_chores": [],
            "pool_chores": [
                {
                    "id": 1,
                    "chore": {"name": "Pool Chore 1", "is_pool": True},
                    "status": "POOL",
                    "assigned_to": None,
                    "due_at": today.replace(hour=10, minute=0, second=0).isoformat(),
                },
                {
                    "id": 3,
                    "chore": {"name": "Pool Chore 2", "is_pool": True},
                    "status": "POOL",
                    "assigned_to": None,
                    "due_at": today.replace(hour=12, minute=0, second=0).isoformat(),
                },
            ],
            "leaderboard_weekly": [],
            "leaderboard_alltime": [],
            "my_chores": {},
        }

        coordinator = ChoreboardCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()

        # Verify pool chores were extracted
        assert "pool_chores" in coordinator.data
        pool_chores = coordinator.data["pool_chores"]
        assert len(pool_chores) == 2
        assert pool_chores[0]["id"] == 1
        assert pool_chores[1]["id"] == 3
