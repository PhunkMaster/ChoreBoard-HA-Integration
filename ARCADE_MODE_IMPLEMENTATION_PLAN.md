# Arcade Mode Integration Implementation Plan

## Status: ✅ COMPLETE

The ChoreBoard Home Assistant Integration v1.4.0 has **full arcade mode support already implemented**. All service handlers, API client methods, and data structures are ready.

## What's Already Implemented

### 1. Service Handlers (custom_components/choreboard/__init__.py)

All 6 arcade mode services are fully implemented:

| Service | Handler | Status |
|---------|---------|--------|
| `choreboard.start_arcade` | ✅ Implemented | Starts arcade timer for chore instance |
| `choreboard.stop_arcade` | ✅ Implemented | Stops timer, prepares for judging |
| `choreboard.approve_arcade` | ✅ Implemented | Judge approves completion |
| `choreboard.deny_arcade` | ✅ Implemented | Judge denies completion |
| `choreboard.continue_arcade` | ✅ Implemented | Resumes timer after denial |
| `choreboard.cancel_arcade` | ✅ Implemented | Cancels session, returns to pool |

### 2. API Client Methods (custom_components/choreboard/api_client.py)

All 8 arcade mode API client methods are implemented:

| Method | Status | Backend Endpoint |
|--------|--------|------------------|
| `start_arcade(instance_id, user_id)` | ✅ Implemented | POST `/api/arcade/start/` |
| `stop_arcade(session_id)` | ✅ Implemented | POST `/api/arcade/stop/` |
| `approve_arcade(session_id, judge_id, notes)` | ✅ Implemented | POST `/api/arcade/approve/` |
| `deny_arcade(session_id, judge_id, notes)` | ✅ Implemented | POST `/api/arcade/deny/` |
| `continue_arcade(session_id)` | ✅ Implemented | POST `/api/arcade/continue/` |
| `cancel_arcade(session_id)` | ✅ Implemented | POST `/api/arcade/cancel/` |
| `get_arcade_status(user_id)` | ✅ Implemented | GET `/api/arcade/status/` |
| `get_arcade_leaderboards()` | ✅ Implemented | GET `/api/arcade/leaderboards/` |

### 3. Service Definitions (custom_components/choreboard/services.yaml)

Complete service definitions with:
- Field descriptions and examples
- Required/optional parameter markers
- Selector configurations for UI
- User-friendly names and descriptions

### 4. Constants (custom_components/choreboard/const.py)

All arcade mode constants defined:
- Service names: `SERVICE_START_ARCADE`, `SERVICE_STOP_ARCADE`, etc.
- Attribute names: `ATTR_SESSION_ID`, `ATTR_INSTANCE_ID`, `ATTR_JUDGE_ID`, `ATTR_USER_ID`, `ATTR_NOTES`

### 5. Coordinator Integration

Arcade mode triggers coordinator refresh after all service calls, ensuring:
- Immediate sensor updates after arcade actions
- Real-time timer display in card
- Fresh leaderboard data

## What's Blocking Arcade Mode

### 🚨 Backend API Endpoints Missing

The integration is **100% complete** but cannot function because the **ChoreBoard Django backend does not have REST API endpoints** for arcade mode.

**Error when calling services:**
```
Failed to start arcade: Request failed: 400, message='Bad Request',
url='https://chores.phunkmaster.com/api/arcade/start/'
```

The backend has:
- ✅ Arcade mode business logic (`chores/arcade_service.py`)
- ✅ Web UI views (`board/views_arcade.py`)
- ❌ REST API endpoints (`api/views_arcade.py`) - **MISSING**

## Backend Requirements

The backend must implement these 8 REST API endpoints:

### 1. POST `/api/arcade/start/`
Start arcade timer for a chore instance.

**Request:**
```json
{
  "instance_id": 123,
  "user_id": 5  // Optional
}
```

**Response:**
```json
{
  "success": true,
  "message": "Arcade mode started",
  "session_id": 456,
  "session": {
    "id": 456,
    "chore_id": 123,
    "chore_name": "Wash Dishes",
    "user_id": 5,
    "user_name": "ash",
    "start_time": "2026-01-09T18:30:00Z",
    "elapsed_seconds": 0,
    "status": "active"
  }
}
```

### 2. POST `/api/arcade/stop/`
Stop arcade timer, submit for judging.

**Request:**
```json
{
  "session_id": 456
}
```

**Response:**
```json
{
  "success": true,
  "message": "Arcade session stopped - awaiting judge approval"
}
```

### 3. POST `/api/arcade/approve/`
Judge approves completion.

**Request:**
```json
{
  "session_id": 456,
  "judge_id": 2,     // Optional
  "notes": "Great job!"  // Optional
}
```

**Response:**
```json
{
  "success": true,
  "message": "Arcade completion approved - points awarded",
  "points_awarded": 10,
  "high_score": true,
  "rank": 1
}
```

### 4. POST `/api/arcade/deny/`
Judge denies completion.

**Request:**
```json
{
  "session_id": 456,
  "judge_id": 2,     // Optional
  "notes": "Chore not fully complete"  // Optional
}
```

**Response:**
```json
{
  "success": true,
  "message": "Arcade completion denied"
}
```

### 5. POST `/api/arcade/continue/`
Resume timer after denial.

**Request:**
```json
{
  "session_id": 456
}
```

**Response:**
```json
{
  "success": true,
  "message": "Arcade session resumed"
}
```

### 6. POST `/api/arcade/cancel/`
Cancel session and return chore to pool.

**Request:**
```json
{
  "session_id": 456
}
```

**Response:**
```json
{
  "success": true,
  "message": "Arcade session cancelled"
}
```

### 7. GET `/api/arcade/status/`
Get current arcade session status for user.

**Query Parameters:**
- `user_id` (optional) - If not provided, uses authenticated user

**Response:**
```json
{
  "has_active_session": true,
  "session": {
    "id": 456,
    "chore_id": 123,
    "chore_name": "Wash Dishes",
    "user_id": 5,
    "user_name": "ash",
    "start_time": "2026-01-09T18:30:00Z",
    "elapsed_seconds": 125,
    "status": "active"
  }
}
```

**Or when no active session:**
```json
{
  "has_active_session": false,
  "session": null
}
```

### 8. GET `/api/arcade/leaderboards/`
Get high scores for all chores.

**Response:**
```json
[
  {
    "chore_id": 123,
    "chore_name": "Wash Dishes",
    "high_scores": [
      {
        "user_id": 5,
        "user_name": "ash",
        "display_name": "Ash",
        "time_seconds": 180,
        "completed_at": "2026-01-09T18:45:00Z",
        "rank": 1
      },
      {
        "user_id": 3,
        "user_name": "misty",
        "display_name": "Misty",
        "time_seconds": 195,
        "completed_at": "2026-01-08T19:20:00Z",
        "rank": 2
      }
    ]
  }
]
```

## Integration Testing Checklist

Once backend API endpoints are implemented:

### Service Call Testing

- [ ] `start_arcade` - Creates new session, returns session_id
- [ ] `start_arcade` with `user_id` - Starts arcade for specific user
- [ ] `start_arcade` when session active - Returns error
- [ ] `stop_arcade` - Changes status to "judging"
- [ ] `approve_arcade` - Completes chore, awards points, updates leaderboard
- [ ] `approve_arcade` with `judge_id` and `notes` - Records judge info
- [ ] `deny_arcade` - Changes status to "denied"
- [ ] `deny_arcade` with notes - Records denial reason
- [ ] `continue_arcade` - Resumes timer after denial
- [ ] `cancel_arcade` - Deletes session, returns chore to pool

### Data Fetching Testing

- [ ] `get_arcade_status` returns correct session
- [ ] `get_arcade_status` with no session returns `has_active_session: false`
- [ ] `get_arcade_leaderboards` returns array of leaderboards
- [ ] Leaderboards sorted by time (fastest first)
- [ ] Timer calculation accurate (elapsed_seconds + time since start)

### Coordinator Testing

- [ ] Coordinator refreshes immediately after each service call
- [ ] Sensors update with new arcade session data
- [ ] Leaderboards update after approval
- [ ] Timer values increase in real-time

### Error Handling Testing

- [ ] Invalid `instance_id` returns 404
- [ ] Invalid `session_id` returns 404
- [ ] Unauthenticated requests return 401
- [ ] Missing required parameters return 400
- [ ] Network errors handled gracefully

## Success Criteria

✅ **Integration:** All service handlers implemented and tested
✅ **Integration:** All API client methods implemented
✅ **Integration:** Service definitions complete
✅ **Integration:** Constants defined
✅ **Integration:** Coordinator integration complete
❌ **Backend:** REST API endpoints need implementation
❌ **Testing:** End-to-end testing blocked by missing backend

## Next Steps

1. **Implement backend REST API endpoints** (See `ARCADE_MODE_BACKEND_PLAN.md` in ChoreBoard repository)
2. Test each endpoint with curl/Postman
3. Deploy backend with arcade API support
4. Run integration testing checklist above
5. Test with ChoreBoard Card v1.4.0+

## Notes

- Integration estimated implementation time: **COMPLETE (0 hours)**
- Backend estimated implementation time: **2-3 hours** (see backend plan)
- The integration is production-ready and waiting on backend API

## References

- Integration Release Notes: `release_notes_v1.4.0.md`
- Service Definitions: `custom_components/choreboard/services.yaml`
- API Client: `custom_components/choreboard/api_client.py`
- Service Handlers: `custom_components/choreboard/__init__.py`
- Backend Plan: See ChoreBoard repository `ARCADE_MODE_BACKEND_PLAN.md`
