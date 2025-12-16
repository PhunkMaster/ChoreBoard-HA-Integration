# Phase 2: Integration Testing Guide

**Date**: 2025-12-16
**Phase**: Integration Testing in Home Assistant
**Prerequisites**: ✅ Phase 1 Complete (API Verified)

---

## Overview

This guide walks through testing the ChoreBoard integration with Home Assistant to verify the pool chores feature works end-to-end.

**Estimated Time**: 30-45 minutes
**Required**: Home Assistant instance + ChoreBoard backend running

---

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Home Assistant running**
  - Local instance or test instance
  - Access to Settings → Devices & Services
  - Access to Developer Tools

- [ ] **ChoreBoard backend running**
  - Backend accessible (e.g., http://localhost:8000)
  - At least 2 users configured
  - At least 1 pool chore available
  - API responding to requests

- [ ] **ChoreBoard Integration installed**
  - Custom component in `custom_components/choreboard/`
  - Home Assistant restarted after installation
  - Integration configured with credentials

- [ ] **ChoreBoard Card installed** (optional for full testing)
  - Card installed in HACS or manually
  - Dashboard configured with card

---

## Test Plan

### Test 1: Verify Users Sensor Exists ⚠️ **CRITICAL**

**Objective**: Confirm dedicated users sensor is created

**Steps**:

1. Open Home Assistant
2. Navigate to **Developer Tools** → **States**
3. Search for: `sensor.users`

**Expected Results**:

✅ **Sensor State**:
```
State: <number> (e.g., "2" for 2 users)
```

✅ **Sensor Attributes**:
```yaml
users:
  - id: 1
    username: "ash"
    display_name: "Ash"
    first_name: "Ash"
    can_be_assigned: true
    eligible_for_points: true
    weekly_points: "25.00"
    all_time_points: "150.00"
    claims_today: 2
  - id: 2
    username: "sam"
    # ... more users
count: 2
```

**Verification Checklist**:
- [ ] Sensor `sensor.users` exists
- [ ] State shows correct user count
- [ ] Attributes contain `users` array
- [ ] Each user has `id` field (integer)
- [ ] Each user has all required fields

**❌ If Fails**:
- Check Home Assistant logs for errors
- Verify integration loaded: Settings → Devices & Services → ChoreBoard
- Restart Home Assistant and recheck

---

### Test 2: Verify All Sensors Have Users Array

**Objective**: Confirm all 13 sensors include users/all_users in attributes

**Sensors to Check**:

1. `sensor.outstanding_chores`
2. `sensor.late_chores`
3. `sensor.pool_chores`
4. `sensor.chore_breakdown`
5. `sensor.completion_history`
6. `sensor.<username>_my_chores` (e.g., `sensor.ash_my_chores`)
7. `sensor.<username>_my_immediate_chores`
8. `sensor.leaderboard_weekly`
9. `sensor.leaderboard_alltime`
10. `sensor.arcade_<chore_name>` (if arcade chores exist)
11. `sensor.<username>_weekly_points`
12. `sensor.<username>_all_time_points`
13. `sensor.users` (already checked in Test 1)

**Steps**:

1. Go to **Developer Tools** → **States**
2. For each sensor in the list:
   - Search for the sensor entity
   - Click to expand attributes
   - Look for `users` or `all_users` field

**Expected for Each Sensor**:

✅ **Has users array**:
```yaml
users:  # or "all_users" for leaderboard sensors
  - id: 1
    username: "ash"
    # ... full user object
```

✅ **Users array is not empty**
✅ **First user has `id` field**

**Quick Check Script** (optional):

If you have access to Home Assistant Python:
```python
# In Home Assistant Developer Tools → Template
{% set sensors = [
  'sensor.outstanding_chores',
  'sensor.late_chores',
  'sensor.pool_chores',
  'sensor.chore_breakdown',
  'sensor.completion_history',
  'sensor.ash_my_chores',
  'sensor.ash_my_immediate_chores',
  'sensor.leaderboard_weekly',
  'sensor.leaderboard_alltime',
  'sensor.ash_weekly_points',
  'sensor.ash_all_time_points',
  'sensor.users'
] %}

{% for sensor in sensors %}
{{ sensor }}:
  {% set s = states[sensor] %}
  {% if s %}
    {% if 'users' in s.attributes %}
      ✅ Has 'users' ({{ s.attributes.users | length }} users)
    {% elif 'all_users' in s.attributes %}
      ✅ Has 'all_users' ({{ s.attributes.all_users | length }} users)
    {% else %}
      ❌ Missing users array
    {% endif %}
  {% else %}
    ❌ Sensor not found
  {% endif %}
{% endfor %}
```

**Verification Checklist**:
- [ ] All sensors exist
- [ ] All sensors have users or all_users array
- [ ] Arrays are not empty
- [ ] User objects have id field

---

### Test 3: Pool Chores Claim Dialog ⚠️ **CRITICAL**

**Objective**: Verify claim dialog shows users and successfully claims chore

**Prerequisites**:
- ChoreBoard Card installed
- Dashboard with pool chores card configured
- At least 1 pool chore available

**Steps**:

1. Open Home Assistant dashboard with ChoreBoard Card
2. Locate a **pool chore** in the card
3. Click the **"Claim"** button on the pool chore
4. Observe the dialog that appears

**Expected Results**:

✅ **Dialog Opens**:
- Dialog appears without errors
- No "Unable to load users list" error

✅ **User List Displayed**:
- Shows list of users with display names
- Users are selectable (radio buttons or dropdown)
- List matches users from backend

✅ **Selection Works**:
- Can select a user
- Confirm/Submit button is enabled

✅ **Claim Succeeds**:
- Click confirm/submit
- Dialog closes
- Chore is removed from pool chores
- Chore appears in selected user's "My Chores"
- No errors in Home Assistant logs

**Manual Verification**:

After claiming, check:
```
Developer Tools → States → sensor.pool_chores
- Count should decrease by 1

Developer Tools → States → sensor.<username>_my_chores
- Count should increase by 1
- Chore should appear in chores list
```

**Verification Checklist**:
- [ ] Claim button exists on pool chores
- [ ] Clicking claim opens dialog
- [ ] Dialog shows user list (no error)
- [ ] Can select user from list
- [ ] Claim succeeds when confirmed
- [ ] Chore moves to user's chores
- [ ] No errors in HA logs

**❌ If Fails**:
- Check browser console for JavaScript errors
- Check Home Assistant logs for service call errors
- Verify sensor attributes have users array
- Verify user objects have id field

---

### Test 4: Pool Chores Complete Dialog ⚠️ **CRITICAL**

**Objective**: Verify complete dialog shows user selection and successfully completes chore

**Prerequisites**:
- Pool chore available (claimed or unclaimed)
- ChoreBoard Card configured

**Steps**:

1. Locate a pool chore in the card
2. Click the **"Complete"** button
3. Observe the dialog that appears

**Expected Results**:

✅ **Dialog Opens**:
- Dialog appears with two sections
- No "Unable to load users list" error

✅ **Section 1: Who Completed** (Required):
- Label: "Who completed this chore?" or similar
- Shows list of users
- Single-select (radio buttons)
- Required field

✅ **Section 2: Who Helped** (Optional):
- Label: "Who helped?" or similar
- Shows list of users
- Multi-select (checkboxes)
- Optional field
- Can select 0, 1, or multiple helpers

✅ **Selection Works**:
- Can select completer (required)
- Can select 0+ helpers (optional)
- Confirm button enabled when completer selected

✅ **Complete Succeeds**:
- Click confirm/submit
- Dialog closes
- Chore marked as complete
- Chore removed from active chores
- Points awarded to completer and helpers
- No errors in logs

**Manual Verification**:

After completing:
```
Developer Tools → States → sensor.pool_chores
- Chore should be removed from pool

Developer Tools → States → sensor.completion_history
- New completion should appear
- Shows completer and helpers
- Shows points awarded
```

**Verification Checklist**:
- [ ] Complete button exists
- [ ] Clicking complete opens dialog
- [ ] Dialog has two sections (completer + helpers)
- [ ] Both sections show user lists
- [ ] Can select completer (required)
- [ ] Can select helpers (optional, multi-select)
- [ ] Complete succeeds when confirmed
- [ ] Chore marked complete in backend
- [ ] Points awarded correctly
- [ ] No errors in HA logs

**❌ If Fails**:
- Check browser console for errors
- Check HA logs for service errors
- Verify users array has all required fields
- Verify backend service endpoints work

---

### Test 5: Service Calls with User IDs

**Objective**: Verify service calls work directly with user IDs

**Test 5A: Claim Chore Service**

**Steps**:

1. Go to **Developer Tools** → **Services**
2. Select service: `choreboard.claim_chore`
3. Fill in service data:
   ```yaml
   chore_id: 42  # Use actual pool chore instance ID
   assign_to_user_id: 1  # Use actual user ID
   ```
4. Click **"Call Service"**

**Expected**:
- ✅ Service call succeeds (no error toast)
- ✅ Chore assigned to user in backend
- ✅ Sensors update after refresh
- ✅ No errors in logs

**Test 5B: Complete Chore Service**

**Steps**:

1. Go to **Developer Tools** → **Services**
2. Select service: `choreboard.mark_complete`
3. Fill in service data:
   ```yaml
   chore_id: 42  # Use actual chore instance ID
   completed_by_user_id: 1  # User who completed
   helpers:
     - 2  # Helper user IDs (optional)
     - 3
   ```
4. Click **"Call Service"**

**Expected**:
- ✅ Service call succeeds
- ✅ Chore marked complete in backend
- ✅ Points awarded to completer and helpers
- ✅ Completion appears in history
- ✅ No errors in logs

**Verification Checklist**:
- [ ] `claim_chore` service works with user ID
- [ ] `mark_complete` service works with user IDs
- [ ] Backend processes requests correctly
- [ ] Sensors update after service calls
- [ ] No service call errors

---

## Test Results Template

After completing all tests, document results:

```markdown
# Phase 2 Integration Testing Results

**Date**: YYYY-MM-DD
**Tester**: Your Name
**Environment**: Home Assistant version, ChoreBoard version

## Test Results Summary

| Test | Status | Notes |
|------|--------|-------|
| Test 1: Users Sensor | ✅/❌ | |
| Test 2: All Sensors Have Users | ✅/❌ | |
| Test 3: Claim Dialog | ✅/❌ | |
| Test 4: Complete Dialog | ✅/❌ | |
| Test 5: Service Calls | ✅/❌ | |

## Detailed Results

### Test 1: Users Sensor
- Status: ✅ PASSED / ❌ FAILED
- User Count: X users
- ID Field Present: Yes/No
- Notes: [Any issues or observations]

### Test 2: All Sensors Have Users
- Status: ✅ PASSED / ❌ FAILED
- Sensors Checked: X/13
- Sensors Missing Users: [list if any]
- Notes: [Any issues]

### Test 3: Claim Dialog
- Status: ✅ PASSED / ❌ FAILED
- Dialog Opened: Yes/No
- Users Displayed: Yes/No
- Claim Succeeded: Yes/No
- Notes: [Any issues]

### Test 4: Complete Dialog
- Status: ✅ PASSED / ❌ FAILED
- Dialog Opened: Yes/No
- Completer Selection: Yes/No
- Helper Selection: Yes/No
- Complete Succeeded: Yes/No
- Notes: [Any issues]

### Test 5: Service Calls
- Status: ✅ PASSED / ❌ FAILED
- Claim Service: Success/Failed
- Complete Service: Success/Failed
- Notes: [Any issues]

## Overall Result

- ✅ **ALL TESTS PASSED** - Ready for Production
- ⚠️ **SOME TESTS FAILED** - Requires fixes
- ❌ **CRITICAL FAILURES** - Blocked

## Issues Found

[List any issues, errors, or unexpected behavior]

## Next Steps

[Based on results, what should be done next?]
```

---

## Troubleshooting

### Issue: Sensor Not Found

**Problem**: `sensor.users` or other sensors don't exist

**Solutions**:
1. Check integration loaded: Settings → Devices & Services
2. Check Home Assistant logs for errors
3. Restart Home Assistant
4. Verify integration files in `custom_components/choreboard/`

### Issue: Users Array Empty

**Problem**: Sensor has `users` attribute but array is empty

**Solutions**:
1. Check backend `/api/users/` returns data
2. Verify users exist in backend database
3. Check users are active and can_be_assigned=true
4. Check integration API client credentials

### Issue: Missing ID Field

**Problem**: Users array exists but objects missing `id`

**Solutions**:
1. Re-verify backend serializer (should not happen after Phase 1)
2. Check coordinator data transformation
3. Check sensor format_users_for_attributes function

### Issue: Claim Dialog Error

**Problem**: "Unable to load users list" error in dialog

**Solutions**:
1. Verify sensors have users array (Test 2)
2. Check browser console for JavaScript errors
3. Verify card can access Home Assistant entities
4. Check card configuration

### Issue: Service Call Fails

**Problem**: Service calls return errors

**Solutions**:
1. Verify user IDs are correct (integers)
2. Check Home Assistant logs for error details
3. Verify backend endpoints are accessible
4. Check HMAC authentication working

---

## Success Criteria

Phase 2 is complete when:

- ✅ All 5 tests pass
- ✅ No critical errors in logs
- ✅ Pool chores claim works
- ✅ Pool chores complete works
- ✅ Service calls succeed

**Next Phase**: Phase 3 (Production Validation)

---

*Integration Testing Guide - Phase 2*
*Version: 1.0*
*Date: 2025-12-16*
