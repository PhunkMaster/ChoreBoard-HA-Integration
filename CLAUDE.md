# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Home Assistant custom integration for ChoreBoard, a chore management system. The integration enables Home Assistant to interact with ChoreBoard's API to track chores, assignments, and completion status as sensors and services.

- **Integration Type**: Service (cloud-based API integration)
- **Target HA Version**: 2024.1.0 or later
- **Domain**: `choreboard`

## Local Development Environment

**IMPORTANT**: For development purposes, the ChoreBoard backend project is located at `../ChoreBoard` (sibling directory). You have full access to make changes to the ChoreBoard backend API as needed while developing this integration.

This means for development:
- You can modify ChoreBoard API endpoints to support integration features
- You can add new API methods or fields as needed
- You can test the integration against the local ChoreBoard instance at `../ChoreBoard`
- API changes should be coordinated between both projects

When implementing features that require API changes, update both repositories:
1. Add/modify API endpoints in `../ChoreBoard`
2. Implement integration code in this repository to consume those endpoints

**Production Note**: In production, users will configure their own ChoreBoard backend URL during the integration setup via the config flow. The `../ChoreBoard` location is only relevant for development and testing.

## Project Structure

```
custom_components/choreboard/
├── __init__.py              # Integration setup, config entry management, service registration
├── manifest.json            # Integration metadata, dependencies, and requirements
├── config_flow.py           # Configuration UI flow for setting up the integration
├── coordinator.py           # DataUpdateCoordinator for efficient API polling
├── const.py                 # Constants, configuration keys, and domain definition
├── sensor.py                # Sensor platform entities (chore status, assignments, etc.)
├── binary_sensor.py         # Binary sensor entities (chore completion flags)
├── strings.json             # Translations for config flow and services
└── services.yaml            # Service definitions (mark_complete, assign_chore, etc.)

tests/
├── conftest.py              # Pytest fixtures and test configuration
├── test_config_flow.py      # Tests for configuration flow
├── test_coordinator.py      # Tests for data coordinator
├── test_sensor.py           # Tests for sensor entities
└── test_init.py             # Tests for integration setup

.pre-commit-config.yaml      # Pre-commit hooks (ruff, mypy, etc.)
requirements_dev.txt         # Development dependencies
```

## Development Setup

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install development dependencies
pip install pytest-homeassistant-custom-component ruff mypy pre-commit

# Setup pre-commit hooks
pre-commit install

# Symlink to Home Assistant config for testing
# Windows: mklink /D "%USERPROFILE%\.homeassistant\custom_components\choreboard" "custom_components\choreboard"
# Linux/Mac: ln -s $(pwd)/custom_components/choreboard ~/.homeassistant/custom_components/
```

## Common Development Commands

```bash
# Testing
pytest tests/ -v                                    # Run all tests with verbose output
pytest tests/ --cov=custom_components.choreboard    # Run tests with coverage report
pytest tests/ --snapshot-update                     # Update snapshot tests
pytest tests/test_config_flow.py -k test_form       # Run specific test

# Linting and Type Checking
ruff check .                                        # Check for linting issues
ruff format .                                       # Format code (replaces black)
mypy custom_components/choreboard/                 # Type checking
pre-commit run --all-files                         # Run all pre-commit hooks

# Validation
# Use hassfest via GitHub Actions (preferred)
# Or run locally if hassfest is installed

# Testing in Home Assistant
# 1. Ensure symlink is created (see Development Setup)
# 2. Restart Home Assistant
# 3. Check logs: config/home-assistant.log
# 4. Add integration via UI: Settings > Devices & Services > Add Integration
```

## Key Architectural Patterns

### 1. Config Flow Pattern

Config flows provide the UI for configuring the integration. Implement in `config_flow.py`:

```python
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

class ChoreboardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ChoreBoard."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate user input (API key, URL, etc.)
            try:
                # Test API connection
                await self._test_credentials(user_input[CONF_API_KEY])
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                # Create the config entry
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )

        # Show the form to the user
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_URL): str,
            }),
            errors=errors,
        )
```

### 2. Coordinator Pattern

Use `DataUpdateCoordinator` for efficient data fetching. All entities subscribe to a single coordinator:

```python
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

class ChoreboardCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch data from ChoreBoard API."""

    def __init__(self, hass, api_client):
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="ChoreBoard",
            update_interval=timedelta(minutes=5),  # Poll every 5 minutes
        )
        self.api_client = api_client

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            # Fetch data from API
            return await self.api_client.async_get_chores()
        except AuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}")
        except APIError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
```

In `__init__.py`, create the coordinator during setup:

```python
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ChoreBoard from a config entry."""
    api_client = ChoreboardAPIClient(entry.data[CONF_API_KEY])

    coordinator = ChoreboardCoordinator(hass, api_client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True
```

### 3. Entity Implementation

Entities use `CoordinatorEntity` to subscribe to coordinator updates:

```python
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorEntity

class ChoreboardChoreEntity(CoordinatorEntity, SensorEntity):
    """Representation of a ChoreBoard chore sensor."""

    def __init__(self, coordinator, chore_id):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._chore_id = chore_id
        self._attr_unique_id = f"{DOMAIN}_{chore_id}"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP  # If tracking due dates

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.coordinator.data[self._chore_id]["name"]

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data[self._chore_id]["status"]

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        chore = self.coordinator.data[self._chore_id]
        return {
            "assignee": chore.get("assignee"),
            "due_date": chore.get("due_date"),
            "points": chore.get("points"),
        }
```

Platform setup in `sensor.py`:

```python
async def async_setup_entry(hass, entry, async_add_entities):
    """Set up ChoreBoard sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        ChoreboardChoreEntity(coordinator, chore_id)
        for chore_id in coordinator.data.keys()
    ]

    async_add_entities(entities)
```

### 4. Service Registration

Define services in `services.yaml`:

```yaml
mark_complete:
  name: Mark Chore Complete
  description: Mark a chore as completed
  fields:
    entity_id:
      name: Entity
      description: The chore entity to mark complete
      required: true
      selector:
        entity:
          domain: sensor
          integration: choreboard
    notes:
      name: Notes
      description: Optional completion notes
      required: false
      selector:
        text:
```

Register services in `__init__.py`:

```python
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ChoreBoard from a config entry."""
    # ... coordinator setup ...

    # Register services
    async def handle_mark_complete(call):
        """Handle the mark_complete service call."""
        entity_id = call.data["entity_id"]
        notes = call.data.get("notes", "")
        # Call API to mark complete
        await coordinator.api_client.mark_complete(entity_id, notes)
        await coordinator.async_request_refresh()

    hass.services.async_register(DOMAIN, "mark_complete", handle_mark_complete)

    return True
```

## manifest.json Requirements

The manifest.json must include these required fields:

```json
{
  "domain": "choreboard",
  "name": "ChoreBoard",
  "version": "1.0.0",
  "documentation": "https://github.com/PhunkMaster/ChoreBoard-HA-Integration",
  "codeowners": ["@PhunkMaster"],
  "config_flow": true,
  "dependencies": [],
  "requirements": ["aiohttp>=3.9.0"],
  "iot_class": "cloud_polling",
  "integration_type": "service"
}
```

**Key fields:**
- `domain`: Must match directory name and DOMAIN constant
- `config_flow`: Set to `true` for UI-based configuration
- `requirements`: Python packages from PyPI (will be installed by HA)
- `iot_class`: How the integration communicates (`cloud_polling`, `local_polling`, etc.)
- `integration_type`: `hub`, `service`, or `device`

## Testing Patterns

### Basic Test Structure

```python
from pytest_homeassistant_custom_component.common import MockConfigEntry

async def test_setup_entry(hass, aioclient_mock):
    """Test successful setup."""
    # Mock API responses
    aioclient_mock.get(
        "https://api.choreboard.com/chores",
        json={"chores": [{"id": "1", "name": "Dishes"}]},
    )

    # Create config entry
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_API_KEY: "test_key"},
    )
    entry.add_to_hass(hass)

    # Setup the integration
    assert await async_setup_entry(hass, entry)
    await hass.async_block_till_done()

    # Verify setup
    assert DOMAIN in hass.data
    assert entry.entry_id in hass.data[DOMAIN]
```

### Testing Config Flow

```python
async def test_form(hass):
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "user"

    # Test form submission
    with patch("custom_components.choreboard.config_flow.test_credentials"):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: "test_key"},
        )

    assert result["type"] == "create_entry"
    assert result["title"] == "ChoreBoard"
```

### Coverage Requirements

Aim for >80% test coverage. Focus on:
- Config flow validation and error handling
- Coordinator data fetching and error recovery
- Entity state calculation and attributes
- Service handlers

## HACS Integration

To make this integration installable via HACS:

1. **Repository Structure**: Must have `custom_components/choreboard/` at root
2. **Releases**: Use semantic versioning (e.g., `v1.0.0`) for release tags
3. **hacs.json** (optional): Create if custom configuration needed
4. **README.md**: Include installation instructions and screenshots

HACS validation checks:
- Valid manifest.json
- No Python syntax errors
- Proper repository structure
- GitHub releases with tags

## Development Workflow

Recommended implementation order:

1. **Create manifest.json**: Define integration metadata
2. **Create const.py**: Define domain, configuration keys, constants
3. **Implement config_flow.py**: Build configuration UI with validation
4. **Create API client**: Wrap ChoreBoard API calls (in separate module)
5. **Implement coordinator.py**: Set up DataUpdateCoordinator
6. **Create __init__.py**: Integration setup and service registration
7. **Implement sensor.py**: Create sensor entities using coordinator
8. **Add strings.json**: Translations for config flow and services
9. **Write tests**: Comprehensive test coverage
10. **Test in real HA**: Symlink and test with actual Home Assistant instance
11. **Validate**: Run hassfest, linting, and type checking

## Common Issues & Debugging

### Config Flow Not Appearing
- Check `manifest.json` has `"config_flow": true`
- Verify domain matches directory name
- Restart Home Assistant completely
- Check logs for import errors

### Coordinator Update Failures
- Implement proper error handling in `_async_update_data`
- Raise `UpdateFailed` for expected errors
- Use appropriate retry logic (coordinator handles backoff)
- Log errors with context

### Entity Not Showing in UI
- Verify `unique_id` is set and truly unique
- Check entity is added via `async_add_entities`
- Ensure `device_class` is valid for entity type
- Verify coordinator has data before entity creation

### Translation Strings Not Loading
- Check `strings.json` structure matches HA format
- Ensure file is in correct location
- Verify keys match those in config_flow.py
- Restart HA after modifying strings.json

### Import Errors
- Check `requirements` in manifest.json
- Verify Python packages are importable
- Check for circular imports between modules
- Ensure all dependencies are async-compatible

## Code Quality Checklist

Before submitting PR or release:

- [ ] Hassfest validation passes (via GitHub Action)
- [ ] All tests pass: `pytest tests/`
- [ ] Test coverage >80%: `pytest tests/ --cov`
- [ ] Type checking passes: `mypy custom_components/choreboard/`
- [ ] Linting passes: `ruff check .`
- [ ] Code formatted: `ruff format .`
- [ ] No print statements (use logging)
- [ ] Error handling for all API calls
- [ ] Translations complete in strings.json
- [ ] README.md with installation and usage instructions
- [ ] All functions have type hints
- [ ] Constants used instead of magic strings

## Important Notes

- **Async-first**: Home Assistant is async-first. Use `async def` and `await` throughout
- **Type hints required**: All functions must have type hints for parameters and return values
- **Use constants**: Define constants in `const.py`, never use magic strings
- **Naming conventions**: Use snake_case for domains, entity IDs, and service names
- **Unique IDs**: Entity `unique_id` must be stable (never change) and globally unique
- **Logging**: Use `_LOGGER` from `logging.getLogger(__name__)`, not print()
- **Error handling**: Catch specific exceptions, provide helpful error messages

### Deprecation Warning

Legacy template entities are deprecated in Home Assistant 2025.12. Always inherit from proper entity base classes (`SensorEntity`, `BinarySensorEntity`, etc.) rather than using generic `Entity`.

## Development Resources

- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [Integration Manifest Reference](https://developers.home-assistant.io/docs/creating_integration_manifest/)
- [Config Flow Documentation](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/)
- [Data Coordinator Pattern](https://developers.home-assistant.io/docs/integration_fetching_data/)
- [Entity Documentation](https://developers.home-assistant.io/docs/core/entity/)
- [Testing Guide](https://developers.home-assistant.io/docs/development_testing/)
- [HACS Documentation](https://www.hacs.xyz/docs/publish/integration/)
- Always use semver branching