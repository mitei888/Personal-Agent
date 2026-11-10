#!/usr/bin/env python3
"""Friday-night Adele check (read-only).

Reads the iCloud calendar feed (URL in .env, never printed), looks at the coming
Mon–Sun week, and if it has fewer than the usual 2 Adele sessions, DMs Miranda on
Discord asking whether to add the missing ones (with the next session numbers).
It never writes to any calendar — adding is done by Bob after Miranda says yes.

  adele_check.py            run the check for next week and DM if needed
  adele_check.py --dry-run  print the message instead of sending
  adele_check.py --week 2026-11-09   check the week starting that Monday
"""
import re, sys, urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import remind  # reuse config() / send_dm()

TRIPS = ROOT / "Travel, Entertain, Food" / "trips.yaml"
HK = ZoneInfo("Asia/Hong_Kong")
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def to_tz(name):
    """IANA name, or Apple-style 'GMT-0400' / 'GMT+08:00'; fall back to Hong Kong."""
    name = name.strip('"')
    try:
        return ZoneInfo(name)
    except Exception:
        m = re.fullmatch(r"(?:GMT|UTC)([+-])(\d{1,2}):?(\d{2})?", name)
        if m:
            off = timedelta(hours=int(m.group(2)), minutes=int(m.group(3) or 0))
            return timezone(off if m.group(1) == "+" else -off)
        return HK


def feed_events(env_key):
    env = dict(re.findall(r"^(\w+)=(.*)$", (ROOT / ".env").read_text(), re.M))
    url = env[env_key].strip().strip("\"'").replace("webcal://", "https://", 1)
    data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "PersonalAgent/1.0"}),
                                  timeout=30).read().decode("utf-8", "replace")
    data = re.sub(r"\r?\n[ \t]", "", data)  # unfold lines
    out = []
    for ev in data.split("BEGIN:VEVENT")[1:]:
        s = re.search(r"^SUMMARY[^:]*:(.*)$", ev, re.M)
        st = re.search(r"^DTSTART([^:]*):(\S+)", ev, re.M)
        if not (s and st):
            continue
        raw = st.group(2)
        if len(raw) == 8:  # all-day
            dt = datetime.strptime(raw, "%Y%m%d").replace(tzinfo=HK)
        else:
            dt = datetime.strptime(raw.rstrip("Z"), "%Y%m%dT%H%M%S")
            tz = re.search(r"TZID=([^;:]+)", st.group(1))
            dt = dt.replace(tzinfo=timezone.utc if raw.endswith("Z") else to_tz(tz.group(1)) if tz else HK).astimezone(HK)
        out.append((dt, s.group(1).strip()))
    return out


def main():
    args = sys.argv[1:]
    cfg = yaml.safe_load((ROOT / "Schedule" / "routines.yaml").read_text())
    a = cfg["adele"]
    today = datetime.now(HK).date()
    if "--week" in args:
        monday = date.fromisoformat(args[args.index("--week") + 1])
    else:
        monday = today + timedelta(days=(7 - today.weekday()) % 7 or 7)  # next Monday
    sunday = monday + timedelta(days=6)

    away = [(date.fromisoformat(str(aw["from"])), date.fromisoformat(str(aw["to"]))) for aw in cfg.get("away") or []]
    trips = yaml.safe_load(TRIPS.read_text()) if TRIPS.exists() else []
    away += [(date.fromisoformat(str(t["start"])), date.fromisoformat(str(t["end"])))
             for t in trips or [] if t.get("status") != "idea"]
    is_away = lambda d: any(f <= d <= t for f, t in away)

    seen, evs = set(), []
    for src in a["sources"]:
        for dt, t in feed_events(src):
            if "adele" in t.lower() and (dt, t.lower()) not in seen:  # de-dupe copies in both calendars
                seen.add((dt, t.lower())); evs.append((dt, t))
    numbered = [(dt, int(m.group(1))) for dt, t in evs if (m := re.search(r"(\d+)\s*[/:]\s*" + str(a["total"]), t))]
    week = sorted(dt for dt, _ in evs if monday <= dt.date() <= sunday)
    if len(week) >= len(a["slots"]):
        print(f"week of {monday}: {len(week)} sessions, nothing to ask"); return

    # next number = after the latest numbered session on or before the end of that week
    last_n = max(numbered, key=lambda x: x[0])[1] if numbered else 0
    before = [n for dt, n in sorted(numbered) if dt.date() <= sunday]
    last_n = before[-1] if before else last_n
    booked_days = {dt.weekday() for dt in week}
    missing = [s for s in a["slots"] if DAYS.index(s["weekday"]) not in booked_days
               and not is_away(monday + timedelta(days=DAYS.index(s["weekday"])))]
    if not missing:
        print(f"week of {monday}: remaining slots fall on away days, nothing to ask"); return
    lines, n = [], last_n
    for s in missing:
        d = monday + timedelta(days=DAYS.index(s["weekday"]))
        n = n % a["total"] + 1
        lines.append(f"• {s['weekday']} {d:%d %b} {s['time']} — " + a["title"].format(n=n, total=a["total"]))
    have = ", ".join(f"{dt:%a %d %b %H:%M}" for dt in week) or "none"
    msg = (f"🗓 Adele check for the week of {monday:%a %d %b}: only {len(week)} session(s) in your calendar ({have}).\n"
           f"Add these?\n" + "\n".join(lines) +
           "\nReply to me with yes / which ones / skip (e.g. if you're away).")
    if "--dry-run" in args:
        print(msg); return
    remind.send_dm(*remind.discord_creds(remind.load_config()), msg)
    remind.log(f"adele_check sent for week {monday}")


if __name__ == "__main__":
    main()
