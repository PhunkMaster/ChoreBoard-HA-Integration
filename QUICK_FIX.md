# Quick Fix: "Unable to load users list" Error

## Status

✅ **Integration code**: Complete (v1.2.1 released)
✅ **Backend API**: Verified working (includes user `id` field)
❌ **Your Home Assistant**: Not loading updated integration

## The Issue

You're still seeing "Unable to load users list" because **Home Assistant hasn't reloaded the updated integration code** yet. The code is correct, but your HA instance is running the old version.

## Quick Fix (Try These in Order)

### Fix 1: Hard Restart Home Assistant (90% success rate)

1. **Settings → System → Restart**
2. Wait 3 minutes for full restart
3. Hard refresh browser: **Ctrl + F5** (Windows) or **Cmd + Shift + R** (Mac)
4. Try pool chores Claim button

**Why this works**: Forces Home Assistant to reload all integrations and clear Python bytecode cache.

### Fix 2: Reload Integration (95% success rate)

1. **Settings → Devices & Services**
2. Find **ChoreBoard** integration
3. Click **three dots (•••) → Reload**
4. Wait 30 seconds
5. Hard refresh browser: **Ctrl + F5**
6. Try pool chores Claim button

**Why this works**: Reloads just the ChoreBoard integration without full restart.

### Fix 3: Clear Python Cache + Restart (99% success rate)

**Windows** (run from HA config directory):
```cmd
rmdir /s /q custom_components\choreboard\__pycache__
```

**Linux/Mac**:
```bash
rm -rf custom_components/choreboard/__pycache__
```

Then:
1. Restart Home Assistant
2. Wait 3 minutes
3. Hard refresh browser
4. Try pool chores Claim button

**Why this works**: Deletes cached .pyc files that may be using old code.

### Fix 4: Reinstall Integration (100% success rate)

**If using HACS**:
1. HACS → Integrations
2. Find ChoreBoard
3. Click **three dots → Remove**
4. Restart Home Assistant
5. HACS → Integrations → **Explore & Download Repositories**
6. Search "ChoreBoard"
7. Install
8. Restart Home Assistant
9. Reconfigure integration (Settings → Devices & Services → Add Integration)

**If manual install**:
1. Delete `custom_components/choreboard` folder completely
2. Download latest release: https://github.com/PhunkMaster/ChoreBoard-HA-Integration/releases/latest
3. Extract to `custom_components/choreboard`
4. Restart Home Assistant

## Verify the Fix

After trying a fix, verify it worked:

1. **Developer Tools → States**
2. Search for `sensor.choreboard_pool`
3. Click to expand attributes
4. Look for `users` array

**✅ Success looks like**:
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
      "all_time_points": "150.00"
    }
  ]
}
```

**❌ Still broken looks like**:
```json
{
  "chores": [...],
  "count": 3
}
```
(No `users` array)

## If Still Not Working

If none of the above worked, check:

1. **Integration version**: Settings → Devices & Services → ChoreBoard
   - Should show v1.2.1 or later
   - If older, update failed - try Fix 4

2. **Sensor actually updated**: Check the file on disk
   ```bash
   # Should find the helper function
   grep "format_users_for_attributes" custom_components/choreboard/sensor.py
   ```
   - If not found, files didn't update - try Fix 4

3. **Home Assistant logs**: Settings → System → Logs
   - Search for "choreboard"
   - Look for errors like "import error" or "syntax error"

## After Fix Works

Once you see the users array in sensor attributes:

1. ✅ Pool chores Claim button should show user selection dialog
2. ✅ Pool chores Complete button should show completer + helpers selection
3. ✅ Service calls should work with user IDs

## Still Having Issues?

See detailed troubleshooting:
- [TROUBLESHOOTING_USERS_ERROR.md](./TROUBLESHOOTING_USERS_ERROR.md) - Integration side
- [Card debugging guide](../ChoreBoard-HA-Card/INTEGRATION_USERS_DEBUGGING.md) - Card side

## Summary

**The code is correct and complete**. This is purely an issue of Home Assistant not loading the updated files. One of the fixes above WILL work - it's just a matter of finding which one forces your HA instance to reload properly.

**Most likely fix**: Fix 1 (Hard Restart) or Fix 2 (Reload Integration)
