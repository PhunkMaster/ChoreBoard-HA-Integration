"""Fixtures for ChoreBoard integration tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture
def mock_choreboard_api():
    """Mock ChoreBoard API responses."""
    with patch(
        "custom_components.choreboard.coordinator.ChoreboardCoordinator._async_update_data"
    ) as mock_update:
        mock_update.return_value = {
            "outstanding_chores": [
                {
                    "id": 1,
                    "chore": {
                        "name": "Test Chore 1",
                        "description": "Test chore description",
                        "points": 10,
                        "complete_later": False,
                    },
                    "status": "ASSIGNED",
                    "assigned_to": {
                        "username": "testuser",
                        "display_name": "Test User",
                    },
                    "due_at": "2025-12-15T10:00:00Z",
                    "is_overdue": False,
                    "points_value": 10,
                }
            ],
            "late_chores": [
                {
                    "id": 2,
                    "chore": {
                        "name": "Late Chore",
                        "description": "Overdue chore",
                        "points": 5,
                        "complete_later": False,
                    },
                    "status": "ASSIGNED",
                    "assigned_to": {
                        "username": "testuser",
                        "display_name": "Test User",
                    },
                    "due_at": "2025-12-13T10:00:00Z",
                    "is_overdue": True,
                    "points_value": 5,
                }
            ],
            "leaderboard_weekly": [
                {
                    "user": {"username": "testuser", "display_name": "Test User"},
                    "points": 100,
                    "rank": 1,
                }
            ],
            "leaderboard_alltime": [
                {
                    "user": {"username": "testuser", "display_name": "Test User"},
                    "points": 500,
                    "rank": 1,
                }
            ],
            "my_chores": {
                "testuser": [
                    {
                        "id": 1,
                        "chore": {
                            "name": "Test Chore 1",
                            "description": "Test chore description",
                            "points": 10,
                            "complete_later": False,
                        },
                        "status": "ASSIGNED",
                        "assigned_to": {
                            "username": "testuser",
                            "display_name": "Test User",
                        },
                        "due_at": "2025-12-15T10:00:00Z",
                        "is_overdue": False,
                        "points_value": 10,
                    }
                ]
            },
        }
        yield mock_update
