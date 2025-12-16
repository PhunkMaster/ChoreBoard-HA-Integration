# ChoreBoard Integration: Add Users Data to Sensor Attributes

## Executive Summary

**Task**: Enable ChoreBoard Card pool chores feature by exposing users data through Home Assistant sensor attributes.

**Problem**: Card shows "Unable to load users list" error when clicking Claim/Complete buttons on pool chores.

**Solution**: Add `users` array to all ChoreBoard sensor attributes + create dedicated Users sensor.

**Estimated Time**: 2.5-3 hours for junior engineer

---

## Background

### Current State

- ✅ Users data IS already fetched from ChoreBoard API (`/api/users/`)
- ✅ Users data IS already stored in coordinator (`coordinator.data["users"]`)
- ❌ Users data is NOT exposed in sensor attributes
- ❌ Card cannot access users for selection dialogs

### Requirements

1. Add `users` array to ALL ChoreBoard sensors
2. Create new dedicated `sensor.choreboard_users` sensor
3. Verify API returns user `id` field (critical for service calls)

---

## Implementation Plan

### Phase 1: Verify API Data Structure (15-20 minutes)

**Objective**: Confirm `/api/users/` endpoint returns user `id` field

#### Steps

1. **Check Django API Code**
   - Locate `/api/users/` endpoint view
   - Check serializer for user data
   - Verify required fields:
     - `id` (integer, **CRITICAL**)
     - `username` (string)
     - `display_name` (string)
     - `first_name` (string)
     - `can_be_assigned` (boolean)
     - `eligible_for_points` (boolean)
     - `weekly_points` (decimal/string)
     - `all_time_points` (decimal/string)
     - `claims_today` (integer, optional)

2. **Test API Manually**
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" \
        https://your-choreboard-api.com/api/users/
   ```

3. **Expected Response**
   ```json
   [
     {
       "id": 1,
       "username": "ash",
       "display_name": "Ash",
       "first_name": "Ash",
       "can_be_assigned": true,
       "eligible_for_points": true,
       "weekly_points": "25.00",
       "all_time_points": "150.00",
       "claims_today": 2
     }
   ]
   ```

4. **If `id` Missing**
   - ⚠️ **BLOCKER**: Must update Django serializer first
   - Card service calls require `assign_to_user_id` and `completed_by_user_id`
   - Deploy backend before continuing

---

### Phase 2: Create Dedicated Users Sensor (30-40 minutes)

**File**: `C:\Users\pmagalios\PycharmProjects\ChoreBoard-HA-Integration\custom_components\choreboard\sensor.py`

#### Step 1: Add Sensor Class

Insert after line 757 (after `ChoreboardUserAllTimePointsSensor`):

```python
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
        users = self.coordinator.data.get("users", [])

        user_list = []
        for user in users:
            user_info = {
                "id": user.get("id"),  # CRITICAL: Must be present
                "username": user.get("username", "Unknown"),
                "display_name": user.get("display_name", user.get("username", "Unknown")),
                "first_name": user.get("first_name", ""),
                "can_be_assigned": user.get("can_be_assigned", True),
                "eligible_for_points": user.get("eligible_for_points", True),
                "weekly_points": str(user.get("weekly_points", 0)),
                "all_time_points": str(user.get("all_time_points", 0)),
            }

            # Optional field
            if "claims_today" in user:
                user_info["claims_today"] = user.get("claims_today", 0)

            user_list.append(user_info)

        return {
            "users": user_list,
            "count": len(user_list),
        }
```

#### Step 2: Register Sensor

Find `async_setup_entry` (around line 80-120) and add:

```python
# Add users sensor
entities.append(ChoreboardUsersSensor(coordinator))
```

**Location**: After pool chores sensor, before per-user sensor loop

#### Step 3: Test

- Restart Home Assistant
- Developer Tools → States → Search `sensor.choreboard_users`
- Verify: State shows user count
- Verify: Attributes contain `users` array with all fields

---

### Phase 3: Add Users to All Existing Sensors (45-60 minutes)

**File**: `C:\Users\pmagalios\PycharmProjects\ChoreBoard-HA-Integration\custom_components\choreboard\sensor.py`

#### Critical Sensors to Update

1. `ChoreboardPoolSensor` (lines 210-270) - **HIGHEST PRIORITY**
2. `ChoreboardMyChoresSensor` (lines 399-463) - **HIGH PRIORITY**
3. `ChoreboardMyImmediateChoresSensor` (lines 466-560) - **HIGH PRIORITY**
4. `ChoreboardOutstandingSensor` (lines 120-180)
5. `ChoreboardLateSensor` (lines 180-210)
6. `ChoreboardChoreBreakdownSensor` (lines 273-370)

#### Implementation Pattern

**Step 1: Add Helper Function**

Insert around line 100 (before first sensor class):

```python
def format_users_for_attributes(coordinator_data: dict[str, Any]) -> list[dict[str, Any]]:
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
```

**Step 2: Update Each Sensor**

For EACH sensor in the list above, update `extra_state_attributes`:

**Before**:
```python
@property
def extra_state_attributes(self) -> dict[str, Any]:
    """Return additional state attributes."""
    chores = self.coordinator.data.get("pool_chores", [])

    # ... existing logic ...

    return {
        "chores": chore_list,
        "count": len(chores),
    }
```

**After**:
```python
@property
def extra_state_attributes(self) -> dict[str, Any]:
    """Return additional state attributes."""
    chores = self.coordinator.data.get("pool_chores", [])

    # ... existing logic ...

    return {
        "chores": chore_list,
        "count": len(chores),
        "users": format_users_for_attributes(self.coordinator.data),  # NEW
    }
```

**Example for Pool Sensor** (lines 228-270):

Find the return statement in `ChoreboardPoolSensor.extra_state_attributes` and change:

```python
# OLD
return {
    "chores": chore_list,
    "count": len(chores),
}

# NEW
return {
    "chores": chore_list,
    "count": len(chores),
    "users": format_users_for_attributes(self.coordinator.data),
}
```

Repeat for all 6 sensors.

---

### Phase 4: Testing (30-45 minutes)

#### Test Checklist

- [ ] **Restart Home Assistant** (Settings → System → Restart)

- [ ] **Verify Users Sensor**
  - Developer Tools → States → `sensor.choreboard_users`
  - State = user count
  - Attributes contain `users` array
  - Each user has `id` field

- [ ] **Verify Pool Sensor**
  - Find `sensor.choreboard_pool`
  - Attributes contain `users` array
  - Structure matches Users sensor

- [ ] **Verify My Chores Sensors**
  - Find `sensor.ash_my_chores` (or similar)
  - Attributes contain `users` array
  - Structure matches

- [ ] **Test Card - Claim Dialog**
  - Open dashboard with pool chores
  - Click "Claim" on pool chore
  - **Expected**: Dialog shows user list
  - **Previous**: Error "Unable to load users list"
  - Select user → Verify claim succeeds

- [ ] **Test Card - Complete Dialog**
  - Click "Complete" on pool chore
  - **Expected**: Two-section dialog:
    1. "Who completed?" (required, single-select)
    2. "Who helped?" (optional, multi-select)
  - Select completer + helpers
  - Verify completion succeeds

- [ ] **Check Logs**
  - Settings → System → Logs
  - No ChoreBoard errors

---

### Phase 5: Documentation (15-20 minutes)

#### File 1: CLAUDE.md

`C:\Users\pmagalios\PycharmProjects\ChoreBoard-HA-Integration\CLAUDE.md`

Add new section:

```markdown
## Sensor Attributes

All ChoreBoard sensors include a `users` array in their attributes for use by the ChoreBoard Card's user selection dialogs.

### Users Array Structure

```python
"users": [
    {
        "id": 1,                       # User ID for API calls
        "username": "ash",             # Login username
        "display_name": "Ash",         # Display name
        "first_name": "Ash",           # First name
        "can_be_assigned": true,       # Can receive assignments
        "eligible_for_points": true,   # Can earn points
        "weekly_points": "25.00",      # This week's points
        "all_time_points": "150.00",   # Total points ever
        "claims_today": 2              # Claims made today (optional)
    }
]
```

### Dedicated Users Sensor

`sensor.choreboard_users` provides a dedicated sensor for accessing all users:
- **State**: Number of users
- **Attributes**:
  - `users`: Full users array
  - `count`: Number of users

### Usage in Card

The ChoreBoard Card searches all ChoreBoard sensors for the `users` array when displaying user selection dialogs for pool chores. Having users in all sensors ensures the card can always find the data regardless of which sensor is configured.
```

#### File 2: README.md

`C:\Users\pmagalios\PycharmProjects\ChoreBoard-HA-Integration\README.md`

Add to Features section:
```markdown
- **User Selection Dialogs**: All sensors include users data for card user selection features
```

Add to sensor list:
```markdown
- `sensor.choreboard_users` - All ChoreBoard users with points and stats
```

#### File 3: CHANGELOG.md

`C:\Users\pmagalios\PycharmProjects\ChoreBoard-HA-Integration\CHANGELOG.md`

Add entry:
```markdown
## [vX.X.X] - YYYY-MM-DD

### Added
- New `sensor.choreboard_users` sensor exposing all ChoreBoard users
- `users` array added to all ChoreBoard sensor attributes for card compatibility
- Users data includes `id`, `username`, `display_name`, and points for user selection dialogs

### Changed
- All sensor attributes now include full users list for ChoreBoard Card pool chores feature
```

---

### Phase 6: Code Review Checklist (10 minutes)

Before submitting PR:

- [ ] API returns user `id` field (Phase 1 verified)
- [ ] `ChoreboardUsersSensor` class created
- [ ] New sensor registered in `async_setup_entry`
- [ ] `format_users_for_attributes` helper function created
- [ ] All 6+ sensors updated with `users` in attributes
- [ ] Users array has required fields: id, username, display_name
- [ ] Users array properly formatted (id=int, points=string)
- [ ] Tested in Developer Tools → States
- [ ] Tested with ChoreBoard Card dialogs
- [ ] Documentation updated (CLAUDE.md, README.md, CHANGELOG.md)
- [ ] No errors in Home Assistant logs

---

## Success Criteria

✅ **New sensor exists**: `sensor.choreboard_users` in Home Assistant

✅ **Users in attributes**: All ChoreBoard sensors have `users` array

✅ **Card Claim works**: Pool chores show user selection dialog

✅ **Card Complete works**: Pool chores show user + helper selection

✅ **No errors**: Clean Home Assistant logs

✅ **Documentation complete**: All docs updated

---

## Common Pitfalls

### 1. Missing User ID
**Problem**: Users don't have `id` field
**Impact**: Service calls fail - card cannot claim/complete chores
**Solution**: Update Django serializer FIRST, then proceed

### 2. Type Inconsistency
**Problem**: Points as numbers (25.0) instead of strings ("25.00")
**Impact**: Type mismatches in card
**Solution**: Always use `str(user.get("weekly_points", 0))`

### 3. Forgetting Sensors
**Problem**: Only updating 3 of 6 sensors
**Impact**: Card fails when configured with non-updated sensor
**Solution**: Update ALL sensors:
- OutstandingSensor
- LateSensor
- PoolSensor ⚠️
- ChoreBreakdownSensor
- MyChoresSensor ⚠️
- MyImmediateChoresSensor ⚠️

### 4. Code Duplication
**Problem**: Copy/pasting user formatting logic 6+ times
**Impact**: Hard to maintain, inconsistent formatting
**Solution**: Use `format_users_for_attributes` helper

### 5. Testing Only in Dev Tools
**Problem**: Assuming Dev Tools test is sufficient
**Impact**: Card may still fail with real usage
**Solution**: Always test with actual ChoreBoard Card

---

## Questions to Ask If Stuck

1. **"What fields does `/api/users/` return?"**
   → Ask backend developer

2. **"Where is `async_setup_entry`?"**
   → Line 80-120 in sensor.py

3. **"How do I restart Home Assistant?"**
   → Settings → System → Restart

4. **"How do I clear browser cache?"**
   → Hard refresh: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)

5. **"Why is `id` field critical?"**
   → Card service calls use `assign_to_user_id` and `completed_by_user_id`

---

## Files to Modify

### Primary Implementation

1. **sensor.py**
   `C:\Users\pmagalios\PycharmProjects\ChoreBoard-HA-Integration\custom_components\choreboard\sensor.py`
   - Add helper function (line ~100)
   - Add ChoreboardUsersSensor class (line ~757)
   - Register sensor in async_setup_entry (line ~80-120)
   - Update 6+ sensors' extra_state_attributes methods

### Documentation

2. **CLAUDE.md**
   `C:\Users\pmagalios\PycharmProjects\ChoreBoard-HA-Integration\CLAUDE.md`
   - Add "Sensor Attributes" section

3. **README.md**
   `C:\Users\pmagalios\PycharmProjects\ChoreBoard-HA-Integration\README.md`
   - Update features list
   - Add users sensor to sensor list

4. **CHANGELOG.md**
   `C:\Users\pmagalios\PycharmProjects\ChoreBoard-HA-Integration\CHANGELOG.md`
   - Add changelog entry

### Backend (If Needed)

5. **Django API** (Backend Repository)
   - User serializer (if `id` field missing)
   - Deploy before proceeding

---

## Resources

- **Home Assistant Sensor Docs**: https://developers.home-assistant.io/docs/core/entity/sensor/
- **Coordinator Pattern**: https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
- **ChoreBoard Card**: https://github.com/PhunkMaster/ChoreBoard-HA-Card
- **ChoreBoard Integration**: https://github.com/PhunkMaster/ChoreBoard-HA-Integration

---

## Timeline

| Phase | Task | Time |
|-------|------|------|
| 1 | API Verification | 15-20 min |
| 2 | Users Sensor | 30-40 min |
| 3 | Update All Sensors | 45-60 min |
| 4 | Testing | 30-45 min |
| 5 | Documentation | 15-20 min |
| 6 | Code Review | 10 min |
| **Total** | | **2.5-3 hours** |

---

## Contact

If you have questions about this implementation:

1. **ChoreBoard Card Issues**: https://github.com/PhunkMaster/ChoreBoard-HA-Card/issues
2. **ChoreBoard Integration Issues**: https://github.com/PhunkMaster/ChoreBoard-HA-Integration/issues
3. **Backend API Questions**: Contact backend development team

---

*Generated with Claude Code for handoff to junior engineer*
*Last Updated: 2025-12-16*
