## ChoreBoard Home Assistant Integration v1.4.1

### Fixed
- **Auto-Release Workflow** - Now handles squash merges correctly
  - Added support for detecting squash merge commits
  - Uses GitHub API to fetch branch name from PR number
  - Supports all three merge types: regular merge, branch merge, and squash merge

- **Release Workflow** - Fixed asset upload permissions
  - Replaced deprecated `actions/upload-release-asset@v1` with `gh release upload`
  - Added `contents: write` permission to workflow job
  - Resolves "Resource not accessible by integration" error

### Installation

1. Download `choreboard.zip` from the assets below
2. Extract to your Home Assistant `custom_components` directory
3. Restart Home Assistant
4. Add the ChoreBoard integration via Settings → Devices & Services

### Requirements

- Home Assistant 2024.1.0 or newer
- ChoreBoard backend API

### What's Changed

This is a maintenance release that fixes the automated release pipeline to work correctly with GitHub's squash merge feature. No functional changes to the integration itself.
