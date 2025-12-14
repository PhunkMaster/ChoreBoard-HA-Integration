# ChoreBoard Home Assistant Integration

A Home Assistant custom integration for ChoreBoard, enabling you to track chores, assignments, and completion status directly within Home Assistant.

## Features

- Track chore status as sensors (pending, completed, overdue)
- Binary sensors for chore completion status
- View chore details including assignee, due date, and points
- Services to mark chores as complete and assign chores
- Automatic polling of ChoreBoard API for updates

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
4. Enter your ChoreBoard API credentials:
   - API Key
   - API URL (optional, defaults to https://api.choreboard.com)
5. Click "Submit"

## Usage

### Sensors

The integration creates sensors for each chore:
- **Sensor**: Shows the current status of the chore (pending, completed, overdue)
- **Binary Sensor**: Shows whether the chore is completed (on) or not (off)

Each sensor includes attributes:
- `assignee`: Person assigned to the chore
- `due_date`: When the chore is due
- `points`: Point value of the chore
- `description`: Chore description

### Services

#### `choreboard.mark_complete`

Mark a chore as completed.

```yaml
service: choreboard.mark_complete
data:
  entity_id: sensor.choreboard_wash_dishes
  notes: "All dishes cleaned and put away"
```

#### `choreboard.assign_chore`

Assign a chore to a user.

```yaml
service: choreboard.assign_chore
data:
  chore_id: "chore_123"
  assignee: "John"
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
