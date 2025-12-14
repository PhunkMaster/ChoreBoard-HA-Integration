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
            "test_chore_1": {
                "id": "test_chore_1",
                "name": "Test Chore 1",
                "status": "pending",
                "assignee": "Test User",
                "due_date": "2025-12-15",
                "points": 10,
                "description": "Test chore description",
            },
            "test_chore_2": {
                "id": "test_chore_2",
                "name": "Test Chore 2",
                "status": "completed",
                "assignee": "Test User 2",
                "due_date": "2025-12-14",
                "points": 5,
                "description": "Another test chore",
            },
        }
        yield mock_update
