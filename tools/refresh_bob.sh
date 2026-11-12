#!/bin/zsh
# Give Bob a fresh conversation (files, reminders, memory are untouched — only the chat history resets).
#   refresh_bob.sh --daily   run hourly by launchd (com.personalagent.bobrefresh): refreshes once a day
#                            between 04:00 and 06:59 in Miranda's current time zone (trips.yaml),
#                            skipping any hour where Bob is busy or someone is typing in his session.
#   refresh_bob.sh --now     Miranda asked on Discord ("fresh start"): restart ~15 s from now, detached,
#                            so Bob can finish his reply first.
SESSION=${BOB_SESSION:-bob}
ROOT=${0:A:h:h}
T="$ROOT/tools"
export PATH="$HOME/.bun/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
PY=${PYTHON:-$(command -v python3)}
STATE="$T/.bob_refreshed_date"
log() { echo "$(date '+%F %T') $*"; }

restart() {
  tmux kill-session -t "$SESSION" 2>/dev/null
  sleep 2
  "$T/start_bob.sh"
}

case "$1" in
  --now)
    # nohup: survives the SIGHUP when the bob session (Bob's own process tree) is killed.
    nohup zsh -c "sleep 15; tmux kill-session -t '$SESSION' 2>/dev/null; sleep 2; '$T/start_bob.sh'" \
      >> "$T/bob.log" 2>&1 &
    log "fresh start requested from Discord — restarting in 15 s"
    exit 0 ;;
  --daily) ;;
  *) echo "usage: $0 --daily | --now"; exit 2 ;;
esac

# Miranda's local date and hour (trip tz if travelling, else Hong Kong).
read -r LDATE LHOUR <<< "$(cd "$T" && "$PY" -c '
from datetime import datetime, timezone
import remind
now = datetime.now(timezone.utc)
tz = remind.local_tz(now.astimezone(remind.ZoneInfo(remind.HOME_TZ)).date())
l = now.astimezone(tz)
print(l.date().isoformat(), l.hour)')" || exit 0
[[ -z "$LHOUR" ]] && exit 0
(( LHOUR >= 4 && LHOUR <= 6 )) || exit 0
[[ "$(cat "$STATE" 2>/dev/null)" == "$LDATE" ]] && exit 0
tmux has-session -t "$SESSION" 2>/dev/null || exit 0     # Bob not running: the watchdog handles that

# Busy? (Claude shows "esc to interrupt" while working) or someone typed in the session in the last 10 min.
if tmux list-panes -s -t "$SESSION" -F '#{pane_id}' | while read p; do
     tmux capture-pane -p -t "$p" | grep -v '^[[:space:]]*$' | tail -4; done | grep -qi "esc to interrupt"; then
  log "daily refresh: Bob busy at hour $LHOUR, will retry next hour"; exit 0
fi
last=$(tmux list-clients -t "$SESSION" -F '#{client_activity}' 2>/dev/null | sort -n | tail -1)
[[ -n "$last" ]] && (( $(date +%s) - last < 600 )) && { log "daily refresh: session in use, retry next hour"; exit 0; }

echo "$LDATE" > "$STATE"
restart
log "daily refresh: Bob restarted with a fresh conversation"
