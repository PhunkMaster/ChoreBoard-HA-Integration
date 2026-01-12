"""Tests for ChoreboardCoordinator static methods."""

from __future__ import annotations

from datetime import timedelta

import homeassistant.util.dt as dt_util

from custom_components.choreboard.coordinator import ChoreboardCoordinator


def test_is_due_today_with_today_date():
    """Test _is_due_today returns True for chores due today."""
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

    assert ChoreboardCoordinator._is_due_today(chore) is True


def test_is_due_today_with_tomorrow_date():
    """Test _is_due_today returns False for chores due tomorrow."""
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

    assert ChoreboardCoordinator._is_due_today(chore) is False


def test_is_due_today_with_past_date():
    """Test _is_due_today returns True for chores due in the past."""
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

    assert ChoreboardCoordinator._is_due_today(chore) is True


def test_is_due_today_with_none():
    """Test _is_due_today returns False for None."""
    chore = {
        "id": 1,
        "chore": {
            "name": "Test Chore",
            "schedule_type": "daily",
        },
        "due_at": None,
    }

    assert ChoreboardCoordinator._is_due_today(chore) is False


def test_normalize_datetime_removes_seconds():
    """Test _normalize_datetime removes seconds and microseconds."""
    # ISO format with seconds and microseconds
    dt_str = "2025-12-15T10:30:45.123456Z"

    result = ChoreboardCoordinator._normalize_datetime(dt_str)

    # Should return format YYYY-MM-DD HH:MM (no seconds)
    assert result is not None
    assert ":" in result  # Has hour:minute separator
    assert result.count(":") == 1  # Only one colon (no seconds)
    assert "2025-12-15" in result  # Has the date
    # Note: Don't check specific time - timezone conversion varies by environment


def test_normalize_datetime_with_none():
    """Test _normalize_datetime returns None for None input."""
    assert ChoreboardCoordinator._normalize_datetime(None) is None
