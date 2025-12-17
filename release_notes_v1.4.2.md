## ChoreBoard Home Assistant Integration v1.4.2

### Testing
- Successfully tested auto-release workflow with squash merge detection
- Verified github-actions bot can detect and parse semver branch names from squash merges

### Workflow Status

✅ **Working:**
- Squash merge detection via GitHub API
- Branch name extraction from PR number
- Semver pattern matching
- Version detection (1.4.2)
- Manifest.json update preparation

⚠️ **Blocked by Repository Rulesets:**
- Bot cannot push manifest updates to main branch
- Repository rulesets require code owner approval
- Bypass actors feature not available in current GitHub plan

### Note on manifest.json

The manifest.json version remains at 1.4.1 because the automated push was blocked by repository rulesets. This is a test release to verify the workflow detection logic - a separate PR can update the manifest version if needed.

### Installation

1. Download `choreboard.zip` from the assets below
2. Extract to your Home Assistant `custom_components` directory
3. Restart Home Assistant
4. Add the ChoreBoard integration via Settings → Devices & Services

### Requirements

- Home Assistant 2024.1.0 or newer
- ChoreBoard backend API

### Next Steps

The auto-release workflow will be adjusted to work within repository ruleset constraints by either:
- Creating a PR for manifest updates instead of direct push
- Documenting manual manifest update process
- Using GitHub Apps with proper permissions
