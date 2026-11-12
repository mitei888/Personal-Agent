#!/usr/bin/env python3
"""Personal Agent reminders + nightly briefing, delivered to Miranda's Discord DM.

Run every 15 min by launchd (tools/com.personalagent.remind.plist).
  remind.py              send due reminders; send the 9 pm briefing once per night
  remind.py --dry-run    print what would be sent, send nothing
  remind.py --briefing   send tomorrow's briefing now (preview)
  Also: at 9 am local the day before a trip in trips.yaml starts, sends the weather forecast
  for the trip's places (Open-Meteo, no key needed).
  remind.py --test       send a one-off test DM

Config is read from (later files don't override earlier ones):
  environment, <root>/.agent.env, <root>/.env, ~/.claude/channels/discord/.env
  DISCORD_BOT_TOKEN (or discord_token), DISCORD_USER_ID
  Calendars: any key ending in _cal / _CAL or of the form GCAL_<NAME>_ICS holding a
  Google "secret address in iCal format" URL. The label is taken from the key name.
"""
import calendar, json, os, re, sys, urllib.request, urllib.error
from datetime import datetime, date, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import yaml

ROOT = Path(__file__).resolve().parent.parent
REMINDERS = ROOT / "reminders.yaml"
TRIPS = ROOT / "Travel, Entertain, Food" / "trips.yaml"
STATE = ROOT / ".reminders_state.json"
LOG = ROOT / "tools" / "remind.log"
HOME_TZ = "Asia/Hong_Kong"
BRIEFING_HOUR = 21          # 9 pm local
WEATHER_HOUR = 9            # 9 am local, the day before a trip starts
# Events only worth showing while Miranda is in North America (per trips.yaml tz).
NORTH_AMERICA_ONLY = [r"\bavos\s+ama\b"]
NORTH_AMERICA_TZ = ("America/", "US/", "Canada/")
API = "https://discord.com/api/v10"
# Miranda's own addresses: events where one of these has declined are left out of the briefing.
MY_EMAILS = {"miranda@ferrettocap.com", "mitei9@gmail.com"}


# ---------- config ----------
def read_env(path):
    out = {}
    try:
        for line in Path(path).expanduser().read_text().splitlines():
            m = re.match(r"\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*['\"]?(\S+?)['\"]?\s*$", line)
            if m:
                out[m.group(1)] = m.group(2)
    except FileNotFoundError:
        pass
    return out


def load_config():
    cfg = {}
    for src in (ROOT / ".agent.env", ROOT / ".env", Path("~/.claude/channels/discord/.env")):
        for k, v in read_env(src).items():
            cfg.setdefault(k, v)
    for k, v in os.environ.items():
        if k.startswith(("DISCORD_", "GCAL_")):
            cfg[k] = v
    return cfg


def discord_creds(cfg):
    token = cfg.get("DISCORD_BOT_TOKEN") or cfg.get("discord_token")
    user = cfg.get("DISCORD_USER_ID")
    if not token or not user:
        sys.exit("Missing Discord bot token or DISCORD_USER_ID")
    return token, user


def calendars(cfg):
    cals = []
    for k, v in cfg.items():
        m = re.fullmatch(r"GCAL_(\w+)_ICS", k) or re.fullmatch(r"(\w+?)_cal", k, re.I)
        if m and v.startswith("webcal://"):        # iCloud public calendar links
            v = "https://" + v[len("webcal://"):]
        if m and v.startswith("https://"):
            cals.append((m.group(1).replace("_", " ").title(), v))
    return sorted(cals)


# ---------- discord ----------
def discord(token, method, path, body):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bot {token}", "Content-Type": "application/json",
                                          "User-Agent": "PersonalAgentReminder (local, 1.0)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read() or b"{}")


def send_dm(token, user, text):
    ch = discord(token, "POST", "/users/@me/channels", {"recipient_id": user})
    while text:  # Discord limit 2000 chars; split on line breaks
        chunk = text[:1990]
        if len(text) > 1990 and "\n" in chunk:
            chunk = chunk[:chunk.rfind("\n")]
        discord(token, "POST", f"/channels/{ch['id']}/messages", {"content": chunk})
        text = text[len(chunk):].lstrip("\n")


# ---------- reminders ----------
def reminder_time(r):
    tz = ZoneInfo(r.get("tz", HOME_TZ))
    return datetime.strptime(str(r["at"]), "%Y-%m-%d %H:%M").replace(tzinfo=tz)


def next_after(r, t):
    rep = r.get("repeat")
    if rep == "daily":
        return t + timedelta(days=1)
    if rep == "weekly":
        return t + timedelta(weeks=1)
    if rep == "monthly":
        y, m = (t.year + (t.month == 12), t.month % 12 + 1)
        day = min(int(str(r["at"])[8:10]), calendar.monthrange(y, m)[1])
        return t.replace(year=y, month=m, day=day)
    return None


def occurrence_due(r, now):
    """Latest scheduled occurrence <= now, or None."""
    t = reminder_time(r)
    if t > now:
        return None
    while True:
        nxt = next_after(r, t)
        if nxt is None or nxt > now:
            return t
        t = nxt


def occurrences_between(r, start, end):
    t = reminder_time(r)
    out = []
    while t < end:
        if t >= start:
            out.append(t)
        t = next_after(r, t)
        if t is None:
            break
    return out


# ---------- briefing ----------
def local_tz(d):
    """Time zone to use on date d: the trip's tz if travelling, else home."""
    try:
        for trip in yaml.safe_load(TRIPS.read_text()) or []:
            if trip.get("tz") and str(trip["start"]) <= d.isoformat() <= str(trip["end"]):
                return ZoneInfo(trip["tz"])
    except FileNotFoundError:
        pass
    return ZoneInfo(HOME_TZ)


def trips_on(d):
    try:
        return [t for t in (yaml.safe_load(TRIPS.read_text()) or [])
                if str(t["start"]) <= d.isoformat() <= str(t["end"])]
    except FileNotFoundError:
        return []


def declined_by_me(ev):
    att = ev.get("ATTENDEE")
    for a in (att if isinstance(att, list) else [att] if att else []):
        email = str(a).lower().removeprefix("mailto:")
        if email in MY_EMAILS and str(a.params.get("PARTSTAT", "")).upper() == "DECLINED":
            return True
    return False


def fetch_events(cals, day, tz):
    import icalendar, recurring_ical_events
    start = datetime.combine(day, time(0), tz)
    end = start + timedelta(days=1)
    out, errors = [], []
    for label, url in cals:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PersonalAgent/1.0"})
            cal = icalendar.Calendar.from_ical(urllib.request.urlopen(req, timeout=30).read())
            for ev in recurring_ical_events.of(cal).between(start, end):
                if str(ev.get("STATUS", "")).upper() == "CANCELLED" or declined_by_me(ev):
                    continue
                s = ev.decoded("DTSTART")
                e = ev.decoded("DTEND") if ev.get("DTEND") else None
                allday = not isinstance(s, datetime)
                if not allday:
                    s = s.astimezone(tz) if s.tzinfo else s.replace(tzinfo=tz)
                    e = (e.astimezone(tz) if e.tzinfo else e.replace(tzinfo=tz)) if isinstance(e, datetime) else None
                title = str(ev.get("SUMMARY", "(no title)")).strip()
                loc = str(ev.get("LOCATION", "")).strip().split("\n")[0]
                out.append(dict(cal=label, allday=allday, start=s, end=e, title=title, loc=loc))
        except Exception as ex:
            errors.append(f"{label} calendar unavailable ({type(ex).__name__})")
    return out, errors


_STOP = {"the", "a", "an", "and", "with", "for", "of", "re", "to", "at", "on", "in",
         "meeting", "call", "catch", "up", "catchup", "microsoft", "teams", "zoom"}


def _words(title):
    return {w for w in re.findall(r"[a-z0-9]+", title.lower()) if w not in _STOP and len(w) > 1}


def _same_event(a, b):
    """Same event copied onto two calendars: same start time and similar title."""
    if a["allday"] != b["allday"] or a["start"] != b["start"]:
        return False
    wa, wb = _words(a["title"]), _words(b["title"])
    if not wa or not wb:
        return a["title"].strip().lower() == b["title"].strip().lower()
    return wa <= wb or wb <= wa or len(wa & wb) / len(wa | wb) >= 0.5


def dedupe(events, prefer=("Work",)):
    """Keep one copy of events that appear on several calendars (preferred calendar wins)."""
    rank = lambda e: (prefer.index(e["cal"]) if e["cal"] in prefer else len(prefer), -len(e["loc"]))
    kept = []
    for ev in sorted(events, key=rank):
        if not any(_same_event(ev, k) for k in kept):
            kept.append(ev)
    return kept


def itinerary_for(trip, day):
    """Lines of the trip's itinerary.md section for `day` (heading like '## Wed 30 Dec — …').
    Times in the itinerary are local to the destination, same as the briefing."""
    folder = trip.get("folder")
    if not folder:
        return []
    path = TRIPS.parent / folder / "itinerary.md"
    try:
        text = path.read_text()
    except FileNotFoundError:
        return []
    out, inside = [], False
    head = re.compile(rf"^##\s+{day:%a}\w*\s+0?{day.day}\s+{day:%b}\w*\b", re.I)
    for line in text.splitlines():
        if line.startswith("## "):
            if inside:
                break
            inside = bool(head.match(line))
            if inside:
                out.append(f"_{line[3:].split('—', 1)[-1].strip()}_")
            continue
        if inside and line.strip():
            out.append(line.rstrip())
    return out


def build_briefing(day, cfg):
    tz = local_tz(day)
    events, errors = fetch_events(calendars(cfg), day, tz)
    events = dedupe(events)
    if not tz.key.startswith(NORTH_AMERICA_TZ):
        events = [e for e in events if not any(re.search(p, e["title"], re.I) for p in NORTH_AMERICA_ONLY)]
    lines = [f"🌙 **Tomorrow — {day:%a %-d %b}**" + ("" if tz.key == HOME_TZ else f"  _(times in {tz.key.split('/')[-1]})_")]
    for t in trips_on(day):
        lines.append(f"✈️ {t['name']}")
        plan = itinerary_for(t, day)
        if plan:
            lines.append("\n**🗺 Itinerary**")
            lines.extend(plan)
    by_cal = {}
    for ev in events:
        by_cal.setdefault(ev["cal"], []).append(ev)
    for label in sorted(by_cal):
        lines.append(f"\n**{label}**")
        for ev in sorted(by_cal[label], key=lambda e: (not e["allday"], e["start"] if not e["allday"] else datetime.min.replace(tzinfo=tz))):
            if ev["allday"]:
                when = "All day"
            else:
                when = f"{ev['start']:%H:%M}" + (f"–{ev['end']:%H:%M}" if ev["end"] else "")
            loc = f" · {ev['loc'][:40]}" if ev["loc"] else ""
            lines.append(f"• {when}  {ev['title'][:80]}{loc}")
    # reminders due tomorrow
    start = datetime.combine(day, time(0), tz)
    end = start + timedelta(days=1)
    rems = []
    for r in yaml.safe_load(REMINDERS.read_text()) or []:
        for occ in occurrences_between(r, start, end):
            rems.append((occ.astimezone(tz), r["text"]))
    if rems:
        lines.append("\n**⏰ Reminders**")
        for t, text in sorted(rems):
            lines.append(f"• {t:%H:%M}  {text}")
    if not events and not rems:
        lines.append("\nNothing scheduled — enjoy a free day ✨")
    for e in errors:
        lines.append(f"\n⚠️ {e}")
    return "\n".join(lines)


# ---------- pre-trip weather ----------
WMO = {0: "☀️ Clear", 1: "🌤 Mostly clear", 2: "⛅ Partly cloudy", 3: "☁️ Cloudy", 45: "🌫 Fog", 48: "🌫 Fog",
       51: "🌦 Light drizzle", 53: "🌦 Drizzle", 55: "🌧 Heavy drizzle", 56: "🌧 Freezing drizzle", 57: "🌧 Freezing drizzle",
       61: "🌧 Light rain", 63: "🌧 Rain", 65: "🌧 Heavy rain", 66: "🌧 Freezing rain", 67: "🌧 Freezing rain",
       71: "🌨 Light snow", 73: "🌨 Snow", 75: "❄️ Heavy snow", 77: "🌨 Snow grains",
       80: "🌦 Showers", 81: "🌧 Heavy showers", 82: "⛈ Violent showers", 85: "🌨 Snow showers", 86: "❄️ Heavy snow showers",
       95: "⛈ Thunderstorms", 96: "⛈ Thunderstorms + hail", 99: "⛈ Thunderstorms + hail"}


def _get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "PersonalAgent/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def trip_places(trip):
    """[(place name, region, first day, last day)]. Uses the trip's optional `places:` list
    ({name, region, from, to}; region = prefecture/state to pick the right town); otherwise `city:`, otherwise the trip name, for the whole trip."""
    start, end = str(trip["start"]), str(trip["end"])
    places = trip.get("places") or [{"name": trip.get("city") or trip["name"]}]
    return [(p["name"], p.get("region"), str(p.get("from", start)), str(p.get("to", end))) for p in places]


def weather_message(trip):
    from urllib.parse import quote
    lines = [f"🌦 **Weather for {trip['name']}** ({trip['start']:%a %-d %b} – {trip['end']:%a %-d %b})"]
    for name, region, d0, d1 in trip_places(trip):
        try:
            hits = _get_json(f"https://geocoding-api.open-meteo.com/v1/search?count=10&name={quote(name)}")["results"]
            geo = next((h for h in hits if region and region.lower() in str(h.get("admin1", "")).lower()), hits[0])
            fc = _get_json("https://api.open-meteo.com/v1/forecast?daily=weather_code,temperature_2m_max,"
                           "temperature_2m_min,precipitation_probability_max&forecast_days=16&timezone=auto"
                           f"&latitude={geo['latitude']}&longitude={geo['longitude']}")["daily"]
        except Exception as ex:
            lines.append(f"\n**{name}**: forecast unavailable ({type(ex).__name__})")
            continue
        lines.append(f"\n**{geo['name']}**")
        shown = 0
        for i, d in enumerate(fc["time"]):
            if d0 <= d <= d1:
                rain = fc["precipitation_probability_max"][i]
                lines.append(f"• {date.fromisoformat(d):%a %-d}: {WMO.get(fc['weather_code'][i], '?')}, "
                             f"{fc['temperature_2m_min'][i]:.0f}–{fc['temperature_2m_max'][i]:.0f}°C"
                             + (f", rain {rain}%" if rain is not None else ""))
                shown += 1
        if fc["time"] and d1 > fc["time"][-1]:
            lines.append(f"• _No forecast yet after {date.fromisoformat(fc['time'][-1]):%a %-d %b}_" if shown
                         else "• _Too far ahead for a forecast_")
    return "\n".join(lines)


def trips_starting(d):
    try:
        return [t for t in (yaml.safe_load(TRIPS.read_text()) or [])
                if str(t.get("start")) == d.isoformat() and t.get("status") in ("booked", "planning")]
    except FileNotFoundError:
        return []


# ---------- main ----------
def log(msg):
    with open(LOG, "a") as f:
        f.write(f"{datetime.now().isoformat(timespec='seconds')} {msg}\n")


def main():
    args = set(sys.argv[1:])
    cfg = load_config()
    dry = "--dry-run" in args
    if "--test" in args:
        send_dm(*discord_creds(cfg), "✅ Personal Agent reminders are connected.")
        print("test sent"); return

    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    now_home = datetime.now(ZoneInfo(HOME_TZ))
    today = now_home.astimezone(local_tz(now_home.date())).date()
    tz_now = local_tz(today)
    now = datetime.now(tz_now)

    if "--briefing" in args:
        text = build_briefing(now.date() + timedelta(days=1), cfg)
        if dry: print(text)
        else: send_dm(*discord_creds(cfg), text); print("briefing sent")
        return

    # 1) due reminders
    due = []
    for r in yaml.safe_load(REMINDERS.read_text()) or []:
        occ = occurrence_due(r, now)
        if occ and state.get(r["id"]) != occ.isoformat():
            due.append((r, occ))
    # 2) nightly briefing (once per local date, from 21:00 until 23:59)
    brief_due = now.hour >= BRIEFING_HOUR and state.get("_briefing") != now.date().isoformat()
    # 3) weather for trips starting tomorrow (once per trip, from 9 am local)
    wx_due = [t for t in trips_starting(now.date() + timedelta(days=1))
              if now.hour >= WEATHER_HOUR and not state.get(f"_weather_{t['id']}")]

    if dry:
        for r, occ in due: print("REMINDER", r["id"], occ)
        if brief_due: print(build_briefing(now.date() + timedelta(days=1), cfg))
        for t in wx_due: print(weather_message(t))
        if not due and not brief_due and not wx_due: print("nothing due")
        return
    if not due and not brief_due and not wx_due:
        return
    token, user = discord_creds(cfg)
    for r, occ in due:
        late = now - occ > timedelta(minutes=30)
        text = ("⏰ " + r["text"]) if not late else f"⏰ (late — was due {occ:%a %-d %b %H:%M}) {r['text']}"
        try:
            send_dm(token, user, text)
            state[r["id"]] = occ.isoformat(); log(f"sent {r['id']}")
        except Exception as e:
            log(f"FAILED {r['id']}: {e}")
    if brief_due:
        try:
            send_dm(token, user, build_briefing(now.date() + timedelta(days=1), cfg))
            state["_briefing"] = now.date().isoformat(); log("sent briefing")
        except Exception as e:
            log(f"FAILED briefing: {e}")
    for t in wx_due:
        try:
            send_dm(token, user, weather_message(t))
            state[f"_weather_{t['id']}"] = now.date().isoformat(); log(f"sent weather {t['id']}")
        except Exception as e:
            log(f"FAILED weather {t['id']}: {e}")
    STATE.write_text(json.dumps(state, indent=2))


if __name__ == "__main__":
    main()
