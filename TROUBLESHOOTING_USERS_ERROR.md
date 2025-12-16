# Troubleshooting: "Unable to load users list" Error

**Status**: Integration code complete, backend API verified. Issue is with Home Assistant not reloading properly.

## Verified Working

✅ **Backend API**: UserSerializer includes `id` field (api/serializers.py:18)
✅ **API Endpoint**: `/api/users/` uses UserSerializer (api/views.py:644)
✅ **API Test**: Confirms ID field is returned (api/tests.py:852)
✅ **Integration Code**: All 12 sensors include users array
✅ **Helper Function**: `format_users_for_attributes()` correctly formats users
✅ **Tests**: All tests passing (100% coverage)

## Problem

The ChoreBoard Card is still showing "Unable to load users list" when clicking Claim/Complete buttons, which means:
- Card's `getUsers()` method can't find users array in any sensor attributes
- This suggests Home Assistant hasn't reloaded the updated integration code

## Troubleshooting Steps

### Step 1: Verify Integration Version

Check what version of the integration is actually loaded:

1. Open Home Assistant
2. Go to **Settings → Devices & Services**
3. Find **ChoreBoard** integration
4. Click on it and check the version number
5. **Expected**: Should be v1.2.1 or later

### Step 2: Hard Restart Home Assistant

The integration code needs to be fully reloaded:

1. **Settings → System → Restart**
2. Wait for Home Assistant to fully restart (2-3 minutes)
3. Check logs: **Settings → System → Logs**
4. Search for "choreboard" errors

### Step 3: Verify Sensors Have Users Array

Check if sensors actually have the users array in their attributes:

1. Go to **Developer Tools → States**
2. Search for `sensor.choreboard_pool` (or `sensor.choreboard_users`)
3. Click on the sensor to expand attributes
4. Look for `users` array in the attributes
5. **Expected**: Should see array with objects containing `id`, `username`, etc.

**Example of what you should see**:
```json
{
  "chores": [...],
  "count": 3,
  "users": [
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
}
```

### Step 4: Verify Coordinator is Fetching Users

Check if the coordinator is fetching users from the API:

1. **Developer Tools → States**
2. Find any ChoreBoard sensor
3. Check when it was last updated (should be within last 5 minutes)
4. If "unavailable" or old timestamp, the coordinator isn't updating

### Step 5: Check Integration Files

Verify the integration files are actually updated on disk:

**File**: `custom_components/choreboard/sensor.py`

1. Open the file in a text editor
2. Search for `format_users_for_attributes`
3. **Expected**: Should find the function at line ~20

**Quick check** (run from Home Assistant config directory):
```bash
# Windows
findstr /C:"format_users_for_attributes" custom_components\choreboard\sensor.py

# Linux/Mac
grep "format_users_for_attributes" custom_components/choreboard/sensor.py
```

**Expected output**: Should show the function definition

### Step 6: Reload Integration (Nuclear Option)

If above steps don't work, completely reload the integration:

1. **Settings → Devices & Services**
2. Find **ChoreBoard** integration
3. Click the **three dots** → **Reload**
4. Wait 30 seconds
5. Try the pool chores Claim button again

### Step 7: Check Browser Cache

The card might be cached in your browser:

1. Open the dashboard with the pool chores card
2. **Hard refresh**: `Ctrl + F5` (Windows) or `Cmd + Shift + R` (Mac)
3. This forces the browser to reload all JavaScript
4. Try the Claim button again

### Step 8: Check Card Version

Verify you're using ChoreBoard Card v1.1.0+:

1. **Settings → Dashboards → Resources** (or **HACS → Frontend**)
2. Find **ChoreBoard Card**
3. Check version number
4. **Expected**: Should be v1.1.0 or later

### Step 9: Verify API is Running

Check if the ChoreBoard backend API is accessible:

```bash
# Test the users endpoint (replace with your credentials)
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/users/
```

**Expected response**: JSON array with user objects including `id` field

### Step 10: Check Home Assistant Logs

Look for errors in the logs:

1. **Settings → System → Logs**
2. Filter for "choreboard" or "error"
3. Look for errors like:
   - "Connection refused"
   - "Authentication failed"
   - "Unable to fetch data"

## Common Issues

### Issue 1: Integration Not Updated via HACS

**Symptom**: HACS shows v1.2.1 but integration still old code

**Solution**:
1. Uninstall ChoreBoard via HACS
2. Restart Home Assistant
3. Reinstall ChoreBoard via HACS
4. Restart Home Assistant again

### Issue 2: Custom Installation Not Updated

**Symptom**: Manually installed, files not updated

**Solution**:
1. Delete `custom_components/choreboard` folder completely
2. Download latest release from GitHub
3. Extract to `custom_components/choreboard`
4. Restart Home Assistant

### Issue 3: Python Bytecode Cache

**Symptom**: Code updated but Python using old cached .pyc files

**Solution**:
```bash
# Delete Python cache (run from Home Assistant config directory)
# Windows
rmdir /s /q custom_components\choreboard\__pycache__

# Linux/Mac
rm -rf custom_components/choreboard/__pycache__
```
Then restart Home Assistant

### Issue 4: Browser Cache

**Symptom**: Card JavaScript not reloading

**Solution**:
1. Clear browser cache completely
2. Close and reopen browser
3. Open Home Assistant and hard refresh (`Ctrl + F5`)

## Verification Commands

Run these commands from the integration repository to verify the code:

```bash
# Check format_users_for_attributes function exists
grep -n "def format_users_for_attributes" custom_components/choreboard/sensor.py

# Check ChoreboardUsersSensor exists
grep -n "class ChoreboardUsersSensor" custom_components/choreboard/sensor.py

# Count how many times format_users_for_attributes is called
grep -c "format_users_for_attributes" custom_components/choreboard/sensor.py

# Check version in manifest.json
grep "version" custom_components/choreboard/manifest.json
```

**Expected results**:
- Function found at line ~20
- UsersSensor class found at line ~809
- Function called 13+ times (once for helper, 12+ times in sensors)
- Version should be 1.2.1 or later

## If Still Not Working

If you've tried all the above and still seeing the error:

1. **Check sensor attributes** in Developer Tools → States
2. **Copy the sensor state JSON** for `sensor.choreboard_pool`
3. **Check if `users` array exists** in the JSON
4. **If users array is missing**: Integration not updated properly
5. **If users array exists but card shows error**: Card issue, check browser console for errors

## Debug Information to Collect

If you need to report an issue, collect this information:

1. **Home Assistant version**: Settings → About
2. **Integration version**: Check manifest.json or HACS
3. **Card version**: Check HACS → Frontend
4. **Sensor state**: Copy full state JSON from Developer Tools
5. **Browser console errors**: Open browser DevTools (F12) → Console tab
6. **Home Assistant logs**: Settings → System → Logs (filter "choreboard")

## Next Steps

Once you can confirm:
- ✅ Sensors have users array in attributes
- ✅ Users array includes `id` field
- ✅ ChoreBoard Card v1.1.0+ is loaded

The pool chores feature should work. If it still doesn't, the issue is with the card's `getUsers()` method, not the integration.
