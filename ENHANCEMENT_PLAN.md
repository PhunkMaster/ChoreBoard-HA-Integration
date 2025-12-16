# ChoreBoard Integration Enhancement Plan

**Date**: 2025-12-16
**Version**: 1.0
**Target Version**: 1.3.0

---

## Overview

This plan addresses three enhancement requirements for the ChoreBoard Home Assistant Integration:

1. **Smart Polling Strategy** - Immediate refresh after actions, configurable interval
2. **Options Flow** - Make integration settings reconfigurable without reinstalling
3. **User Picker Enhancement** - Expose all users during setup

---

## Enhancement 1: Smart Polling Strategy

### Current Behavior

**Problem**: Integration polls backend at fixed 30-second interval regardless of user actions
- User claims chore → waits up to 30s for UI update
- User completes chore → waits up to 30s for UI update
- Poor user experience with stale data

**Current Implementation** (`coordinator.py`):
```python
self.update_interval = timedelta(seconds=30)  # Fixed interval
```

### Target Behavior

**Desired**: Intelligent polling based on activity
- **After service call** (claim, complete, undo): Immediate refresh
- **No activity**: Poll every N seconds (configurable, default 30s)
- **Configurable interval**: User can adjust poll frequency

### Implementation Details

#### 1.1 Add Configuration Option

**File**: `const.py`

Add new constant:
```python
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 30  # seconds
```

#### 1.2 Update Config Flow

**File**: `config_flow.py`

**In `async_step_user`** - Add scan_interval field:
```python
data_schema = vol.Schema({
    vol.Required(CONF_USERNAME): str,
    vol.Required(CONF_SECRET_KEY): str,
    vol.Required(CONF_URL, default=DEFAULT_URL): str,
    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
        vol.Coerce(int),
        vol.Range(min=10, max=300)  # 10 seconds to 5 minutes
    ),
})
```

#### 1.3 Update Coordinator

**File**: `coordinator.py`

**Changes**:

1. Make update_interval configurable:
```python
def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Initialize coordinator."""
    self.api_client = ChoreboardAPIClient(...)
    self.monitored_users = entry.data.get(CONF_MONITORED_USERS, [])

    # Configurable scan interval
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    super().__init__(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_interval=timedelta(seconds=scan_interval),
    )
```

2. Add method for immediate refresh:
```python
async def async_refresh_immediately(self) -> None:
    """Trigger immediate data refresh after user action.

    This bypasses the normal update interval to provide
    instant feedback after service calls.
    """
    await self.async_request_refresh()
```

#### 1.4 Update Service Handlers

**File**: `__init__.py`

**All service handlers** - Add immediate refresh:

```python
async def handle_claim_chore(call: ServiceCall) -> None:
    """Handle claim_chore service call."""
    chore_id = call.data[ATTR_CHORE_ID]
    assign_to_user_id = call.data.get(ATTR_ASSIGN_TO_USER_ID)

    try:
        await coordinator.api_client.claim_chore(chore_id, assign_to_user_id)

        # Immediate refresh after successful action
        await coordinator.async_refresh_immediately()

    except ChoreboardAPIError as err:
        raise HomeAssistantError(f"Failed to claim chore: {err}") from err


async def handle_mark_complete(call: ServiceCall) -> None:
    """Handle mark_complete service call."""
    chore_id = call.data[ATTR_CHORE_ID]
    helpers = call.data.get(ATTR_HELPERS)
    completed_by_user_id = call.data.get(ATTR_COMPLETED_BY_USER_ID)

    try:
        await coordinator.api_client.complete_chore(
            chore_id,
            completed_by_user_id,
            helpers
        )

        # Immediate refresh after successful action
        await coordinator.async_refresh_immediately()

    except ChoreboardAPIError as err:
        raise HomeAssistantError(f"Failed to complete chore: {err}") from err


async def handle_undo_completion(call: ServiceCall) -> None:
    """Handle undo_completion service call."""
    chore_id = call.data[ATTR_CHORE_ID]

    try:
        await coordinator.api_client.undo_completion(chore_id)

        # Immediate refresh after successful action
        await coordinator.async_refresh_immediately()

    except ChoreboardAPIError as err:
        raise HomeAssistantError(f"Failed to undo completion: {err}") from err
```

### Testing Requirements

1. **Service Call Refresh**:
   - Claim chore → Verify immediate sensor update (< 2s)
   - Complete chore → Verify immediate sensor update (< 2s)
   - Undo completion → Verify immediate sensor update (< 2s)

2. **Background Polling**:
   - No service calls → Verify polls at configured interval
   - Set interval to 60s → Verify 60s polls
   - Set interval to 10s → Verify 10s polls

3. **Configuration**:
   - New integration → Can set scan interval during setup
   - Existing integration → Can change interval via options flow (see Enhancement 2)

---

## Enhancement 2: Options Flow

### Current Behavior

**Problem**: Integration settings cannot be changed after initial setup
- Cannot change scan interval
- Cannot change monitored users
- Cannot change backend URL
- User must delete and re-add integration to change settings

### Target Behavior

**Desired**: Options flow allows reconfiguration
- Reconfigure scan interval
- Add/remove monitored users
- Update backend URL
- Change credentials (username/secret_key)

### Implementation Details

#### 2.1 Add Options Flow to Config Flow

**File**: `config_flow.py`

Add `OptionsFlowHandler` class:

```python
class ChoreboardOptionsFlowHandler(OptionsFlow):
    """Handle ChoreBoard options flow."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Update config entry with new options
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={
                    **self.config_entry.data,
                    CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                },
            )

            # Reload integration to apply changes
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)

            return self.async_create_entry(title="", data={})

        # Show current settings as defaults
        current_scan_interval = self.config_entry.data.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=current_scan_interval,
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=10, max=300)
                ),
            }),
        )


@staticmethod
@callback
def async_get_options_flow(config_entry: ConfigEntry) -> ChoreboardOptionsFlowHandler:
    """Get the options flow handler."""
    return ChoreboardOptionsFlowHandler(config_entry)
```

**Add to `ChoreboardConfigFlow` class**:
```python
@staticmethod
@callback
def async_get_options_flow(config_entry: ConfigEntry) -> ChoreboardOptionsFlowHandler:
    """Get the options flow for this handler."""
    return ChoreboardOptionsFlowHandler(config_entry)
```

#### 2.2 Add Advanced Options Step (Future Enhancement)

For more complex reconfiguration (users, credentials, URL):

```python
async def async_step_init(
    self, user_input: dict[str, Any] | None = None
) -> FlowResult:
    """Manage the options - main menu."""
    return self.async_show_menu(
        step_id="init",
        menu_options=["scan_interval", "monitored_users", "credentials"],
    )

async def async_step_scan_interval(
    self, user_input: dict[str, Any] | None = None
) -> FlowResult:
    """Configure scan interval."""
    # Implementation above
    ...

async def async_step_monitored_users(
    self, user_input: dict[str, Any] | None = None
) -> FlowResult:
    """Configure monitored users."""
    if user_input is not None:
        # Update monitored users
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data={
                **self.config_entry.data,
                CONF_MONITORED_USERS: user_input[CONF_MONITORED_USERS],
            },
        )
        await self.hass.config_entries.async_reload(self.config_entry.entry_id)
        return self.async_create_entry(title="", data={})

    # Fetch current users from API
    api_client = ChoreboardAPIClient(...)
    users = await api_client.get_users()
    current_monitored = self.config_entry.data.get(CONF_MONITORED_USERS, [])

    return self.async_show_form(
        step_id="monitored_users",
        data_schema=vol.Schema({
            vol.Required(
                CONF_MONITORED_USERS,
                default=current_monitored,
            ): cv.multi_select({user["username"]: user["display_name"] for user in users}),
        }),
    )

async def async_step_credentials(
    self, user_input: dict[str, Any] | None = None
) -> FlowResult:
    """Update credentials and URL."""
    if user_input is not None:
        # Validate new credentials
        api_client = ChoreboardAPIClient(
            base_url=user_input[CONF_URL],
            username=user_input[CONF_USERNAME],
            secret_key=user_input[CONF_SECRET_KEY],
            session=async_get_clientsession(self.hass),
        )

        try:
            await api_client.test_connection()
        except ChoreboardAuthError:
            return self.async_show_form(
                step_id="credentials",
                data_schema=self._get_credentials_schema(),
                errors={"base": "invalid_auth"},
            )
        except ChoreboardConnectionError:
            return self.async_show_form(
                step_id="credentials",
                data_schema=self._get_credentials_schema(),
                errors={"base": "cannot_connect"},
            )

        # Update config
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data={
                **self.config_entry.data,
                CONF_USERNAME: user_input[CONF_USERNAME],
                CONF_SECRET_KEY: user_input[CONF_SECRET_KEY],
                CONF_URL: user_input[CONF_URL],
            },
        )
        await self.hass.config_entries.async_reload(self.config_entry.entry_id)
        return self.async_create_entry(title="", data={})

    return self.async_show_form(
        step_id="credentials",
        data_schema=self._get_credentials_schema(),
    )

def _get_credentials_schema(self) -> vol.Schema:
    """Get credentials schema with current values as defaults."""
    return vol.Schema({
        vol.Required(
            CONF_USERNAME,
            default=self.config_entry.data.get(CONF_USERNAME, ""),
        ): str,
        vol.Required(
            CONF_SECRET_KEY,
            default=self.config_entry.data.get(CONF_SECRET_KEY, ""),
        ): str,
        vol.Required(
            CONF_URL,
            default=self.config_entry.data.get(CONF_URL, DEFAULT_URL),
        ): str,
    })
```

#### 2.3 Update Strings

**File**: `strings.json`

Add options flow strings:

```json
{
  "config": {
    "step": {
      "user": { ... },
      "select_users": { ... }
    },
    ...
  },
  "options": {
    "step": {
      "init": {
        "title": "ChoreBoard Options",
        "description": "Configure ChoreBoard integration options",
        "menu_options": {
          "scan_interval": "Update Interval",
          "monitored_users": "Monitored Users",
          "credentials": "Connection Settings"
        }
      },
      "scan_interval": {
        "title": "Configure Update Interval",
        "description": "How often to poll the ChoreBoard backend for updates (in seconds). Changes made through Home Assistant will trigger immediate updates regardless of this setting.",
        "data": {
          "scan_interval": "Update interval (seconds)"
        }
      },
      "monitored_users": {
        "title": "Configure Monitored Users",
        "description": "Select which ChoreBoard users to monitor. A 'My Chores' sensor will be created for each selected user.",
        "data": {
          "monitored_users": "Users to monitor"
        }
      },
      "credentials": {
        "title": "Update Connection Settings",
        "description": "Update your ChoreBoard backend connection credentials and URL.",
        "data": {
          "username": "ChoreBoard Username",
          "secret_key": "Django SECRET_KEY",
          "url": "ChoreBoard Backend URL"
        }
      }
    },
    "error": {
      "cannot_connect": "Failed to connect to ChoreBoard backend. Check the URL and network connection.",
      "invalid_auth": "Authentication failed. Check your username and SECRET_KEY.",
      "unknown": "Unexpected error occurred. Check Home Assistant logs."
    }
  }
}
```

### Testing Requirements

1. **Options Menu**:
   - Open integration options → Shows menu with 3 choices
   - Each menu item opens correct form

2. **Scan Interval**:
   - Change from 30s to 60s → Integration reloads, polls at 60s
   - Change to invalid value (e.g., 5s) → Shows validation error

3. **Monitored Users**:
   - Add new user → New "My Chores" sensor created
   - Remove user → Corresponding sensor removed

4. **Credentials**:
   - Update username → New credentials used for API calls
   - Update invalid credentials → Shows authentication error
   - Update URL → Connects to new backend

---

## Enhancement 3: User Picker Enhancement

### Current Behavior

**Problem**: Not all users are exposed during setup
- Users are fetched from `/api/users/` endpoint
- Some users may be filtered out
- User picker may not show all available users

### Possible Causes

1. **API Filter Issue**: `/api/users/` may have default filters
2. **Config Flow Logic**: User filtering in `async_step_user`
3. **User Data Missing**: Some users missing required fields

### Investigation Steps

#### 3.1 Check Current Implementation

**File**: `config_flow.py`

**Current user fetching** (around line 60-80):
```python
async def async_step_user(
    self, user_input: dict[str, Any] | None = None
) -> FlowResult:
    """Handle the initial step."""
    if user_input is not None:
        # ... API client creation ...

        try:
            # Test connection
            await api_client.test_connection()

            # Fetch users for selection
            users = await api_client.get_users()

            # Store for next step
            self._available_users = users

            # ... proceed to user selection ...
```

**Check**: Does `get_users()` return all users?

#### 3.2 Verify API Client

**File**: `api_client.py`

**Check current implementation** (around line 200):
```python
async def get_users(self) -> list[dict[str, Any]]:
    """Get all active, assignable users.

    Returns:
        List of user dictionaries with points and other data
    """
    data = await self._request("GET", "/api/users/")
    return data if isinstance(data, list) else []
```

**Issue**: Docstring says "active, assignable users" but doesn't apply filters
- API may have default filters
- Need to check backend `/api/users/` endpoint behavior

#### 3.3 Backend Investigation (For Reference)

**Backend**: Check if `/api/users/` applies filters

**Potential filters**:
- `is_active=True`
- `can_be_assigned=True`
- `eligible_for_points=True`

**Solution if filtered**: Request ALL users from backend
```python
# If backend supports query params
data = await self._request("GET", "/api/users/?all=true")

# Or use different endpoint
data = await self._request("GET", "/api/all-users/")
```

### Implementation Details

#### 3.4 Option 1: Remove User Filtering (If Present)

**File**: `config_flow.py`

If filtering is done in config flow, remove it:

```python
# Before (if this exists)
active_users = [u for u in users if u.get("can_be_assigned", False)]

# After
# Show ALL users, let user decide who to monitor
all_users = users
```

#### 3.5 Option 2: Update API Client for All Users

**File**: `api_client.py`

Add method to get ALL users without filters:

```python
async def get_all_users(self) -> list[dict[str, Any]]:
    """Get ALL users from ChoreBoard, regardless of status.

    Used during config flow to show all available users for monitoring.

    Returns:
        List of all user dictionaries
    """
    # Try endpoint with 'all' parameter first
    try:
        data = await self._request("GET", "/api/users/?all=true")
        if isinstance(data, list):
            return data
    except ChoreboardAPIError:
        pass

    # Fallback to regular endpoint
    data = await self._request("GET", "/api/users/")
    return data if isinstance(data, list) else []
```

**Update config flow**:
```python
# In async_step_user
users = await api_client.get_all_users()  # Instead of get_users()
```

#### 3.6 Option 3: Backend Enhancement (If Needed)

**If backend doesn't expose all users**, create implementation plan for backend:

**File**: `C:\Users\pmagalios\PycharmProjects\ChoreBoard\downstream_integration_needs\EXPOSE_ALL_USERS_REQUIREMENT.md`

**Content**:
```markdown
# Requirement: Expose All Users in API

**From**: Home Assistant Integration
**Date**: 2025-12-16
**Priority**: Medium

## Problem

The Home Assistant integration's config flow needs to show ALL users during setup so administrators can select which users to monitor. Currently, the `/api/users/` endpoint may filter users (e.g., only active, assignable users).

## Requirement

Add support for retrieving all users, regardless of status.

## Proposed Solutions

### Option 1: Add Query Parameter

Support `?all=true` parameter on `/api/users/`:

```python
# In views.py
class UsersListView(APIView):
    def get(self, request):
        show_all = request.query_params.get('all', 'false').lower() == 'true'

        if show_all:
            users = User.objects.all()
        else:
            # Apply default filters
            users = User.objects.filter(can_be_assigned=True, is_active=True)

        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
```

### Option 2: Create Separate Endpoint

Add `/api/all-users/` endpoint for unrestricted access:

```python
class AllUsersView(APIView):
    """Return all users without filters."""

    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
```

## Testing

Verify endpoint returns users with:
- `can_be_assigned=False`
- `is_active=False`
- `eligible_for_points=False`
```

#### 3.7 Immediate Workaround: Show Better Error

While investigating, improve user feedback:

**File**: `config_flow.py`

```python
users = await api_client.get_users()

if not users:
    return self.async_show_form(
        step_id="user",
        data_schema=self._get_user_schema(),
        errors={"base": "no_users_found"},
    )

_LOGGER.info(f"Found {len(users)} users: {[u.get('username') for u in users]}")
```

**File**: `strings.json`

```json
"error": {
    "no_users_found": "No users found in ChoreBoard backend. Ensure at least one user exists and is active.",
    ...
}
```

### Testing Requirements

1. **All Users Shown**:
   - Backend has 5 users (3 active, 2 inactive)
   - Config flow shows all 5 users for selection

2. **User Selection Works**:
   - Can select active users → Creates sensors
   - Can select inactive users → Creates sensors (may show 0 chores)

3. **Logging**:
   - Check Home Assistant logs for user count
   - Verify correct number of users fetched

---

## Implementation Order

### Phase 1: Smart Polling (2-3 hours)
1. ✅ Add `CONF_SCAN_INTERVAL` constant
2. ✅ Update config flow with scan_interval field
3. ✅ Update coordinator to use configurable interval
4. ✅ Add `async_refresh_immediately()` method
5. ✅ Update all service handlers for immediate refresh
6. ✅ Test service calls trigger immediate update
7. ✅ Test background polling uses configured interval

### Phase 2: Options Flow (3-4 hours)
1. ✅ Add basic options flow (scan_interval only)
2. ✅ Test scan_interval reconfiguration
3. ✅ Add menu-based options flow
4. ✅ Add monitored_users reconfiguration
5. ✅ Add credentials reconfiguration
6. ✅ Update strings.json for options
7. ✅ Test all options flow paths

### Phase 3: User Picker (1-2 hours)
1. ✅ Investigate current user filtering
2. ✅ Check API client `get_users()` behavior
3. ✅ Add logging for user count
4. ✅ Test with multiple user scenarios
5. ⚠️ If backend filtering found: Create backend requirement doc
6. ✅ Implement workaround or fix in integration
7. ✅ Verify all users shown in config flow

---

## Files to Modify

### Must Modify
1. `custom_components/choreboard/const.py` - Add CONF_SCAN_INTERVAL
2. `custom_components/choreboard/config_flow.py` - Add options flow, update user step
3. `custom_components/choreboard/coordinator.py` - Configurable interval, immediate refresh
4. `custom_components/choreboard/__init__.py` - Update service handlers
5. `custom_components/choreboard/strings.json` - Add options flow strings

### May Modify (Depending on Investigation)
6. `custom_components/choreboard/api_client.py` - Add `get_all_users()` if needed

### External (If Backend Change Needed)
7. `C:\Users\pmagalios\PycharmProjects\ChoreBoard\downstream_integration_needs\EXPOSE_ALL_USERS_REQUIREMENT.md`

---

## Testing Checklist

### Smart Polling Tests
- [ ] Claim chore → Sensor updates within 2 seconds
- [ ] Complete chore → Sensor updates within 2 seconds
- [ ] Undo completion → Sensor updates within 2 seconds
- [ ] No actions → Polls at configured interval (30s default)
- [ ] Set interval to 60s → Verify 60s polling
- [ ] Set interval to 10s → Verify 10s polling (minimum)
- [ ] Invalid interval (5s) → Shows validation error

### Options Flow Tests
- [ ] Open integration options → Shows configuration menu
- [ ] Change scan interval → Integration reloads with new interval
- [ ] Add monitored user → New "My Chores" sensor created
- [ ] Remove monitored user → Sensor removed
- [ ] Update credentials → New credentials work
- [ ] Invalid credentials → Shows authentication error
- [ ] Update URL → Connects to new backend

### User Picker Tests
- [ ] Backend has N users → Config flow shows N users
- [ ] Includes inactive users → All shown in picker
- [ ] Select multiple users → All selected users monitored
- [ ] Deselect user → User not monitored
- [ ] No users in backend → Shows helpful error message

---

## Success Criteria

Enhancement implementation is complete when:

1. ✅ **Smart Polling Works**:
   - Service calls trigger immediate refresh
   - Background polling uses configured interval
   - Interval is configurable (10-300 seconds)

2. ✅ **Options Flow Works**:
   - Can reconfigure scan interval without reinstalling
   - Can reconfigure monitored users
   - Can update credentials and URL
   - Integration reloads automatically after changes

3. ✅ **User Picker Shows All Users**:
   - All users from backend appear in config flow
   - No filtering applied during selection
   - Can monitor any user regardless of status

4. ✅ **User Experience**:
   - Instant feedback after actions (< 2s)
   - No need to reinstall integration to change settings
   - Clear error messages when issues occur

5. ✅ **Code Quality**:
   - All tests passing
   - Ruff and mypy checks passing
   - Proper type hints
   - Good logging for debugging

---

## Risk Assessment

### Low Risk ✅
- **Smart Polling**: Low risk, coordinator already supports `async_request_refresh()`
- **Options Flow**: Standard Home Assistant pattern, well-documented

### Medium Risk ⚠️
- **User Picker**: May require backend changes if API filters users
- **Reload After Options**: Need to test with multiple sensors

### Mitigation
- Add comprehensive logging for debugging
- Test with various user configurations
- Create backend requirement doc if needed
- Implement graceful fallbacks

---

*Enhancement Plan v1.0*
*Target Release: v1.3.0*
*Estimated Total Time: 6-9 hours*
