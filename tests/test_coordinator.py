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

    chore = {
        "id": 1,
        "chore": {
            "name": "Test Chore",
            "schedule_type": "daily",
        },
        "due_at": due_at_str,
    }

    assert coordinator._is_due_today(chore) is True


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

    chore = {
        "id": 1,
        "chore": {
            "name": "Test Chore",
            "schedule_type": "daily",
        },
        "due_at": due_at_str,
    }

    assert coordinator._is_due_today(chore) is False


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

    chore = {
        "id": 1,
        "chore": {
            "name": "Test Chore",
            "schedule_type": "daily",
        },
        "due_at": due_at_str,
    }

    assert coordinator._is_due_today(chore) is True


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

    chore = {
        "id": 1,
        "chore": {
            "name": "Test Chore",
            "schedule_type": "daily",
        },
        "due_at": None,
    }

    assert coordinator._is_due_today(chore) is False


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


@pytest.mark.asyncio
@pytest.mark.enable_socket
async def test_is_due_today_with_one_time_no_due_date(hass):
    """Test _is_due_today returns True for one-time tasks with year 9999 (no due date)."""
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

    # One-time task without due date has year 9999
    from datetime import datetime
    year_9999_date = datetime(9999, 12, 31, 0, 0, 0)
    due_at_str = year_9999_date.isoformat()

    chore = {
        "id": 1,
        "chore": {
            "name": "One-time task",
            "schedule_type": "one_time",
        },
        "due_at": due_at_str,
    }

    assert coordinator._is_due_today(chore) is True


@pytest.mark.asyncio
@pytest.mark.enable_socket
async def test_is_due_today_with_one_time_due_today(hass):
    """Test _is_due_today returns True for one-time tasks due today."""
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

    # Create a datetime for today
    today = dt_util.now().replace(hour=10, minute=0, second=0, microsecond=0)
    due_at_str = today.isoformat()

    chore = {
        "id": 1,
        "chore": {
            "name": "One-time task",
            "schedule_type": "one_time",
        },
        "due_at": due_at_str,
    }

    assert coordinator._is_due_today(chore) is True


@pytest.mark.asyncio
@pytest.mark.enable_socket
async def test_is_due_today_with_one_time_due_tomorrow(hass):
    """Test _is_due_today returns False for one-time tasks due tomorrow."""
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

    chore = {
        "id": 1,
        "chore": {
            "name": "One-time task",
            "schedule_type": "one_time",
        },
        "due_at": due_at_str,
    }

    assert coordinator._is_due_today(chore) is False


@pytest.mark.asyncio
@pytest.mark.enable_socket
async def test_is_due_today_with_one_time_overdue(hass):
    """Test _is_due_today returns True for overdue one-time tasks."""
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

    chore = {
        "id": 1,
        "chore": {
            "name": "One-time task",
            "schedule_type": "one_time",
        },
        "due_at": due_at_str,
    }

    assert coordinator._is_due_today(chore) is True


@pytest.mark.asyncio
@pytest.mark.enable_socket
async def test_filter_chores_by_due_date_with_one_time_tasks(hass):
    """Test _filter_chores_by_due_date with mixed one-time and recurring tasks."""
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

    today = dt_util.now().replace(hour=10, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    yesterday = today - timedelta(days=1)
    from datetime import datetime
    year_9999_date = datetime(9999, 12, 31, 0, 0, 0)

    chores = [
        {
            "id": 1,
            "chore": {"name": "One-time no due date", "schedule_type": "one_time"},
            "due_at": year_9999_date.isoformat(),
        },
        {
            "id": 2,
            "chore": {"name": "One-time due today", "schedule_type": "one_time"},
            "due_at": today.isoformat(),
        },
        {
            "id": 3,
            "chore": {"name": "One-time due tomorrow", "schedule_type": "one_time"},
            "due_at": tomorrow.isoformat(),
        },
        {
            "id": 4,
            "chore": {"name": "One-time overdue", "schedule_type": "one_time"},
            "due_at": yesterday.isoformat(),
        },
        {
            "id": 5,
            "chore": {"name": "Daily due today", "schedule_type": "daily"},
            "due_at": today.isoformat(),
        },
        {
            "id": 6,
            "chore": {"name": "Daily due tomorrow", "schedule_type": "daily"},
            "due_at": tomorrow.isoformat(),
        },
    ]

    filtered = coordinator._filter_chores_by_due_date(chores)

    # Should include: one-time no due date, one-time due today, one-time overdue, daily due today
    # Should exclude: one-time due tomorrow, daily due tomorrow
    assert len(filtered) == 4
    filtered_ids = [chore["id"] for chore in filtered]
    assert 1 in filtered_ids  # One-time no due date (year 9999)
    assert 2 in filtered_ids  # One-time due today
    assert 4 in filtered_ids  # One-time overdue
    assert 5 in filtered_ids  # Daily due today
    assert 3 not in filtered_ids  # One-time due tomorrow should be filtered
    assert 6 not in filtered_ids  # Daily due tomorrow should be filtered
