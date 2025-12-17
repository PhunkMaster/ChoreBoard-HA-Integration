## ChoreBoard Home Assistant Integration v1.4.0

### Added
- **Arcade Mode Support** - Full competitive speedrun chore completion system
  - `choreboard.start_arcade` service - Start arcade timer for a chore instance
  - `choreboard.stop_arcade` service - Stop timer and prepare for judging
  - `choreboard.approve_arcade` service - Judge approves completion (awards points and high scores)
  - `choreboard.deny_arcade` service - Judge denies completion
  - `choreboard.continue_arcade` service - Resume arcade after denial
  - `choreboard.cancel_arcade` service - Cancel arcade and return chore to pool
  - All services support kiosk mode with optional user_id and judge_id parameters
  - Judge notes support for arcade approvals and denials
  - Immediate coordinator refresh after all arcade service calls

### Technical
- Added 8 arcade mode API client methods in `api_client.py`
- Added 6 arcade mode service handlers in `__init__.py`
- Added arcade mode service constants to `const.py` (SERVICE_START_ARCADE, etc.)
- Added arcade mode attribute constants (ATTR_SESSION_ID, ATTR_INSTANCE_ID, ATTR_JUDGE_ID, ATTR_USER_ID, ATTR_NOTES)
- Updated `services.yaml` with arcade mode service definitions
- Updated `strings.json` with arcade mode service UI text
- All code quality checks passing (ruff, mypy)

### Documentation
- Created comprehensive backend API specification: `ARCADE_MODE_API_ENDPOINTS.md`
  - 8 REST API endpoint specifications with full request/response formats
  - Complete Django view implementation code for backend team
  - URL configuration, authentication requirements, testing examples
  - Backend implementation estimated at 2-3 hours
- Optimized CLAUDE.md from 737 to 253 lines (66% reduction)
- Enhanced auto-release workflow to automatically update manifest.json version

### Installation

1. Download `choreboard.zip` from the assets below
2. Extract to your Home Assistant `custom_components` directory
3. Restart Home Assistant
4. Add the ChoreBoard integration via Settings → Devices & Services

### Requirements

- Home Assistant 2024.1.0 or newer
- ChoreBoard backend API with arcade mode endpoints

### Notes
- **Backend Requirement**: ChoreBoard backend must implement arcade mode REST API endpoints
- Backend has arcade mode web interface (`board/views_arcade.py`) and business logic (`chores/arcade_service.py`)
- REST API endpoints need to be created in `api/views_arcade.py` (see specification document)
- Integration is fully implemented and ready - waiting on backend API endpoints
