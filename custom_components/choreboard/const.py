"""Constants for the ChoreBoard integration."""

from datetime import timedelta

# Integration domain
DOMAIN = "choreboard"

# Configuration keys
CONF_USERNAME = "username"
CONF_SECRET_KEY = "secret_key"
CONF_URL = "url"
CONF_MONITORED_USERS = "monitored_users"

# Default values
DEFAULT_NAME = "ChoreBoard"
DEFAULT_URL = "http://localhost:8000"  # Development default
DEFAULT_SCAN_INTERVAL = timedelta(minutes=5)
TOKEN_REFRESH_INTERVAL = timedelta(hours=23)  # Refresh before 24h expiry

# Platforms
PLATFORMS = ["sensor"]

# Service names
SERVICE_MARK_COMPLETE = "mark_complete"
SERVICE_CLAIM_CHORE = "claim_chore"
SERVICE_UNDO_COMPLETION = "undo_completion"

# Attributes
ATTR_ASSIGNEE = "assignee"
ATTR_DUE_DATE = "due_date"
ATTR_POINTS = "points"
ATTR_NOTES = "notes"
ATTR_CHORE_ID = "chore_id"
ATTR_HELPERS = "helpers"
ATTR_IS_POOL = "is_pool"
ATTR_IS_OVERDUE = "is_overdue"
ATTR_COMPLETED_AT = "completed_at"
ATTR_WEEKLY_POINTS = "weekly_points"
ATTR_ALL_TIME_POINTS = "all_time_points"

# Sensor types
SENSOR_TYPE_MY_CHORES = "my_chores"
SENSOR_TYPE_OUTSTANDING = "outstanding"
SENSOR_TYPE_LATE = "late"
SENSOR_TYPE_LEADERBOARD_WEEKLY = "leaderboard_weekly"
SENSOR_TYPE_LEADERBOARD_ALLTIME = "leaderboard_alltime"

# API Endpoints
API_ENDPOINT_OUTSTANDING = "/api/outstanding/"
API_ENDPOINT_LATE = "/api/late-chores/"
API_ENDPOINT_MY_CHORES = "/api/my-chores/"
API_ENDPOINT_LEADERBOARD = "/api/leaderboard/"
API_ENDPOINT_CLAIM = "/api/claim/"
API_ENDPOINT_COMPLETE = "/api/complete/"
API_ENDPOINT_UNDO = "/api/undo/"
