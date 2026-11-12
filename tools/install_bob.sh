#!/bin/zsh
# Install (or re-install) the launchd job that starts Bob in tmux at login.
# Usage:  tools/install_bob.sh          install / update
#         tools/install_bob.sh off      remove
set -e
LABEL=com.personalagent.bob
PLIST=~/Library/LaunchAgents/$LABEL.plist
ROOT=${0:A:h:h}

RLABEL=com.personalagent.bobrefresh
RPLIST=~/Library/LaunchAgents/$RLABEL.plist

launchctl bootout gui/$(id -u)/$LABEL 2>/dev/null || true
launchctl bootout gui/$(id -u)/$RLABEL 2>/dev/null || true
if [[ "$1" == "off" ]]; then rm -f "$PLIST" "$RPLIST"; echo "Bob autostart, watchdog and daily refresh removed"; exit 0; fi

chmod +x "$ROOT/tools/start_bob.sh"
mkdir -p ~/Library/LaunchAgents
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array><string>$ROOT/tools/start_bob.sh</string></array>
  <key>RunAtLoad</key><true/>
  <key>StartInterval</key><integer>120</integer>
  <key>EnvironmentVariables</key>
  <dict><key>PYTHON</key><string>/usr/local/bin/python3</string></dict>
  <key>AbandonProcessGroup</key><true/>
  <key>StandardOutPath</key><string>$ROOT/tools/bob.log</string>
  <key>StandardErrorPath</key><string>$ROOT/tools/bob.log</string>
</dict>
</plist>
EOF
launchctl bootstrap gui/$(id -u) "$PLIST"
echo "Bob autostart + watchdog installed: start_bob.sh runs at login and every 2 min"

# Daily fresh conversation: hourly check (at :05), acts once a day 04:00-06:59 in Miranda's time zone.
chmod +x "$ROOT/tools/refresh_bob.sh"
cat > "$RPLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$RLABEL</string>
  <key>ProgramArguments</key>
  <array><string>$ROOT/tools/refresh_bob.sh</string><string>--daily</string></array>
  <key>StartCalendarInterval</key><dict><key>Minute</key><integer>5</integer></dict>
  <key>EnvironmentVariables</key>
  <dict><key>PYTHON</key><string>/usr/local/bin/python3</string></dict>
  <key>AbandonProcessGroup</key><true/>
  <key>StandardOutPath</key><string>$ROOT/tools/bob.log</string>
  <key>StandardErrorPath</key><string>$ROOT/tools/bob.log</string>
</dict>
</plist>
EOF
launchctl bootstrap gui/$(id -u) "$RPLIST"
echo "Daily refresh installed: fresh Bob once a day 04:00-06:59 her time (skips while busy)"
