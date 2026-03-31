---
name: praxis-upgrade
version: 1.0.0
description: |
  Upgrade praxis to the latest version. Detects global vs vendored install,
  runs the upgrade, and shows what's new. Use when asked to "upgrade praxis",
  "update praxis", or "get latest version".
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---

# /praxis-upgrade

Upgrade praxis to the latest version and show what's new.

## Inline upgrade flow

This section is referenced by all skill preambles when they detect `UPGRADE_AVAILABLE`.

### Step 1: Ask the user (or auto-upgrade)

First, check if auto-upgrade is enabled:
```bash
_AUTO=""
[ "${PRAXIS_AUTO_UPGRADE:-}" = "1" ] && _AUTO="true"
[ -z "$_AUTO" ] && _AUTO=$(~/.claude/skills/praxis/bin/praxis-config get auto_upgrade 2>/dev/null || .claude/skills/praxis/bin/praxis-config get auto_upgrade 2>/dev/null || true)
echo "AUTO_UPGRADE=$_AUTO"
```

**If `AUTO_UPGRADE=true` or `AUTO_UPGRADE=1`:** Skip AskUserQuestion. Log
"Auto-upgrading praxis v{old} → v{new}..." and proceed directly to Step 2.
If upgrade fails, restore from backup and warn the user.

**Otherwise**, use AskUserQuestion:
- Question: "praxis **v{new}** is available (you're on v{old}). Upgrade now?"
- Options: ["Yes, upgrade now", "Always keep me up to date", "Not now", "Never ask again"]

**If "Yes, upgrade now":** Proceed to Step 2.

**If "Always keep me up to date":**
```bash
~/.claude/skills/praxis/bin/praxis-config set auto_upgrade true 2>/dev/null || \
.claude/skills/praxis/bin/praxis-config set auto_upgrade true 2>/dev/null || true
```
Tell user: "Auto-upgrade enabled. Future updates will install automatically."
Then proceed to Step 2.

**If "Not now":** Write snooze state with escalating backoff (first snooze = 24h,
second = 48h, third+ = 1 week), then continue with the current skill.
```bash
_SNOOZE_FILE=~/.praxis/update-snoozed
_REMOTE_VER="{new}"
_CUR_LEVEL=0
if [ -f "$_SNOOZE_FILE" ]; then
  _SNOOZED_VER=$(awk '{print $1}' "$_SNOOZE_FILE")
  if [ "$_SNOOZED_VER" = "$_REMOTE_VER" ]; then
    _CUR_LEVEL=$(awk '{print $2}' "$_SNOOZE_FILE")
    case "$_CUR_LEVEL" in *[!0-9]*) _CUR_LEVEL=0 ;; esac
  fi
fi
_NEW_LEVEL=$((_CUR_LEVEL + 1))
[ "$_NEW_LEVEL" -gt 3 ] && _NEW_LEVEL=3
echo "$_REMOTE_VER $_NEW_LEVEL $(date +%s)" > "$_SNOOZE_FILE"
```
Note: `{new}` is the remote version from `UPGRADE_AVAILABLE` — substitute from
the update check result.

Tell user the snooze duration: "Next reminder in 24h" (or 48h or 1 week).

**If "Never ask again":**
```bash
~/.claude/skills/praxis/bin/praxis-config set update_check false 2>/dev/null || \
.claude/skills/praxis/bin/praxis-config set update_check false 2>/dev/null || true
```
Tell user: "Update checks disabled. Run `praxis-config set update_check true` to
re-enable." Continue with the current skill.

### Step 2: Detect install type

```bash
if [ -d "$HOME/.claude/skills/praxis/.git" ]; then
  INSTALL_TYPE="global-git"
  INSTALL_DIR="$HOME/.claude/skills/praxis"
elif [ -d ".claude/skills/praxis/.git" ]; then
  INSTALL_TYPE="local-git"
  INSTALL_DIR=".claude/skills/praxis"
elif [ -d ".claude/skills/praxis" ]; then
  INSTALL_TYPE="vendored"
  INSTALL_DIR=".claude/skills/praxis"
elif [ -d "$HOME/.claude/skills/praxis" ]; then
  INSTALL_TYPE="vendored-global"
  INSTALL_DIR="$HOME/.claude/skills/praxis"
else
  echo "ERROR: praxis not found"
  exit 1
fi
echo "Install type: $INSTALL_TYPE at $INSTALL_DIR"
```

### Step 3: Save old version

```bash
OLD_VERSION=$(cat "$INSTALL_DIR/VERSION" 2>/dev/null || echo "unknown")
```

### Step 4: Upgrade

Use the install type and directory detected in Step 2:

**For git installs** (global-git, local-git):
```bash
cd "$INSTALL_DIR"
STASH_OUTPUT=$(git stash 2>&1)
git fetch origin
git reset --hard origin/prod
```
If `$STASH_OUTPUT` contains "Saved working directory", warn the user: "Note: local
changes were stashed. Run `git stash pop` in the skill directory to restore them."

**For vendored installs** (vendored, vendored-global):
```bash
PARENT=$(dirname "$INSTALL_DIR")
TMP_DIR=$(mktemp -d)
git clone --depth 1 -b prod https://github.com/aiwonglab/praxis.git "$TMP_DIR/praxis"
mv "$INSTALL_DIR" "$INSTALL_DIR.bak"
mv "$TMP_DIR/praxis" "$INSTALL_DIR"
rm -rf "$INSTALL_DIR.bak" "$TMP_DIR"
```

### Step 4.5: Sync local vendored copy

Check if there's also a local vendored copy that needs updating:

```bash
_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
LOCAL_PRAXIS=""
if [ -n "$_ROOT" ] && [ -d "$_ROOT/.claude/skills/praxis" ]; then
  _RESOLVED_LOCAL=$(cd "$_ROOT/.claude/skills/praxis" && pwd -P)
  _RESOLVED_PRIMARY=$(cd "$INSTALL_DIR" && pwd -P)
  if [ "$_RESOLVED_LOCAL" != "$_RESOLVED_PRIMARY" ]; then
    LOCAL_PRAXIS="$_ROOT/.claude/skills/praxis"
  fi
fi
echo "LOCAL_PRAXIS=$LOCAL_PRAXIS"
```

If `LOCAL_PRAXIS` is non-empty, update it from the freshly-upgraded primary:
```bash
mv "$LOCAL_PRAXIS" "$LOCAL_PRAXIS.bak"
cp -Rf "$INSTALL_DIR" "$LOCAL_PRAXIS"
rm -rf "$LOCAL_PRAXIS/.git"
rm -rf "$LOCAL_PRAXIS.bak"
```
Tell user: "Also updated vendored copy at `$LOCAL_PRAXIS` — commit
`.claude/skills/praxis/` when you're ready."

If copy fails, restore from backup:
```bash
rm -rf "$LOCAL_PRAXIS"
mv "$LOCAL_PRAXIS.bak" "$LOCAL_PRAXIS"
```

### Step 5: Write marker + clear cache

```bash
mkdir -p ~/.praxis
echo "$OLD_VERSION" > ~/.praxis/just-upgraded-from
rm -f ~/.praxis/last-update-check
rm -f ~/.praxis/update-snoozed
```

### Step 6: Show What's New

Read `$INSTALL_DIR/CHANGELOG.md`. Find all version entries between the old and new
version. Summarize as 3-5 bullets grouped by theme. Focus on user-facing changes.

Format:
```
praxis v{new} — upgraded from v{old}!

What's new:
- [bullet 1]
- [bullet 2]
- ...
```

### Step 7: Continue

After showing What's New, continue with whatever skill the user originally invoked.

---

## Standalone usage

When invoked directly as `/praxis-upgrade` (not from a preamble):

1. Force a fresh update check (bypass cache):
```bash
~/.claude/skills/praxis/bin/praxis-update-check --force 2>/dev/null || \
.claude/skills/praxis/bin/praxis-update-check --force 2>/dev/null || true
```

2. If `UPGRADE_AVAILABLE <old> <new>`: follow Steps 2-6 above.

3. If no output (primary is up to date): check for a stale local vendored copy.

Run the Step 2 bash block to detect install type and directory, then Step 4.5
to check for a local vendored copy.

**If `LOCAL_PRAXIS` is empty:** tell the user "You're already on the latest
version (v{version})."

**If `LOCAL_PRAXIS` is non-empty**, compare versions:
```bash
PRIMARY_VER=$(cat "$INSTALL_DIR/VERSION" 2>/dev/null || echo "unknown")
LOCAL_VER=$(cat "$LOCAL_PRAXIS/VERSION" 2>/dev/null || echo "unknown")
echo "PRIMARY=$PRIMARY_VER LOCAL=$LOCAL_VER"
```

**If versions differ:** sync the local copy and tell the user.
**If versions match:** tell the user both are up to date.
