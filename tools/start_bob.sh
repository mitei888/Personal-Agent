#!/bin/zsh
# Start Bob (the supervisor Claude session with the Discord channel) inside a
# detached tmux session called "bob", and keep him alive.
# Run by launchd (install_bob.sh) at login AND every 2 minutes as a watchdog:
#   - no tmux session            -> start Bob
#   - session but Claude exited  -> restart Bob and DM Miranda
#       (max 3 restarts per 30 min; then one "needs you" DM and it stops trying until Bob is healthy)
#       (skipped while someone is actively typing in the bob session, or while tools/.bob_pause exists)
#   - Bob stuck on a menu/prompt -> DM Miranda once (never presses keys for her)
#   - otherwise                  -> silent
# Attach with:  tmux attach -t bob      Pause the watchdog:  touch ~/Personal_Agent/tools/.bob_pause
SESSION=${BOB_SESSION:-bob}
ROOT=${0:A:h:h}
export PATH="$HOME/.bun/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
PY=${PYTHON:-$(command -v python3)}
T="$ROOT/tools"
STUCK_FLAG="$T/.bob_stuck_notified"
RESTARTS="$T/.bob_restarts"        # one epoch timestamp per watchdog restart
GAVE_UP="$T/.bob_gave_up"
PAUSE="$T/.bob_pause"
now=$(date +%s)
log() { echo "$(date '+%F %T') $*"; }

dm() {   # returns non-zero if the DM could not be sent
  (cd "$T" && "$PY" -c 'import sys, remind; remind.send_dm(*remind.discord_creds(remind.load_config()), sys.argv[1])' "$1") \
    || { log "DM failed"; return 1; }
}

start() {
  # When Claude exits, drop to a shell so the tmux session stays open to inspect.
  tmux new-session -d -s "$SESSION" -c "$ROOT" \
    "claude --channels plugin:discord@claude-plugins-official; exec zsh -l" \
    && log "started Bob in tmux session '$SESSION'"
}

# Pane (in any window of the session) whose direct child is Claude with the Discord channel.
claude_pane() {
  local id pid
  tmux list-panes -s -t "$SESSION" -F '#{pane_id} #{pane_pid}' 2>/dev/null | while read id pid; do
    pgrep -P "$pid" -f 'claude.*--channels' >/dev/null && { echo "$id"; return; }
  done
}

if ! tmux has-session -t "$SESSION" 2>/dev/null; then
  start
  exit 0
fi

PANE=$(claude_pane)
if [[ -z "$PANE" ]]; then
  [[ -f "$PAUSE" ]] && exit 0
  # Someone typed in the bob session in the last 10 min? Leave it alone this round.
  last=$(tmux list-clients -t "$SESSION" -F '#{client_activity}' 2>/dev/null | sort -n | tail -1)
  [[ -n "$last" ]] && (( now - last < 600 )) && exit 0
  # Give a restart already in progress (restart_bob_if_changed.sh) time to finish, then re-check.
  sleep 20
  tmux has-session -t "$SESSION" 2>/dev/null && [[ -n "$(claude_pane)" ]] && exit 0
  [[ -f "$GAVE_UP" ]] && exit 0
  # Crash-loop guard: max 3 restarts in 30 min.
  recent=0
  [[ -f "$RESTARTS" ]] && recent=$(awk -v c=$((now - 1800)) '$1 > c' "$RESTARTS" | wc -l | tr -d ' ')
  if (( recent >= 3 )); then
    touch "$GAVE_UP"
    log "watchdog: Bob keeps crashing — stopped restarting"
    dm "🛑 Bob keeps crashing (3 restarts in 30 min) — I've stopped restarting him. Check Bob's window (tmux attach -t bob), then run ~/Personal_Agent/tools/start_bob.sh."
    exit 0
  fi
  echo "$now" >> "$RESTARTS"
  tmux kill-session -t "$SESSION" 2>/dev/null
  sleep 2
  start
  log "watchdog: Claude had exited, Bob restarted"
  (( recent == 0 )) && dm "🔄 Bob was down (Claude had exited) — restarted automatically. Please resend anything from the last few minutes."
  exit 0
fi

# Healthy Claude found: clear crash-loop state.
rm -f "$GAVE_UP"
[[ -f "$RESTARTS" ]] && awk -v c=$((now - 1800)) '$1 > c' "$RESTARTS" > "$RESTARTS.tmp" && mv "$RESTARTS.tmp" "$RESTARTS"

# Waiting on a menu / confirmation screen? Look only at the bottom of Claude's pane. Tell Miranda once.
if tmux capture-pane -p -t "$PANE" | grep -v '^[[:space:]]*$' | tail -4 | grep -qE "Enter to (confirm|select)|Esc to (cancel|go back|exit)"; then
  if [[ ! -f "$STUCK_FLAG" ]]; then
    dm "⚠️ Bob is waiting on a menu/confirmation screen and can't read Discord. Attach (tmux attach -t bob) and answer it (Enter, or Esc if it's a menu you opened)." \
      && touch "$STUCK_FLAG" && log "watchdog: Bob waiting on a menu — DM sent"
  fi
else
  rm -f "$STUCK_FLAG"
fi
exit 0
