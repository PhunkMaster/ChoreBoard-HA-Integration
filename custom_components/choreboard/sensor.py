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


def format_users_for_attributes(
    coordinator_data: dict[str, Any],
) -> list[dict[str, Any]]:
    """Format users data for sensor attributes.

    Args:
        coordinator_data: The coordinator's data dictionary

    Returns:
        List of formatted user dictionaries
    """
    users = coordinator_data.get("users", [])
    user_list = []

    for user in users:
        user_info = {
            "id": user.get("id"),
            "username": user.get("username", "Unknown"),
            "display_name": user.get("display_name", user.get("username", "Unknown")),
            "first_name": user.get("first_name", ""),
            "can_be_assigned": user.get("can_be_assigned", True),
            "eligible_for_points": user.get("eligible_for_points", True),
            "weekly_points": str(user.get("weekly_points", 0)),
            "all_time_points": str(user.get("all_time_points", 0)),
        }

        if "claims_today" in user:
            user_info["claims_today"] = user.get("claims_today", 0)

        user_list.append(user_info)

    return user_list


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
    entities.append(ChoreboardChoreBreakdownSensor(coordinator))
    entities.append(ChoreboardCompletionHistorySensor(coordinator))
    entities.append(ChoreboardPendingArcadeSensor(coordinator))
    entities.append(ChoreboardLeaderboardSensor(coordinator, "weekly"))
    entities.append(ChoreboardLeaderboardSensor(coordinator, "alltime"))
    entities.append(ChoreboardUsersSensor(coordinator))

    # Create chore leaderboard sensors (arcade mode)
    chore_leaderboards = coordinator.data.get("chore_leaderboards", [])
    for chore_lb in chore_leaderboards:
        chore_id = chore_lb.get("chore_id")
        chore_name = chore_lb.get("chore_name")
        if chore_id and chore_name:
            entities.append(
                ChoreboardChoreLeaderboardSensor(coordinator, chore_id, chore_name)
            )

    # Create per-user sensors
    for username in coordinator.monitored_users:
        # "My Chores" - all chores for the user
        entities.append(ChoreboardMyChoresSensor(coordinator, username))
        # "My Immediate Chores" - only chores not marked as "Complete Later"
        entities.append(ChoreboardMyImmediateChoresSensor(coordinator, username))
        # "Weekly Points" - weekly points for the user
        entities.append(ChoreboardUserWeeklyPointsSensor(coordinator, username))
        # "All-Time Points" - all-time points for the user
        entities.append(ChoreboardUserAllTimePointsSensor(coordinator, username))

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

            # Add last completion information if available
            last_completion = chore.get("last_completion")
            if last_completion:
                chore_info["last_completed_by"] = (
                    last_completion.get("completed_by", {}).get("display_name")
                    or last_completion.get("completed_by", {}).get("username")
                    or "Unknown"
                )
                chore_info["last_completed_at"] = last_completion.get("completed_at")
                chore_info["was_late"] = last_completion.get("was_late", False)
                # Add helpers if any
                helpers = last_completion.get("helpers", [])
                if helpers:
                    helper_names = [
                        h.get("display_name") or h.get("username") or "Unknown"
                        for h in helpers
                    ]
                    chore_info["helpers"] = helper_names

            chore_list.append(chore_info)

        return {
            "chores": chore_list,
            "count": len(chores),
            "points_label": self.coordinator.data.get("points_label", "points"),
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

            # Add last completion information if available
            last_completion = chore.get("last_completion")
            if last_completion:
                chore_info["last_completed_by"] = (
                    last_completion.get("completed_by", {}).get("display_name")
                    or last_completion.get("completed_by", {}).get("username")
                    or "Unknown"
                )
                chore_info["last_completed_at"] = last_completion.get("completed_at")
                chore_info["was_late"] = last_completion.get("was_late", False)
                # Add helpers if any
                helpers = last_completion.get("helpers", [])
                if helpers:
                    helper_names = [
                        h.get("display_name") or h.get("username") or "Unknown"
                        for h in helpers
                    ]
                    chore_info["helpers"] = helper_names

            chore_list.append(chore_info)

        return {
            "chores": chore_list,
            "count": len(chores),
            "points_label": self.coordinator.data.get("points_label", "points"),
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

            # Add last completion information if available
            last_completion = chore.get("last_completion")
            if last_completion:
                chore_info["last_completed_by"] = (
                    last_completion.get("completed_by", {}).get("display_name")
                    or last_completion.get("completed_by", {}).get("username")
                    or "Unknown"
                )
                chore_info["last_completed_at"] = last_completion.get("completed_at")
                chore_info["was_late"] = last_completion.get("was_late", False)
                # Add helpers if any
                helpers = last_completion.get("helpers", [])
                if helpers:
                    helper_names = [
                        h.get("display_name") or h.get("username") or "Unknown"
                        for h in helpers
                    ]
                    chore_info["helpers"] = helper_names

            chore_list.append(chore_info)

        return {
            "chores": chore_list,
            "count": len(chores),
            "points_label": self.coordinator.data.get("points_label", "points"),
        }


class ChoreboardChoreBreakdownSensor(
    CoordinatorEntity[ChoreboardCoordinator], SensorEntity
):
    """Sensor for pool vs assigned chore breakdown statistics."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:chart-pie"

    def __init__(self, coordinator: ChoreboardCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_chore_breakdown"
        self._attr_name = "Chore Breakdown"

    @property
    def native_value(self) -> int:
        """Return the total number of chores."""
        outstanding = self.coordinator.data.get("outstanding_chores", [])
        late = self.coordinator.data.get("late_chores", [])
        # Combine and deduplicate by chore ID
        all_chores = {chore.get("id"): chore for chore in outstanding + late}
        return len(all_chores)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        outstanding = self.coordinator.data.get("outstanding_chores", [])
        late = self.coordinator.data.get("late_chores", [])
        pool = self.coordinator.data.get("pool_chores", [])

        # Combine and deduplicate by chore ID
        all_chores = {chore.get("id"): chore for chore in outstanding + late}
        total = len(all_chores)

        # Count pool chores
        pool_count = len(pool)

        # Count assigned chores (non-pool chores)
        assigned_count = total - pool_count

        # Calculate percentages
        pool_pct = round((pool_count / total * 100), 1) if total > 0 else 0
        assigned_pct = round((assigned_count / total * 100), 1) if total > 0 else 0

        # Break down by status
        status_counts: dict[str, int] = {}
        for chore in all_chores.values():
            status = chore.get("status", "UNKNOWN")
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_chores": total,
            "pool_chores": pool_count,
            "assigned_chores": assigned_count,
            "pool_percentage": pool_pct,
            "assigned_percentage": assigned_pct,
            "status_breakdown": status_counts,
            "outstanding_count": len(outstanding),
            "late_count": len(late),
            "points_label": self.coordinator.data.get("points_label", "points"),
        }


class ChoreboardCompletionHistorySensor(
    CoordinatorEntity[ChoreboardCoordinator], SensorEntity
):
    """Sensor for recent completion history."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:history"

    def __init__(self, coordinator: ChoreboardCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_completion_history"
        self._attr_name = "Completion History"

    @property
    def native_value(self) -> int:
        """Return the number of recent completions."""
        completions = self.coordinator.data.get("recent_completions", [])
        return len(completions)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        completions = self.coordinator.data.get("recent_completions", [])

        completion_list = []
        for completion in completions:
            chore_instance = completion.get("chore_instance", {})
            completed_by = completion.get("completed_by", {})
            shares = completion.get("shares", [])

            completion_info = {
                "id": completion.get("id"),
                "chore_name": chore_instance.get("chore", {}).get("name", "Unknown"),
                "completed_by": (
                    completed_by.get("display_name")
                    or completed_by.get("username")
                    or "Unknown"
                ),
                "completed_at": completion.get("completed_at"),
                "was_late": completion.get("was_late", False),
                "points": chore_instance.get(
                    "points_value", chore_instance.get("chore", {}).get("points", 0)
                ),
            }

            # Add helpers if any
            if shares:
                helper_names = []
                for share in shares:
                    user = share.get("user", {})
                    name = user.get("display_name") or user.get("username") or "Unknown"
                    points = share.get("points_awarded", 0)
                    helper_names.append({"name": name, "points": points})
                completion_info["helpers"] = helper_names

            completion_list.append(completion_info)

        return {
            "completions": completion_list,
            "count": len(completions),
            "points_label": self.coordinator.data.get("points_label", "points"),
        }


class ChoreboardPendingArcadeSensor(
    CoordinatorEntity[ChoreboardCoordinator], SensorEntity
):
    """Sensor for pending arcade sessions awaiting judge approval."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:gavel"

    def __init__(self, coordinator: ChoreboardCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_pending_arcade"
        self._attr_name = "Pending Arcade Sessions"

    @property
    def native_value(self) -> int:
        """Return the number of pending arcade sessions."""
        sessions = self.coordinator.data.get("pending_arcade_sessions", [])
        return len(sessions)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        sessions = self.coordinator.data.get("pending_arcade_sessions", [])

        session_list = []
        for session in sessions:
            session_info = {
                "id": session.get("id"),
                "chore_id": session.get("chore_id"),
                "chore_name": session.get("chore_name", "Unknown"),
                "user_id": session.get("user_id"),
                "user_name": session.get("user_name", "Unknown"),
                "user_display_name": session.get("user_display_name", session.get("user_name", "Unknown")),
                "start_time": session.get("start_time"),
                "elapsed_seconds": session.get("elapsed_seconds", 0),
                "status": session.get("status", "judging"),
            }
            session_list.append(session_info)

        return {
            "sessions": session_list,
            "count": len(sessions),
            "points_label": self.coordinator.data.get("points_label", "points"),
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

            # Add last completion information if available
            last_completion = chore.get("last_completion")
            if last_completion:
                chore_info["last_completed_by"] = (
                    last_completion.get("completed_by", {}).get("display_name")
                    or last_completion.get("completed_by", {}).get("username")
                    or "Unknown"
                )
                chore_info["last_completed_at"] = last_completion.get("completed_at")
                chore_info["was_late"] = last_completion.get("was_late", False)
                # Add helpers if any
                helpers = last_completion.get("helpers", [])
                if helpers:
                    helper_names = [
                        h.get("display_name") or h.get("username") or "Unknown"
                        for h in helpers
                    ]
                    chore_info["helpers"] = helper_names

            chore_list.append(chore_info)

        # Get arcade session for this user if any
        arcade_sessions = self.coordinator.data.get("arcade_sessions", {})
        arcade_session = arcade_sessions.get(self._username)

        attributes = {
            "username": self._username,
            "chores": chore_list,
            "count": len(chores),
            "points_label": self.coordinator.data.get("points_label", "points"),
        }

        # Add arcade session if active
        if arcade_session:
            attributes["arcade_session"] = arcade_session

        return attributes


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

            # Add last completion information if available
            last_completion = chore.get("last_completion")
            if last_completion:
                chore_info["last_completed_by"] = (
                    last_completion.get("completed_by", {}).get("display_name")
                    or last_completion.get("completed_by", {}).get("username")
                    or "Unknown"
                )
                chore_info["last_completed_at"] = last_completion.get("completed_at")
                chore_info["was_late"] = last_completion.get("was_late", False)
                # Add helpers if any
                helpers = last_completion.get("helpers", [])
                if helpers:
                    helper_names = [
                        h.get("display_name") or h.get("username") or "Unknown"
                        for h in helpers
                    ]
                    chore_info["helpers"] = helper_names

            chore_list.append(chore_info)

        return {
            "username": self._username,
            "chores": chore_list,
            "count": len(immediate_chores),
            "total_chores": len(chores),
            "complete_later_chores": len(chores) - len(immediate_chores),
            "points_label": self.coordinator.data.get("points_label", "points"),
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
            "points_label": self.coordinator.data.get("points_label", "points"),
        }


class ChoreboardChoreLeaderboardSensor(
    CoordinatorEntity[ChoreboardCoordinator], SensorEntity
):
    """Sensor for a specific chore's leaderboard (arcade mode)."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:timer-outline"

    def __init__(
        self, coordinator: ChoreboardCoordinator, chore_id: int, chore_name: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._chore_id = chore_id
        self._chore_name = chore_name
        self._attr_unique_id = f"{DOMAIN}_chore_leaderboard_{chore_id}"
        self._attr_name = f"Arcade: {chore_name}"

    @property
    def native_value(self) -> int:
        """Return the number of high scores for this chore."""
        chore_leaderboards = self.coordinator.data.get("chore_leaderboards", [])
        for chore_lb in chore_leaderboards:
            if chore_lb.get("chore_id") == self._chore_id:
                scores = chore_lb.get("high_scores", [])
                return len(scores)
        return 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        chore_leaderboards = self.coordinator.data.get("chore_leaderboards", [])

        for chore_lb in chore_leaderboards:
            if chore_lb.get("chore_id") == self._chore_id:
                high_scores = chore_lb.get("high_scores", [])

                score_list = []
                for score in high_scores:
                    user = score.get("user", {})
                    score_info = {
                        "rank": score.get("rank"),
                        "username": user.get("username", "Unknown"),
                        "display_name": user.get(
                            "display_name", user.get("username", "Unknown")
                        ),
                        "time_seconds": score.get("time_seconds"),
                        "time_formatted": score.get("time_formatted"),
                        "achieved_at": score.get("achieved_at"),
                    }
                    score_list.append(score_info)

                return {
                    "chore_id": self._chore_id,
                    "chore_name": self._chore_name,
                    "scores": score_list,
                    "count": len(high_scores),
                    "points_label": self.coordinator.data.get("points_label", "points"),
                }

        return {
            "chore_id": self._chore_id,
            "chore_name": self._chore_name,
            "scores": [],
            "count": 0,
            "points_label": self.coordinator.data.get("points_label", "points"),
        }


class ChoreboardUserWeeklyPointsSensor(
    CoordinatorEntity[ChoreboardCoordinator], SensorEntity
):
    """Sensor for a user's weekly points."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:medal-outline"
    _attr_native_unit_of_measurement = "points"

    def __init__(self, coordinator: ChoreboardCoordinator, username: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._username = username
        self._attr_unique_id = f"{DOMAIN}_weekly_points_{username}"
        self._attr_name = f"{username} - Weekly Points"

    @property
    def native_value(self) -> float:
        """Return the user's weekly points."""
        users = self.coordinator.data.get("users", [])
        for user in users:
            if user.get("username") == self._username:
                return float(user.get("weekly_points", 0))
        return 0.0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        users = self.coordinator.data.get("users", [])
        for user in users:
            if user.get("username") == self._username:
                return {
                    "username": self._username,
                    "display_name": user.get("display_name", self._username),
                    "points": float(user.get("weekly_points", 0)),
                    "claims_today": user.get("claims_today", 0),
                    "points_label": self.coordinator.data.get("points_label", "points"),
                }
        return {
            "username": self._username,
            "points": 0.0,
            "points_label": self.coordinator.data.get("points_label", "points"),
        }


class ChoreboardUserAllTimePointsSensor(
    CoordinatorEntity[ChoreboardCoordinator], SensorEntity
):
    """Sensor for a user's all-time points."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:trophy"
    _attr_native_unit_of_measurement = "points"

    def __init__(self, coordinator: ChoreboardCoordinator, username: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._username = username
        self._attr_unique_id = f"{DOMAIN}_alltime_points_{username}"
        self._attr_name = f"{username} - All-Time Points"

    @property
    def native_value(self) -> float:
        """Return the user's all-time points."""
        users = self.coordinator.data.get("users", [])
        for user in users:
            if user.get("username") == self._username:
                return float(user.get("all_time_points", 0))
        return 0.0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        users = self.coordinator.data.get("users", [])
        for user in users:
            if user.get("username") == self._username:
                return {
                    "username": self._username,
                    "display_name": user.get("display_name", self._username),
                    "points": float(user.get("all_time_points", 0)),
                    "weekly_points": float(user.get("weekly_points", 0)),
                    "points_label": self.coordinator.data.get("points_label", "points"),
                }
        return {
            "username": self._username,
            "points": 0.0,
            "points_label": self.coordinator.data.get("points_label", "points"),
        }


class ChoreboardUsersSensor(CoordinatorEntity[ChoreboardCoordinator], SensorEntity):
    """Sensor for all ChoreBoard users."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:account-group"

    def __init__(self, coordinator: ChoreboardCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_users"
        self._attr_name = "Users"

    @property
    def native_value(self) -> int:
        """Return the number of users."""
        users = self.coordinator.data.get("users", [])
        return len(users)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        user_list = format_users_for_attributes(self.coordinator.data)

        return {
            "users": user_list,
            "count": len(user_list),
            "points_label": self.coordinator.data.get("points_label", "points"),
        }
