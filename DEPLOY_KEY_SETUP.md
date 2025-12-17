# Deploy Key Setup for Auto-Release Workflow

This document provides step-by-step instructions for configuring SSH deploy keys to allow the auto-release workflow to push manifest.json updates to the main branch while respecting repository rulesets.

## Overview

The auto-release workflow needs to push manifest.json version updates directly to the main branch after creating a release. Since repository rulesets prevent the built-in `github-actions[bot]` from bypassing protection rules, we use **SSH deploy keys** with bypass permissions.

## Prerequisites

- Repository admin access
- SSH client installed locally (for key generation)
- Repository must be using **rulesets** (not legacy branch protection)

## Setup Steps

### Step 1: Generate SSH Deploy Key

Open a terminal and generate a new SSH key pair:

```bash
ssh-keygen -t ed25519 -C "auto-release-workflow" -f ./deploy_key -N ""
```

This creates two files:
- `deploy_key` - Private key (keep secret, add to GitHub secrets)
- `deploy_key.pub` - Public key (add to repository deploy keys)

**Important**: Use an empty passphrase (`-N ""`) as GitHub Actions cannot interactively enter passphrases.

### Step 2: Add Public Key as Deploy Key

1. Navigate to your repository on GitHub
2. Go to **Settings** → **Deploy keys**
3. Click **Add deploy key**
4. Configure the deploy key:
   - **Title**: `Auto-Release Workflow`
   - **Key**: Paste the contents of `deploy_key.pub`
   - **Allow write access**: ✅ **Check this box** (required for pushing)
5. Click **Add key**

### Step 3: Add Private Key as Repository Secret

1. In your repository, go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Configure the secret:
   - **Name**: `DEPLOY_KEY`
   - **Secret**: Paste the entire contents of the `deploy_key` file (private key)
4. Click **Add secret**

**Security Note**: After adding the private key to GitHub, **securely delete** both key files from your local machine:

```bash
rm deploy_key deploy_key.pub
```

### Step 4: Add Deploy Keys to Ruleset Bypass List

1. Go to **Settings** → **Rules** → **Rulesets**
2. Click on your **Main** ruleset (or the ruleset protecting your main branch)
3. Click **Edit** (top right)
4. Scroll to the **Bypass list** section
5. Click **Add bypass**
6. In the modal dialog:
   - Search for or select **Deploy keys**
   - Click **Add selected**
7. (Optional) To restrict bypass to pull requests only:
   - Next to the "Deploy keys" bypass actor, click the **⋮** menu icon
   - Select **For pull requests only**
   - **Note**: For our workflow, we need direct push capability, so leave it as "Always allow"
8. Scroll to the bottom and click **Save changes**

### Step 5: Verify Workflow Configuration

The auto-release workflow (`.github/workflows/auto-release.yml`) should already be configured to use the deploy key:

```yaml
- name: Checkout code
  uses: actions/checkout@v6
  with:
    fetch-depth: 0
    ssh-key: ${{ secrets.DEPLOY_KEY }}
    persist-credentials: false
```

**Key parameters**:
- `ssh-key: ${{ secrets.DEPLOY_KEY }}` - Uses the deploy key for authentication
- `persist-credentials: false` - Prevents using the default GITHUB_TOKEN (which cannot bypass rulesets)

## Testing the Setup

Create a test branch and PR to verify the workflow:

1. Create a test branch with semantic versioning:
   ```bash
   git checkout -b bugfix/1.4.3
   ```

2. Make a small change (e.g., update CHANGELOG.md):
   ```bash
   echo "## [1.4.3] - $(date +%Y-%m-%d)" >> CHANGELOG.md
   echo "" >> CHANGELOG.md
   echo "### Testing" >> CHANGELOG.md
   echo "- Test deploy key auto-release workflow" >> CHANGELOG.md
   git add CHANGELOG.md
   git commit -m "test: Verify deploy key workflow"
   git push -u origin bugfix/1.4.3
   ```

3. Create and merge a pull request via GitHub web interface

4. Monitor the auto-release workflow:
   - Go to **Actions** tab
   - Click on the latest "Auto Release on Semver Branch Merge" workflow run
   - Verify these steps succeed:
     - ✅ Get merged branch name
     - ✅ Check if branch is semver and create release
     - ✅ Update manifest.json version
     - ✅ **Commit and push manifest.json update** ← This should now succeed
     - ✅ Generate release notes
     - ✅ Create GitHub Release

5. Verify the results:
   - Check that `custom_components/choreboard/manifest.json` version was updated to 1.4.3
   - Verify a new release `v1.4.3` was created in the Releases page
   - Confirm the release includes `choreboard.zip` asset (uploaded by release.yml workflow)

## Troubleshooting

### "Permission denied (publickey)" Error

**Cause**: Private key not properly added to repository secrets, or public key not added as deploy key.

**Solution**:
- Verify `DEPLOY_KEY` secret exists and contains the complete private key (including `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----`)
- Ensure the public key was added as a deploy key with write access enabled

### "Protected branch update failed" Error

**Cause**: Deploy keys not added to ruleset bypass list, or deploy key doesn't have write access.

**Solution**:
- Verify "Deploy keys" appears in the ruleset's bypass list
- Confirm the deploy key has "Allow write access" checked in Settings → Deploy keys
- Ensure you're editing the correct ruleset (the one protecting the main branch)

### Workflow Fails at Checkout Step

**Cause**: `DEPLOY_KEY` secret doesn't exist or contains invalid key data.

**Solution**:
- Regenerate the SSH key pair
- Ensure you're copying the **private key** (not the .pub file) to the secret
- Verify the key has no passphrase (empty passphrase)

### manifest.json Not Updated After Release

**Cause**: Workflow succeeded but push was blocked by other ruleset rules.

**Solution**:
- Check workflow logs for specific error messages
- Verify status checks are not required, or that they pass before the push
- Ensure no other ruleset rules are blocking the push

## Security Considerations

### Deploy Key Scope

- Deploy keys are scoped to a **single repository** (unlike personal access tokens)
- Only grants access to this specific repository
- More secure than using a personal access token or bot account

### Audit Trail

- All commits made using the deploy key will show as `github-actions[bot]`
- Push events are logged in the repository's audit log
- The bypass action is recorded for compliance

### Key Rotation

To rotate the deploy key:

1. Generate a new SSH key pair
2. Add the new public key as a deploy key
3. Update the `DEPLOY_KEY` secret with the new private key
4. Test the workflow with a test branch/PR
5. Remove the old deploy key from Settings → Deploy keys

Recommended rotation frequency: **Annually** or when team members with access to secrets leave the project.

## References

- [GitHub Actions: Checkout Action](https://github.com/actions/checkout)
- [GitHub Docs: Managing Deploy Keys](https://docs.github.com/en/developers/overview/managing-deploy-keys)
- [GitHub Docs: Repository Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- [GitHub Community Discussion: Allowing github-actions to push to protected branches](https://github.com/orgs/community/discussions/25305)

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ PR Merged to Main (bugfix/1.4.3)                                │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ Auto-Release Workflow Triggered                                 │
│ - Detects semver branch name (bugfix/1.4.3)                     │
│ - Extracts version (1.4.3)                                      │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ Checkout with Deploy Key                                        │
│ - actions/checkout@v6 with ssh-key: ${{ secrets.DEPLOY_KEY }}  │
│ - Configures git to use SSH authentication                      │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ Update manifest.json                                            │
│ - Changes version: "1.4.2" → "1.4.3"                           │
│ - Commits with message: "chore: Update manifest.json..."        │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ Push to Main Branch                                             │
│ - Uses deploy key (bypasses ruleset)                            │
│ - Ruleset allows deploy keys in bypass list                     │
│ - Push succeeds ✅                                              │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ Create GitHub Release                                           │
│ - Tag: v1.4.3                                                   │
│ - Generate release notes from commits                           │
│ - Trigger release.yml workflow to upload ZIP                    │
└─────────────────────────────────────────────────────────────────┘
```

## Summary

With deploy keys configured:
- ✅ Auto-release workflow can push to protected main branch
- ✅ Repository rulesets remain enforced for human contributors
- ✅ Fully automated release process (no manual PR approvals needed)
- ✅ Secure and scoped authentication (single repository only)
- ✅ Complete audit trail maintained
