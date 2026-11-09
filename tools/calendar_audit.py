#!/usr/bin/env python3
"""PreToolUse hook: log every attempted Google Calendar change to tools/calendar_audit.log.
Runs before the permission prompt, so it records attempts whether you approve them or not."""
import json, sys
from datetime import datetime
from pathlib import Path
d = json.load(sys.stdin)
tool = d.get("tool_name", "").rsplit("__", 1)[-1]
inp = d.get("tool_input", {})
keep = {k: inp[k] for k in ("calendarId", "eventId", "summary", "start", "end", "attendees", "response") if k in inp}
line = f"{datetime.now().isoformat(timespec='seconds')} ATTEMPT {tool} {json.dumps(keep, ensure_ascii=False, default=str)[:600]}\n"
with open(Path(__file__).with_name("calendar_audit.log"), "a") as f:
    f.write(line)
sys.exit(0)
