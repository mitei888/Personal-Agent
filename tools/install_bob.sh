#!/bin/zsh
# Install (or re-install) the launchd job that starts Bob in tmux at login.
# Usage:  tools/install_bob.sh          install / update
#         tools/install_bob.sh off      remove
set -e
LABEL=com.personalagent.bob
PLIST=~/Library/LaunchAgents/$LABEL.plist
ROOT=${0:A:h:h}

launchctl bootout gui/$(id -u)/$LABEL 2>/dev/null || true
if [[ "$1" == "off" ]]; then rm -f "$PLIST"; echo "Bob autostart removed"; exit 0; fi

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
  <key>AbandonProcessGroup</key><true/>
  <key>StandardOutPath</key><string>$ROOT/tools/bob.log</string>
  <key>StandardErrorPath</key><string>$ROOT/tools/bob.log</string>
</dict>
</plist>
EOF
launchctl bootstrap gui/$(id -u) "$PLIST"
echo "Bob autostart installed: runs $ROOT/tools/start_bob.sh at every login"
