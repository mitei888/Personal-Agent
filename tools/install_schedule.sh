#!/bin/zsh
# Install (or re-install) on THIS Mac: 15-min reminders, Friday Adele check, and two watchers
# (re-run this script when it changes; restart Bob when his instructions change).
# Usage:  tools/install_schedule.sh          install / update
#         tools/install_schedule.sh off      remove
set -e
LABEL=com.personalagent.remind
PLIST=~/Library/LaunchAgents/$LABEL.plist
ROOT=${0:A:h:h}
PY=${PYTHON:-$(command -v python3)}

ALABEL=com.personalagent.adele
APLIST=~/Library/LaunchAgents/$ALABEL.plist
# Watcher: re-runs THIS script automatically whenever git pull changes it,
# so after the first manual run you never need to run it by hand again.
WLABEL=com.personalagent.schedwatch
WPLIST=~/Library/LaunchAgents/$WLABEL.plist
# Bob watcher: restarts Bob when CLAUDE.md / .claude/agents / .claude/settings.json change.
BLABEL=com.personalagent.bobwatch
BPLIST=~/Library/LaunchAgents/$BLABEL.plist
launchctl bootout gui/$(id -u)/$LABEL 2>/dev/null || true
launchctl bootout gui/$(id -u)/$ALABEL 2>/dev/null || true
if [[ "$1" == "off" ]]; then
  launchctl bootout gui/$(id -u)/$WLABEL 2>/dev/null || true
  launchctl bootout gui/$(id -u)/$BLABEL 2>/dev/null || true
  rm -f "$PLIST" "$APLIST" "$WPLIST" "$BPLIST"; echo "reminder + Adele schedules and both watchers removed"; exit 0
fi
PY=${PY:A}   # absolute path, so launchd uses the same Python as this manual run

"$PY" -c "import yaml, icalendar, recurring_ical_events" || {
  echo "Missing Python packages. Run:  $PY -m pip install --user pyyaml icalendar recurring-ical-events"; exit 1; }

mkdir -p ~/Library/LaunchAgents
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array><string>$PY</string><string>$ROOT/tools/remind.py</string></array>
  <key>StartInterval</key><integer>900</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardErrorPath</key><string>$ROOT/tools/remind.err</string>
</dict>
</plist>
EOF
launchctl bootstrap gui/$(id -u) "$PLIST"
echo "reminder schedule installed: $PY $ROOT/tools/remind.py every 15 min"

# Friday 20:00 Adele check (read-only; DMs if next week has < 2 sessions)
cat > "$APLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$ALABEL</string>
  <key>ProgramArguments</key>
  <array><string>$PY</string><string>$ROOT/tools/adele_check.py</string></array>
  <key>StartCalendarInterval</key>
  <dict><key>Weekday</key><integer>5</integer><key>Hour</key><integer>20</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardErrorPath</key><string>$ROOT/tools/adele.err</string>
</dict>
</plist>
EOF
launchctl bootstrap gui/$(id -u) "$APLIST"
echo "Adele check installed: Fridays 20:00 (this Mac's local time)"

# Bob watcher (installed/updated on every run, including watcher-triggered ones)
launchctl bootout gui/$(id -u)/$BLABEL 2>/dev/null || true
cat > "$BPLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$BLABEL</string>
  <key>ProgramArguments</key>
  <array><string>/bin/zsh</string><string>$ROOT/tools/restart_bob_if_changed.sh</string></array>
  <key>EnvironmentVariables</key>
  <dict><key>PYTHON</key><string>$PY</string></dict>
  <key>WatchPaths</key>
  <array>
    <string>$ROOT/CLAUDE.md</string>
    <string>$ROOT/.claude/settings.json</string>
    <string>$ROOT/.claude/agents</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>ThrottleInterval</key><integer>60</integer>
  <key>StandardOutPath</key><string>$ROOT/tools/bobwatch.log</string>
  <key>StandardErrorPath</key><string>$ROOT/tools/bobwatch.log</string>
</dict>
</plist>
EOF
launchctl bootstrap gui/$(id -u) "$BPLIST"
echo "Bob watcher installed: Bob restarts automatically when his instructions change"

# Install the watcher once (skipped when the watcher itself is running this script).
if [[ -z "$FROM_SCHEDWATCH" ]]; then
  launchctl bootout gui/$(id -u)/$WLABEL 2>/dev/null || true
  cat > "$WPLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$WLABEL</string>
  <key>ProgramArguments</key>
  <array><string>/bin/zsh</string><string>$ROOT/tools/install_schedule.sh</string></array>
  <key>EnvironmentVariables</key>
  <dict><key>FROM_SCHEDWATCH</key><string>1</string><key>PYTHON</key><string>$PY</string></dict>
  <key>WatchPaths</key>
  <array><string>$ROOT/tools/install_schedule.sh</string></array>
  <key>StandardOutPath</key><string>$ROOT/tools/schedwatch.log</string>
  <key>StandardErrorPath</key><string>$ROOT/tools/schedwatch.log</string>
</dict>
</plist>
EOF
  launchctl bootstrap gui/$(id -u) "$WPLIST"
  echo "watcher installed: this script re-runs automatically whenever git pull changes it"
else
  echo "$(date '+%F %T') re-installed by watcher"
fi
