#!/bin/zsh -l
# Run by launchd (com.personalagent.bobwatch) when Bob's instructions or rules change,
# i.e. after a git pull touches CLAUDE.md, .claude/agents/ or .claude/settings.json.
# Restarts Bob's tmux session only if the content really changed, then DMs Miranda.
ROOT=${0:A:h:h}
export PATH="$HOME/.bun/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
STATE="$ROOT/.bob_config_hash"
SESSION=${BOB_SESSION:-bob}
PY=${PYTHON:-$(command -v python3)}

sleep 20   # let git pull finish writing all files

HASH=$(cat "$ROOT/CLAUDE.md" "$ROOT/.claude/settings.json" "$ROOT"/.claude/agents/*.md 2>/dev/null | shasum | cut -d' ' -f1)
if [[ ! -f "$STATE" ]]; then           # first run after install: just remember, don't restart
  echo "$HASH" > "$STATE"; echo "$(date '+%F %T') baseline recorded"; exit 0
fi
[[ "$(cat "$STATE")" == "$HASH" ]] && exit 0   # touched but not changed

echo "$HASH" > "$STATE"
tmux kill-session -t "$SESSION" 2>/dev/null
sleep 3
"$ROOT/tools/start_bob.sh"
echo "$(date '+%F %T') Bob restarted to load new instructions"
cd "$ROOT/tools" && "$PY" -c 'import remind; remind.send_dm(*remind.discord_creds(remind.load_config()), "🔄 Bob restarted to load updated instructions (from git pull). Anything you sent in the last minute may need resending.")' \
  || echo "$(date '+%F %T') restart DM failed"
