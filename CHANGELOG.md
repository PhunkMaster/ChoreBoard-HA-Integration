# Changelog

All notable changes to the ChoreBoard Home Assistant Integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
