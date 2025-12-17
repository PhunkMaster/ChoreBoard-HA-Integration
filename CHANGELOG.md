# Changelog

All notable changes to the ChoreBoard Home Assistant Integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.4.5] - 2025-12-17

### Changed
- **Auto-Release Workflow** - Replaced deprecated `actions/create-release@v1` with `softprops/action-gh-release@v2`
  - Uses actively maintained action for creating GitHub releases
  - Properly triggers `release.yml` workflow to upload choreboard.zip asset
  - Eliminates deprecation warnings in workflow logs
  - Same functionality with better support and reliability

### Technical
- Updated `.github/workflows/auto-release.yml` to use `softprops/action-gh-release@v2`
- Changed `release_name` parameter to `name` per new action's API
- Added explicit `token` parameter for authentication

## [1.4.4] - 2025-12-17

### Fixed
- **Auto-Release Workflow** - Fixed SSH credential persistence for deploy key authentication
  - Removed `persist-credentials: false` that was causing deploy key removal after checkout
  - Deploy key now remains available for git push operation
  - Resolves "Permission denied (publickey)" error when pushing manifest.json updates
  - v1.4.3 successfully added deploy key support, v1.4.4 fixes credential persistence

## [1.4.3] - 2025-12-17

### Fixed
- **Auto-Release Workflow** - Implemented SSH deploy key authentication to bypass repository rulesets
  - Workflow can now successfully push manifest.json updates to main branch (with v1.4.4 fix)
  - Deploy keys can be added to ruleset bypass list (unlike built-in github-actions[bot])
  - Resolves "Repository rule violations found" errors when updating manifest.json
  - See DEPLOY_KEY_SETUP.md for complete configuration instructions

### Added
- **DEPLOY_KEY_SETUP.md** - Comprehensive guide for configuring SSH deploy keys
  - Step-by-step setup instructions with security best practices
  - Troubleshooting guide for common issues
  - Workflow diagram and testing procedures
  - Key rotation recommendations

### Changed
- Updated auto-release workflow to use `ssh-key` parameter in checkout action
- Added workflow documentation comments explaining deploy key usage

### Note
This release completes the fully automated release pipeline:
- ✅ Squash merge detection (v1.4.1)
- ✅ Asset upload automation (v1.4.1)
- ✅ manifest.json automatic updates (v1.4.3)
- ✅ Full automation with no manual steps required

## [1.4.2] - 2025-12-17

### Testing
- Test auto-release workflow with github-actions bot bypass enabled
- Verify manifest.json automatic update works without manual PR

## [1.4.1] - 2025-12-17

### Fixed
- **Auto-Release Workflow** - Now handles squash merges correctly
- **Release Workflow** - Fixed asset upload permissions

## [1.4.0] - 2025-12-16

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

### Notes
- **Backend Requirement**: ChoreBoard backend must implement arcade mode REST API endpoints
- Backend has arcade mode web interface (`board/views_arcade.py`) and business logic (`chores/arcade_service.py`)
- REST API endpoints need to be created in `api/views_arcade.py` (see specification document)
- Integration is fully implemented and ready - waiting on backend API endpoints

## [1.3.0] - 2025-12-16

### Added
- **Smart Polling Strategy** - Intelligent data refresh based on user activity
  - Immediate refresh after service calls (claim, complete, undo) for instant UI feedback
  - Configurable background polling interval (10-300 seconds, default 30s)
  - `async_refresh_immediately()` method in coordinator for explicit immediate updates
- **Configurable Scan Interval** - Users can set custom poll frequency during integration setup
  - New `scan_interval` configuration option in setup flow
  - Range validation (10-300 seconds) to ensure reasonable polling behavior
  - Default: 30 seconds (was fixed at 5 minutes)
- **Options Flow** - Menu-based reconfiguration without reinstalling integration
  - Update scan interval after initial setup
  - Add/remove monitored users dynamically
  - Update credentials and backend URL
  - All changes applied immediately with automatic reload
- **Enhanced User Discovery** - All users now exposed in setup and options
  - Primary method: Fetch directly from `/api/users/` endpoint
  - Fallback method: Discover from leaderboard and chores
  - Shows all users including those with no chores or points
  - Comprehensive logging for debugging user discovery issues

### Changed
- Service handlers now trigger immediate coordinator refresh for responsive UI updates
  - `choreboard.mark_complete` → immediate refresh
  - `choreboard.claim_chore` → immediate refresh
  - `choreboard.undo_completion` → immediate refresh
- Coordinator update interval is now user-configurable instead of fixed
- Background polling occurs only when no recent user actions have triggered updates
- Options flow replaced with menu-based interface (3 configuration categories)
- Config entry updates now stored in `data` instead of `options` for consistency
- User discovery now prioritizes `/api/users/` endpoint over leaderboard/chores discovery
- User fetching logic unified between initial setup and options flow

### Fixed
- **User Picker Missing Users** - Setup and options now show ALL users from backend
  - Previously only showed users with chores or points
  - New users without activity are now visible
  - Inactive users are now selectable during setup
  - Resolves issue where some users couldn't be monitored

### Improved
- User experience: Data updates within 2 seconds of service calls instead of up to 5 minutes
- Network efficiency: Configurable polling allows users to balance freshness vs. API load
- Coordinator architecture: Cleaner separation between scheduled and action-triggered updates
- Configuration flexibility: All settings reconfigurable without removing/re-adding integration
- Credential updates: Can change backend URL or credentials after initial setup
- User discovery reliability: Two-tier approach ensures all users found even if API fails

### Technical
- Added `CONF_SCAN_INTERVAL` configuration constant
- Updated config flow to collect scan_interval preference
- Enhanced coordinator initialization to use configurable interval
- Implemented menu-based options flow with 3 steps (scan_interval, monitored_users, credentials)
- Each options step validates input and reloads integration automatically
- Removed redundant update listener (reload handled directly in options flow)
- Updated user fetching to use `api_client.get_users()` as primary method
- Added comprehensive logging (INFO/WARNING/DEBUG) for user discovery process
- Fallback user discovery maintains backward compatibility with older backends
- All code quality checks passing (ruff, mypy)

## [1.2.0] - 2025-12-16

### Added
- **Users Sensor** (`sensor.choreboard_users`) - Dedicated sensor exposing all ChoreBoard users with stats
- **Users array in ALL 12 sensors** - Complete implementation across entire sensor suite for ChoreBoard Card compatibility
  - System-wide sensors: Outstanding, Late, Pool Chores, Chore Breakdown, Completion History
  - Leaderboard sensors: Weekly, All-Time, Arcade Mode (per-chore)
  - Per-user sensors: My Chores, My Immediate Chores, Weekly Points, All-Time Points
- Users data includes `id` (required for service calls), `username`, `display_name`, `first_name`, points, and assignment eligibility
- `format_users_for_attributes()` helper function for consistent user data formatting across sensors
- Leaderboard sensors include `all_users` field with full users list (non-breaking change)

### Changed
- All sensor attributes now include full users list for ChoreBoard Card pool chores feature (v1.1.0+)
- Enhanced sensor attributes to support user selection dialogs (Claim and Complete pool chores)
- Leaderboard sensors maintain backward compatibility while adding full users data

### Documentation
- Comprehensive Sensor Attributes section in CLAUDE.md documenting users array structure
- Added ChoreBoard Card Integration section to README.md
- Documented all 12 sensors with users array support
- Added dedicated Users Sensor documentation in README.md with complete field descriptions

## [1.1.0] - 2025-12-15

### Added
- **Pool Chores Sensor** (`sensor.pool_chores`) - Track all unassigned chores in the pool
- **Chore Breakdown Sensor** (`sensor.chore_breakdown`) - Statistics and distribution of chores by status
- **Completion History Sensor** (`sensor.completion_history`) - Recent chore completions with helper information
- **Weekly Points Sensors** (`sensor.<username>_weekly_points`) - Per-user weekly point totals
- **All-Time Points Sensors** (`sensor.<username>_alltime_points`) - Per-user lifetime point totals
- **Weekly Leaderboard Sensor** (`sensor.leaderboard_weekly`) - Current week's point rankings
- **All-Time Leaderboard Sensor** (`sensor.leaderboard_alltime`) - Lifetime point rankings
- **Arcade Mode Leaderboard Sensors** (`sensor.arcade_<chore_name>`) - Speed-run high scores for arcade-enabled chores
- **Completion tracking** on all chore sensors (last_completed_by, last_completed_at, was_late, helpers)
- **Helper support** in `mark_complete` service - Credit multiple users with partial points
- **User selection** in `mark_complete` service - Complete chores on behalf of other users via `completed_by_user_id` parameter
- **User assignment** in `claim_chore` service - Assign pool chores to specific users via `assign_to_user_id` parameter
- **Undo completion service** (`choreboard.undo_completion`) - Reverse accidental completions (admin only)
- **New API endpoints**: `/api/users/`, `/api/recent-completions/`, `/api/chore-leaderboards/`
- **Enhanced API methods** with new parameters for multi-user support
- **Comprehensive test suite**: 206 lines of sensor tests, 240 lines of service tests (36 total tests, 100% passing)

### Changed
- Enhanced `mark_complete` service with `helpers` and `completed_by_user_id` parameters
- Enhanced `claim_chore` service with `assign_to_user_id` parameter
- Updated service schemas and validation
- Improved coordinator data fetching to include users, completions, and leaderboards
- Updated mock data in test fixtures to support all new sensors

### Fixed
- Sensor entity naming to follow Home Assistant conventions
- Test coverage for multi-user scenarios
- Error handling for API failures

### Documentation
- Comprehensive README update with all sensor documentation
- Service examples with new parameters
- Example automations for common use cases
- Configuration guide with HMAC-SHA256 authentication details

## [1.0.3] - 2025-12-15

### Added
- **Filter chores by due date**: Only show chores due by today at 23:59:59
- **Normalize datetime display**: Format all datetime fields as `YYYY-MM-DD HH:MM` (removes seconds/microseconds)
- `_is_due_today()` method to check if chore is due by end of today
- `_normalize_datetime()` method to format datetimes without seconds
- `_filter_chores_by_due_date()` method to apply both filtering and normalization
- 8 comprehensive test cases covering all filtering scenarios

### Changed
- Modified `_async_update_data()` to filter outstanding and late chores by due date

### Fixed
- Chores no longer show future due dates
- Datetime displays are cleaner and more user-friendly

## [1.0.2] - 2025-12-14

### Fixed
- Bug fixes and stability improvements

## [1.0.1] - 2025-12-14

### Added
- Options flow for reconfiguring monitored users
- Improved user selection interface

### Changed
- Enhanced user selection process during configuration

## [1.0.0] - 2025-12-14

### Added
- **Initial release** of ChoreBoard Home Assistant Integration
- **Core sensors**:
  - Outstanding Chores sensor (`sensor.outstanding_chores`)
  - Late Chores sensor (`sensor.late_chores`)
  - My Chores sensors per user (`sensor.<username>_my_chores`)
  - My Immediate Chores sensors per user (`sensor.<username>_my_immediate_chores`)
  - Leaderboard sensors (weekly and all-time)
- **Services**:
  - `choreboard.mark_complete` - Mark chores as completed
  - `choreboard.claim_chore` - Claim pool chores
- **Configuration flow**: Two-step setup with credential validation and user selection
- **HMAC-SHA256 authentication** with Django SECRET_KEY
- **Multi-user support**: Select which ChoreBoard users to monitor
- **Automatic polling**: Regular updates from ChoreBoard API
- **CI/CD pipeline**: Automated testing with Ruff, MyPy, pytest
- **HACS compatibility**: Ready for Home Assistant Community Store
- **Comprehensive testing**: Full test coverage for coordinator, sensors, and services
- **Development tooling**: Pre-commit hooks, linting, type checking

### Dependencies
- Home Assistant 2024.1.0 or later
- Python 3.11 or later
- ChoreBoard backend with REST API

---

## Links

- [GitHub Repository](https://github.com/PhunkMaster/ChoreBoard-HA-Integration)
- [Issue Tracker](https://github.com/PhunkMaster/ChoreBoard-HA-Integration/issues)
- [Releases](https://github.com/PhunkMaster/ChoreBoard-HA-Integration/releases)

## Contributors

- [@PhunkMaster](https://github.com/PhunkMaster)
- [@pmagalios](https://github.com/pmagalios)
- Claude Sonnet 4.5 (via [Claude Code](https://claude.com/claude-code))
