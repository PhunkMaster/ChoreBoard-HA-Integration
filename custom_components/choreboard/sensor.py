"""Sensor platform for ChoreBoard integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ChoreboardCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ChoreBoard sensor entities."""
    coordinator: ChoreboardCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    # Create system-wide sensors
    entities.append(ChoreboardOutstandingSensor(coordinator))
    entities.append(ChoreboardLateSensor(coordinator))
    entities.append(ChoreboardPoolSensor(coordinator))
    entities.append(ChoreboardLeaderboardSensor(coordinator, "weekly"))
    entities.append(ChoreboardLeaderboardSensor(coordinator, "alltime"))

    # Create per-user sensors
    for username in coordinator.monitored_users:
        # "My Chores" - all chores for the user
        entities.append(ChoreboardMyChoresSensor(coordinator, username))
        # "My Immediate Chores" - only chores not marked as "Complete Later"
        entities.append(ChoreboardMyImmediateChoresSensor(coordinator, username))

    async_add_entities(entities)


class ChoreboardOutstandingSensor(
    CoordinatorEntity[ChoreboardCoordinator], SensorEntity
):
    """Sensor for outstanding (incomplete, non-overdue) chores."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:clipboard-list-outline"

    def __init__(self, coordinator: ChoreboardCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_outstanding"
        self._attr_name = "Outstanding Chores"

    @property
    def native_value(self) -> int:
        """Return the number of outstanding chores."""
        chores = self.coordinator.data.get("outstanding_chores", [])
        return len(chores)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        chores = self.coordinator.data.get("outstanding_chores", [])

        # Build list of chore details
        chore_list = []
        for chore in chores:
            chore_info = {
                "id": chore.get("id"),
                "name": chore.get("chore", {}).get("name", "Unknown"),
                "assignee": self._format_assignee(chore.get("assigned_to")),
                "due_date": chore.get("due_at"),
                "points": chore.get(
                    "points_value", chore.get("chore", {}).get("points", 0)
                ),
                "is_pool": chore.get("chore", {}).get("is_pool", False),
            }
            chore_list.append(chore_info)

        return {
            "chores": chore_list,
            "count": len(chores),
        }

    def _format_assignee(self, assigned_to: Any) -> str:
        """Format assignee for display."""
        if assigned_to is None:
            return "Unassigned"
        if isinstance(assigned_to, dict):
            username = assigned_to.get("username", "Unknown")
            return assigned_to.get("display_name", username) or "Unknown"
        return str(assigned_to)


class ChoreboardLateSensor(CoordinatorEntity[ChoreboardCoordinator], SensorEntity):
    """Sensor for late/overdue chores."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:alert-circle-outline"

    def __init__(self, coordinator: ChoreboardCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_late"
        self._attr_name = "Late Chores"

    @property
    def native_value(self) -> int:
        """Return the number of late chores."""
        chores = self.coordinator.data.get("late_chores", [])
        return len(chores)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        chores = self.coordinator.data.get("late_chores", [])

        chore_list = []
        for chore in chores:
            chore_info = {
                "id": chore.get("id"),
                "name": chore.get("chore", {}).get("name", "Unknown"),
                "assignee": self._format_assignee(chore.get("assigned_to")),
                "due_date": chore.get("due_at"),
                "points": chore.get(
                    "points_value", chore.get("chore", {}).get("points", 0)
                ),
                "is_overdue": chore.get("is_overdue", True),
            }
            chore_list.append(chore_info)

        return {
            "chores": chore_list,
            "count": len(chores),
        }

    def _format_assignee(self, assigned_to: Any) -> str:
        """Format assignee for display."""
        if assigned_to is None:
            return "Unassigned"
        if isinstance(assigned_to, dict):
            username = assigned_to.get("username", "Unknown")
            return assigned_to.get("display_name", username) or "Unknown"
        return str(assigned_to)


class ChoreboardPoolSensor(CoordinatorEntity[ChoreboardCoordinator], SensorEntity):
    """Sensor for pool chores (unassigned chores available for claiming)."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:pool"

    def __init__(self, coordinator: ChoreboardCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_pool"
        self._attr_name = "Pool Chores"

    @property
    def native_value(self) -> int:
        """Return the number of pool chores."""
        chores = self.coordinator.data.get("pool_chores", [])
        return len(chores)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        chores = self.coordinator.data.get("pool_chores", [])

        chore_list = []
        for chore in chores:
            chore_info = {
                "id": chore.get("id"),
                "name": chore.get("chore", {}).get("name", "Unknown"),
                "due_date": chore.get("due_at"),
                "points": chore.get(
                    "points_value", chore.get("chore", {}).get("points", 0)
                ),
                "description": chore.get("chore", {}).get("description", ""),
                "status": chore.get("status", "POOL"),
            }
            chore_list.append(chore_info)

        return {
            "chores": chore_list,
            "count": len(chores),
        }


class ChoreboardMyChoresSensor(CoordinatorEntity[ChoreboardCoordinator], SensorEntity):
    """Sensor for a specific user's chores."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:account-check-outline"

    def __init__(self, coordinator: ChoreboardCoordinator, username: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._username = username
        self._attr_unique_id = f"{DOMAIN}_my_chores_{username}"
        self._attr_name = f"{username} - My Chores"

    @property
    def native_value(self) -> int:
        """Return the number of chores for this user."""
        my_chores = self.coordinator.data.get("my_chores", {})
        chores = my_chores.get(self._username, [])
        return len(chores)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        my_chores = self.coordinator.data.get("my_chores", {})
        chores = my_chores.get(self._username, [])

        chore_list = []
        for chore in chores:
            chore_info = {
                "id": chore.get("id"),
                "name": chore.get("chore", {}).get("name", "Unknown"),
                "due_date": chore.get("due_at"),
                "points": chore.get(
                    "points_value", chore.get("chore", {}).get("points", 0)
                ),
                "is_overdue": chore.get("is_overdue", False),
                "status": chore.get("status", "unknown"),
            }
            chore_list.append(chore_info)

        return {
            "username": self._username,
            "chores": chore_list,
            "count": len(chores),
        }


class ChoreboardMyImmediateChoresSensor(
    CoordinatorEntity[ChoreboardCoordinator], SensorEntity
):
    """Sensor for a specific user's immediate chores (not marked as Complete Later)."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:clock-alert-outline"

    def __init__(self, coordinator: ChoreboardCoordinator, username: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._username = username
        self._attr_unique_id = f"{DOMAIN}_my_immediate_chores_{username}"
        self._attr_name = f"{username} - My Immediate Chores"

    @property
    def native_value(self) -> int:
        """Return the number of immediate chores for this user."""
        my_chores = self.coordinator.data.get("my_chores", {})
        chores = my_chores.get(self._username, [])
        # Filter out chores marked as "complete_later"
        immediate_chores = [
            chore
            for chore in chores
            if not chore.get("chore", {}).get("complete_later", False)
        ]
        return len(immediate_chores)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        my_chores = self.coordinator.data.get("my_chores", {})
        chores = my_chores.get(self._username, [])
        # Filter out chores marked as "complete_later"
        immediate_chores = [
            chore
            for chore in chores
            if not chore.get("chore", {}).get("complete_later", False)
        ]

        chore_list = []
        for chore in immediate_chores:
            chore_info = {
                "id": chore.get("id"),
                "name": chore.get("chore", {}).get("name", "Unknown"),
                "due_date": chore.get("due_at"),
                "points": chore.get(
                    "points_value", chore.get("chore", {}).get("points", 0)
                ),
                "is_overdue": chore.get("is_overdue", False),
                "status": chore.get("status", "unknown"),
                "complete_later": chore.get("chore", {}).get("complete_later", False),
            }
            chore_list.append(chore_info)

        return {
            "username": self._username,
            "chores": chore_list,
            "count": len(immediate_chores),
            "total_chores": len(chores),
            "complete_later_chores": len(chores) - len(immediate_chores),
        }


class ChoreboardLeaderboardSensor(
    CoordinatorEntity[ChoreboardCoordinator], SensorEntity
):
    """Sensor for leaderboard data."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:trophy-outline"

    def __init__(
        self, coordinator: ChoreboardCoordinator, leaderboard_type: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._leaderboard_type = leaderboard_type
        self._attr_unique_id = f"{DOMAIN}_leaderboard_{leaderboard_type}"
        self._attr_name = f"Leaderboard - {leaderboard_type.capitalize()}"

    @property
    def native_value(self) -> int:
        """Return the number of users on the leaderboard."""
        key = f"leaderboard_{self._leaderboard_type}"
        leaderboard = self.coordinator.data.get(key, [])
        return len(leaderboard)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        key = f"leaderboard_{self._leaderboard_type}"
        leaderboard = self.coordinator.data.get(key, [])

        user_list = []
        for idx, entry in enumerate(leaderboard, start=1):
            # Handle both direct user objects and nested user objects
            user_data = entry.get("user", entry)

            user_info = {
                "rank": idx,
                "username": user_data.get("username", "Unknown"),
                "display_name": user_data.get(
                    "display_name", user_data.get("username", "Unknown")
                ),
                "points": user_data.get(
                    "weekly_points"
                    if self._leaderboard_type == "weekly"
                    else "all_time_points",
                    0,
                ),
            }
            user_list.append(user_info)

        return {
            "type": self._leaderboard_type,
            "users": user_list,
            "count": len(leaderboard),
        }
