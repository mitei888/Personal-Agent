#!/bin/zsh -l
# Start Bob (the supervisor Claude session with the Discord channel) inside a
# detached tmux session called "bob". Safe to run any time: if the session
# already exists it does nothing. Run at login by launchd (install_bob.sh).
# Attach with:  tmux attach -t bob
SESSION=${BOB_SESSION:-bob}
ROOT=${0:A:h:h}
export PATH="$HOME/.bun/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "$(date '+%F %T') tmux session '$SESSION' already running, nothing to do"
  exit 0
fi

# When Claude exits, drop to a shell so the tmux session stays open to inspect.
tmux new-session -d -s "$SESSION" -c "$ROOT" \
  "claude --channels plugin:discord@claude-plugins-official; exec zsh -l"
echo "$(date '+%F %T') started Bob in tmux session '$SESSION'"
