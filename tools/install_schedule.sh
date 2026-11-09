#!/bin/zsh
# Install (or re-install) the 15-minute reminder/briefing job for THIS Mac.
# Usage:  tools/install_schedule.sh          install / update
#         tools/install_schedule.sh off      remove
set -e
LABEL=com.personalagent.remind
PLIST=~/Library/LaunchAgents/$LABEL.plist
ROOT=${0:A:h:h}
PY=${PYTHON:-$(command -v python3)}

launchctl bootout gui/$(id -u)/$LABEL 2>/dev/null || true
if [[ "$1" == "off" ]]; then rm -f "$PLIST"; echo "reminder schedule removed"; exit 0; fi

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
