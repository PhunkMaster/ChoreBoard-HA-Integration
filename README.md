# ChoreBoard Home Assistant Integration

A Home Assistant custom integration for ChoreBoard, enabling you to track chores, assignments, leaderboards, and completion status directly within Home Assistant.

## Features

### Comprehensive Sensor Suite
- **8 sensor types** covering all aspects of chore tracking
- **System-wide sensors** for outstanding, late, and pool chores
- **Per-user sensors** for individual tracking and leaderboards
- **Statistics sensors** for chore breakdown and completion history
- **Arcade mode support** with speed-run leaderboards

### Enhanced Services
- **Mark chores complete** with helper credits and user selection
- **Claim pool chores** and assign to specific users
- **Undo completions** for mistake correction
- **Full multi-user support** for household management

### Real-Time Tracking
- Automatic polling of ChoreBoard API for updates
- Completion information on all chores (who, when, helpers)
- Point tracking for gamification
- Weekly and all-time leaderboards
- **User Selection Dialogs**: All sensors include users data for card user selection features

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as the category
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/choreboard` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Add the integration via the UI

## Configuration

1. Go to Settings > Devices & Services
2. Click "Add Integration"
3. Search for "ChoreBoard"
4. Enter your ChoreBoard credentials:
   - **Username**: Your ChoreBoard username
   - **Secret Key**: Django SECRET_KEY from your ChoreBoard backend
   - **URL**: Your ChoreBoard backend URL (e.g., http://localhost:8000)
5. Select which users to monitor
6. Click "Submit"

The integration uses HMAC-SHA256 authentication with your Django SECRET_KEY to generate secure API tokens.

## Usage

### Sensors

The integration automatically creates sensors based on your ChoreBoard data and monitored users.

#### System-Wide Sensors

##### Outstanding Chores (`sensor.outstanding_chores`)
Tracks all incomplete, non-overdue chores.

**State**: Count of outstanding chores

**Attributes**:
- `chores`: List of chore details including:
  - `id`: Chore instance ID
  - `name`: Chore name
  - `description`: Chore description
  - `assigned_to`: Username and display name
  - `due_at`: Due date/time
  - `points`: Point value
  - `last_completed_by`: Who last completed this chore
  - `last_completed_at`: When it was last completed
  - `was_late`: Whether last completion was late
  - `helpers`: List of helpers on last completion

##### Late Chores (`sensor.late_chores`)
Tracks all overdue chores.

**State**: Count of late chores

**Attributes**: Same as Outstanding Chores

##### Pool Chores (`sensor.pool_chores`)
Tracks all unassigned chores available for claiming.

**State**: Count of pool chores

**Attributes**:
- `chores`: List of pool chore details

##### Chore Breakdown (`sensor.chore_breakdown`)
Statistics about chore distribution.

**State**: Total chore count

**Attributes**:
- `total_chores`: Total number of chores
- `pool_chores`: Number of pool chores
- `assigned_chores`: Number of assigned chores
- `pool_percentage`: Percentage in pool
- `assigned_percentage`: Percentage assigned
- `status_breakdown`: Count by status (POOL, ASSIGNED, etc.)

##### Completion History (`sensor.completion_history`)
Recent chore completions across all users.

**State**: Count of recent completions

**Attributes**:
- `completions`: List of recent completions with:
  - `chore_name`: Name of completed chore
  - `completed_by`: User who completed it
  - `completed_at`: Completion timestamp
  - `was_late`: Whether completion was late
  - `helpers`: List of helpers with names and points
  - `points_earned`: Points awarded

#### Leaderboard Sensors

##### Weekly Leaderboard (`sensor.leaderboard_weekly`)
Current week's point rankings.

**State**: Number of users on leaderboard

**Attributes**:
- `users`: List of users with:
  - `rank`: Current rank
  - `name`: Display name
  - `username`: Username
  - `points`: Weekly points total

##### All-Time Leaderboard (`sensor.leaderboard_alltime`)
Lifetime point rankings.

**State**: Number of users on leaderboard

**Attributes**: Same as Weekly Leaderboard

##### Arcade Mode Leaderboards (`sensor.arcade_<chore_name>`)
Speed-run high scores for arcade-enabled chores.

**State**: Number of high scores

**Attributes**:
- `chore_id`: ID of the chore
- `chore_name`: Name of the chore
- `scores`: List of high scores with:
  - `rank`: Rank position
  - `username`: User who set the score
  - `time_seconds`: Time in seconds
  - `time_formatted`: Formatted time string
  - `achieved_at`: When the score was set

#### Per-User Sensors

For each monitored user, the following sensors are created:

##### My Chores (`sensor.<username>_my_chores`)
Chores assigned to this user.

**State**: Count of user's chores

**Attributes**:
- `username`: User's username
- `chores`: List of assigned chores (same attributes as Outstanding Chores)

##### My Immediate Chores (`sensor.<username>_my_immediate_chores`)
Chores due today or overdue for this user.

**State**: Count of immediate chores

**Attributes**: Same as My Chores

##### Weekly Points (`sensor.<username>_weekly_points`)
User's current week point total.

**State**: Weekly points (float)

**Unit**: `points`

**Attributes**:
- `username`: Username
- `display_name`: Display name
- `points`: Weekly points
- `claims_today`: Number of chores claimed today

##### All-Time Points (`sensor.<username>_alltime_points`)
User's lifetime point total.

**State**: All-time points (float)

**Unit**: `points`

**Attributes**:
- `username`: Username
- `display_name`: Display name
- `points`: All-time points
- `weekly_points`: Current week points

### Services

#### `choreboard.mark_complete`

Mark a chore as completed, optionally with helpers and on behalf of another user.

**Parameters**:
- `chore_id` (required): The chore instance ID
- `helpers` (optional): List of user IDs who helped (will receive partial points)
- `completed_by_user_id` (optional): User ID to complete on behalf of (defaults to authenticated user)

**Examples**:

```yaml
# Simple completion
service: choreboard.mark_complete
data:
  chore_id: 42

# With helpers
service: choreboard.mark_complete
data:
  chore_id: 42
  helpers: [2, 3]

# Complete on behalf of another user
service: choreboard.mark_complete
data:
  chore_id: 42
  completed_by_user_id: 5

# Complete with helpers on behalf of another user
service: choreboard.mark_complete
data:
  chore_id: 42
  helpers: [2, 3]
  completed_by_user_id: 5
```

#### `choreboard.claim_chore`

Claim a pool chore for yourself or assign it to another user.

**Parameters**:
- `chore_id` (required): The pool chore instance ID
- `assign_to_user_id` (optional): User ID to assign to (defaults to authenticated user)

**Examples**:

```yaml
# Claim for yourself
service: choreboard.claim_chore
data:
  chore_id: 42

# Assign to another user
service: choreboard.claim_chore
data:
  chore_id: 42
  assign_to_user_id: 3
```

#### `choreboard.undo_completion`

Undo a chore completion (admin only).

**Parameters**:
- `chore_id` (required): The completion ID to undo

**Example**:

```yaml
service: choreboard.undo_completion
data:
  chore_id: 123
```

### Example Automations

#### Notify when pool chores are available

```yaml
automation:
  - alias: "Pool Chores Available"
    trigger:
      - platform: numeric_state
        entity_id: sensor.pool_chores
        above: 0
    action:
      - service: notify.family
        data:
          title: "Chores Available"
          message: >
            {{ states('sensor.pool_chores') }} chores are available in the pool!
```

#### Remind about overdue chores

```yaml
automation:
  - alias: "Late Chore Reminder"
    trigger:
      - platform: time
        at: "09:00:00"
    condition:
      - condition: numeric_state
        entity_id: sensor.late_chores
        above: 0
    action:
      - service: notify.persistent_notification
        data:
          title: "Overdue Chores"
          message: >
            You have {{ states('sensor.late_chores') }} overdue chores!
```

#### Weekly leaderboard announcement

```yaml
automation:
  - alias: "Weekly Leaderboard"
    trigger:
      - platform: time
        at: "20:00:00"
    condition:
      - condition: time
        weekday:
          - sun
    action:
      - service: notify.family
        data:
          title: "Weekly Leaderboard"
          message: >
            This week's leader: {{ state_attr('sensor.leaderboard_weekly', 'users')[0]['name'] }}
            with {{ state_attr('sensor.leaderboard_weekly', 'users')[0]['points'] }} points!
```

#### Auto-complete chore from button press

```yaml
automation:
  - alias: "Complete Chore Button"
    trigger:
      - platform: event
        event_type: zha_event
        event_data:
          device_id: button_device_id
          command: "on"
    action:
      - service: choreboard.mark_complete
        data:
          chore_id: >
            {{ state_attr('sensor.john_my_immediate_chores', 'chores')[0]['id'] }}
```

## Development

See [CLAUDE.md](CLAUDE.md) for detailed development instructions.

### Local Development Setup

For developers: This integration is developed alongside the ChoreBoard backend, which is available at `../ChoreBoard` for local development and testing. You have full access to modify the ChoreBoard API as needed to support integration features.

For production deployments, users will configure their own ChoreBoard backend URL when setting up the integration in Home Assistant.

### Quick Start

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements_dev.txt

# Setup pre-commit hooks
pre-commit install

# Run tests
pytest tests/ -v

# Run linting
ruff check .
mypy custom_components/choreboard/
```

## Support

For issues and feature requests, please use the [GitHub issue tracker](https://github.com/PhunkMaster/ChoreBoard-HA-Integration/issues).

## License

This project is licensed under the MIT License.
