# CLAUDE.md

This file provides guidance to Claude Code when working with the ChoreBoard Home Assistant integration. **Assumes familiarity with Home Assistant integration development.**

## 1. Project Status & Overview

**Current Version**: v1.4.0 (manifest shows 0.1.0, update needed)
**Integration Type**: Service (cloud-based API)
**Target HA Version**: 2024.1.0+
**Domain**: `choreboard`

**Feature Completeness**:
- 13 sensor types (9 system-wide, 4 per-user)
- 9 services (3 core + 6 arcade mode)
- HMAC-SHA256 authentication with 23-hour token caching
- Two-step configuration flow with 3-method user discovery
- Menu-based options flow (scan interval, monitored users, credentials)
- Arcade mode with judge approval system (v1.4.0)
- Smart polling with configurable scan interval (10-300s)
- Immediate refresh after service calls

## 2. Local Development Environment

**IMPORTANT**: ChoreBoard backend is at `../ChoreBoard` (sibling directory) for development.

**Development Workflow**:
- Modify ChoreBoard API endpoints in `../ChoreBoard` as needed
- Test integration against local ChoreBoard instance
- API changes must be coordinated between both repositories

**Production Note**: Users configure their own ChoreBoard backend URL during integration setup. The `../ChoreBoard` location is development-only.

**Upstream Changes**: Document required API changes in `../ChoreBoard/downstream_integration_needs/` for backend team coordination.

## 3. Critical Implementation Patterns

### HMAC-SHA256 Authentication

**Token Format**: `username:timestamp:signature`
- `timestamp`: Integer Unix timestamp
- `signature`: HMAC-SHA256 hex digest of `username:timestamp` using Django SECRET_KEY
- Header: `Authorization: Bearer {token}`

**Token Caching** (`api_client.py`):
- Tokens cached for 23 hours (before 24h expiry)
- Auto-regenerated on 401 responses
- Prevents token expiration in production

### Date Filtering & Normalization

**Rule**: Only show chores due by today at 23:59:59
- Future chores (tomorrow+) filtered out
- Overdue chores included
- Today's chores included

**Datetime Format**: `YYYY-MM-DD HH:MM` (no seconds/microseconds)

**Implementation** (`coordinator.py`):
- `_is_due_today()`: Checks if chore is due by end of today
- `_normalize_datetime()`: Formats datetimes without seconds
- `_filter_chores_by_due_date()`: Applies filtering and normalization

### Pool Chore Detection

**Logic**: `status == "POOL"` OR (`is_pool == True` AND no assignee)
**Used by**: ChoreboardPoolSensor, claim_chore service, ChoreBoard Card
**Implementation**: `coordinator.py:201-210`

### Users Array Standard

**Only the `ChoreboardUsersSensor`** includes the `users` array in `extra_state_attributes`. Other sensors do not include user data to reduce data duplication.

**Structure**:
```python
{
    "id": 1,                       # REQUIRED for service calls
    "username": "ash",
    "display_name": "Ash",
    "first_name": "Ash",
    "can_be_assigned": True,
    "eligible_for_points": True,
    "weekly_points": "25.00",      # String format
    "all_time_points": "150.00",   # String format
    "claims_today": 2              # Optional
}
```

**Helper Function**: `format_users_for_attributes()` (`sensor.py:20-51`)

**Important**: To access user data, query the `sensor.choreboard_users` sensor attributes.

## 4. Sensor Reference

### System-Wide Sensors (9 sensors)

| Class | Entity ID | State | Key Attributes |
|-------|-----------|-------|----------------|
| `ChoreboardOutstandingSensor` | `sensor.choreboard_outstanding` | count | chores (list) |
| `ChoreboardLateSensor` | `sensor.choreboard_late` | count | chores (list) |
| `ChoreboardPoolSensor` | `sensor.choreboard_pool` | count | chores (list) |
| `ChoreboardChoreBreakdownSensor` | `sensor.choreboard_chore_breakdown` | count | breakdown (dict) |
| `ChoreboardCompletionHistorySensor` | `sensor.choreboard_completion_history` | count | completions (20 max) |
| `ChoreboardPendingArcadeSensor` | `sensor.choreboard_pending_arcade` | count | sessions (list) |
| `ChoreboardLeaderboardSensor` | `sensor.choreboard_leaderboard_{type}` | count | users (ranked list) |
| `ChoreboardChoreLeaderboardSensor` | `sensor.choreboard_arcade_{chore_name}` | count | scores (list) |
| `ChoreboardUsersSensor` | `sensor.choreboard_users` | count | users (array), count (int) |

**Note**: `{type}` = `weekly` or `alltime` for leaderboard sensors. Arcade leaderboard sensors created dynamically per chore.

### Per-User Sensors (4 types, created for each monitored user)

| Class | Entity ID | State | Key Attributes |
|-------|-----------|-------|----------------|
| `ChoreboardMyChoresSensor` | `sensor.{username}_my_chores` | count | chores (list) |
| `ChoreboardMyImmediateChoresSensor` | `sensor.{username}_my_immediate_chores` | count | chores (filtered) |
| `ChoreboardUserWeeklyPointsSensor` | `sensor.{username}_weekly_points` | points | username, points |
| `ChoreboardUserAllTimePointsSensor` | `sensor.{username}_alltime_points` | points | username, points |

**My Immediate Chores**: Filters out chores where `complete_later=True`

## 5. Service Reference

### Core Chore Management (3 services)

| Service | Parameters | Description |
|---------|------------|-------------|
| `choreboard.mark_complete` | `chore_id` (required), `helpers` (optional list), `completed_by_user_id` (optional) | Mark chore complete with optional helpers |
| `choreboard.claim_chore` | `chore_id` (required), `assign_to_user_id` (optional) | Claim pool chore for user |
| `choreboard.undo_completion` | `completion_id` (required) | Undo chore completion (admin only) |

### Arcade Mode (6 services, v1.4.0)

| Service | Parameters | Description |
|---------|------------|-------------|
| `choreboard.start_arcade` | `chore_id` (required), `user_id` (optional) | Start arcade timer |
| `choreboard.stop_arcade` | `chore_id` (required) | Stop arcade timer, await judgment |
| `choreboard.approve_arcade` | `chore_id` (required), `judge_id` (required), `notes` (optional) | Approve arcade completion |
| `choreboard.deny_arcade` | `chore_id` (required), `judge_id` (required), `notes` (optional) | Deny arcade completion |
| `choreboard.continue_arcade` | `chore_id` (required) | Resume arcade timer after denial |
| `choreboard.cancel_arcade` | `chore_id` (required) | Cancel arcade attempt, return to pool |

**All services trigger immediate coordinator refresh** via `async_refresh_immediately()`

**API Endpoints**: 16 total (8 core + 8 arcade)

## 6. Arcade Mode Workflow

**Service Sequence**:
1. **Start** → `start_arcade` → Timer begins
2. **Stop** → `stop_arcade` → Awaiting judgment
3. **Judge Decision**:
   - `approve_arcade` → Mark complete + record time
   - `deny_arcade` → Decision point
4. **After Denial**:
   - `continue_arcade` → Resume timer
   - `cancel_arcade` → Return to pool

**Leaderboard Sensors**: `ChoreboardChoreLeaderboardSensor` created per chore with arcade mode enabled
- Entity ID: `sensor.choreboard_arcade_{chore_name}`
- Tracks high scores (fastest completion times)

**Pending Arcade Sensor**: `ChoreboardPendingArcadeSensor` shows ALL arcade sessions awaiting judge approval
- Entity ID: `sensor.choreboard_pending_arcade`
- Unfiltered by monitored users - shows all pending sessions for any judge
- State: Count of pending sessions
- Attributes: List of sessions with id, chore info, user info, elapsed time, status

**Judge System**: Requires judge approval for completion, supports optional notes, `judge_id` parameter required

**API Endpoints** (`/api/arcade/*`): start, stop, approve, deny, continue, cancel, status, pending

## 7. Configuration Flows

### Initial Setup (2-step)

**Step 1 - Credentials**:
- Username (ChoreBoard username)
- Secret Key (Django SECRET_KEY for HMAC)
- URL (default: http://localhost:8000)
- Scan Interval (default: 30 seconds)

**Step 2 - User Selection**:
- Multi-select list of available users
- Creates "My Chores" and "My Immediate Chores" sensors per user

### Options Flow (menu-based, v1.3.0+)

**Three Menu Options**:
1. **Update Scan Interval**: Adjust polling frequency (10-300 seconds)
2. **Change Monitored Users**: Add/remove users with dynamic discovery
3. **Update Credentials**: Change URL, username, or secret_key

### User Discovery (3-method fallback)

**Primary**: `/api/users/` endpoint (v1.3.0+)
**Fallback 1**: Leaderboard data (`/api/leaderboard/`)
**Fallback 2**: Chore assignment data (outstanding/late chores)

**Implementation**: `config_flow.py:_discover_users()`

## 8. Data Update Strategy

**Scan Interval**: Configurable, default 30 seconds (10-300 range)
**Pattern**: DataUpdateCoordinator with single shared data fetch
**All sensors**: Subscribe to same coordinator for efficiency

**Immediate Refresh**: After service calls via `async_refresh_immediately()`
- Provides instant feedback to user actions
- Called by all 9 service handlers

**Date Filtering**: Applied during coordinator update (`_async_update_data`)
**Error Handling**: Automatic retry with exponential backoff

## 9. Testing Strategy

**Coverage Target**: >80% for all modified files

**Critical Test Areas**:
- Date filtering logic (`test_coordinator.py`)
- Datetime normalization
- Pool chore detection
- Users array in ChoreboardUsersSensor only (`test_sensors_new.py`)
- Absence of users array in other sensors (`test_sensors_new.py`)
- Service handlers (`test_services.py`)
- Arcade mode workflow
- 3-method user discovery

**Test Setup**: pytest with `pytest-homeassistant-custom-component`
**Async Tests**: Mark with `@pytest.mark.asyncio` and `@pytest.mark.enable_socket`

## 10. Branching & Development Workflow

### Semantic Versioning Branches

**Always use semver branch names**:
- `feature/X.Y.Z` - New features (minor version bump)
- `bugfix/X.Y.Z` - Bug fixes (patch version bump)
- `hotfix/X.Y.Z` - Critical fixes (patch version bump)

**Examples**:
- `feature/1.5.0` - Adding new sensor type
- `bugfix/1.4.1` - Fixing arcade mode issue

### Auto-Release Workflow

Merging semver-named branches to `main` automatically creates GitHub release via workflow.

### Upstream Coordination

When API changes are needed:
1. Document requirements in `../ChoreBoard/downstream_integration_needs/`
2. Implement API changes in `../ChoreBoard`
3. Update integration code to consume new endpoints
4. Test against local ChoreBoard instance

### Development Checklist

- [ ] Run tests: `pytest tests/ --cov`
- [ ] Type checking: `mypy custom_components/choreboard/`
- [ ] Linting: `ruff check . && ruff format .`
- [ ] Update CLAUDE.md if adding features
- [ ] Use semver branch naming
- [ ] Test with real HA instance (symlink to `~/.homeassistant/custom_components/`)
