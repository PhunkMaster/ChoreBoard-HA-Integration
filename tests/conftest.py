"""Fixtures for ChoreBoard integration tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.fixture(scope="session", autouse=True)
def socket_enabled():
    """Enable socket connections for all tests."""
    return True


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
                        "is_pool": False,
                    },
                    "status": "ASSIGNED",
                    "assigned_to": {
                        "username": "testuser",
                        "display_name": "Test User",
                    },
                    "due_at": "2025-12-15T10:00:00Z",
                    "is_overdue": False,
                    "points_value": 10,
                    "last_completion": {
                        "completed_by": {
                            "username": "testuser",
                            "display_name": "Test User",
                        },
                        "completed_at": "2025-12-14T15:30:00Z",
                        "helpers": [],
                        "was_late": False,
                    },
                }
            ],
            "pool_chores": [
                {
                    "id": 3,
                    "chore": {
                        "name": "Pool Chore",
                        "description": "Unassigned pool chore",
                        "points": 15,
                        "complete_later": False,
                        "is_pool": True,
                    },
                    "status": "POOL",
                    "assigned_to": None,
                    "due_at": "2025-12-16T10:00:00Z",
                    "is_overdue": False,
                    "points_value": 15,
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
            "users": [
                {
                    "id": 1,
                    "username": "testuser",
                    "display_name": "Test User",
                    "weekly_points": 100,
                    "all_time_points": 500,
                    "claims_today": 2,
                }
            ],
            "recent_completions": [
                {
                    "id": 10,
                    "chore_instance": {
                        "id": 1,
                        "chore": {
                            "name": "Test Chore 1",
                            "points": 10,
                        },
                        "points_value": 10,
                    },
                    "completed_by": {
                        "username": "testuser",
                        "display_name": "Test User",
                    },
                    "completed_at": "2025-12-14T15:30:00Z",
                    "was_late": False,
                    "shares": [
                        {
                            "user": {
                                "username": "helper1",
                                "display_name": "Helper One",
                            },
                            "points_awarded": 3,
                        }
                    ],
                }
            ],
            "chore_leaderboards": [
                {
                    "chore_id": 1,
                    "chore_name": "Speed Chore",
                    "high_scores": [
                        {
                            "rank": 1,
                            "user": {
                                "username": "testuser",
                                "display_name": "Test User",
                            },
                            "time_seconds": 45,
                            "time_formatted": "0:45",
                            "achieved_at": "2025-12-14T12:00:00Z",
                        }
                    ],
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
