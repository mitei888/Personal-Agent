"""
Flight search using SerpApi Google Flights API.

Features:
      - Exact date search with ±7 day flexibility window
      - Two-call round-trip model (outbound → departure_token → return leg)
      - Cathay Pacific preference scoring
      - Flexible month search (samples every 7 days, ranks by price)
      - ±7 day price calendar view
      - Price history and typical price range from Google price_insights
      - Nonstop filter, cabin class filter, 2hr minimum layover enforcement
      - HKD display alongside USD

travel_class codes:
      1 = Economy   2 = Premium Economy   3 = Business

stops codes:
      1 = Nonstop only   2 = 1 stop or fewer   0 = Any
"""
import os
import asyncio
import httpx
from datetime import datetime, timedelta
from Travel_Agent.Travel_Info import carrier_preference, select_three_options, primary_carrier, CLASS_MAP
from dotenv import load_dotenv


load_dotenv()

SERPAPI_KEY = os.getenv("serp_api")
SERPAPI_BASE = "https://serpapi.com/search"

HKD_RATE = 7.78
MIN_LAYOVER_MINUTES = 120

# Unpack carrier data once at startup
_CARRIERS, _BLOCKED, _ROUTE_PREF = carrier_preference()
_CARRIER_FALLBACK = sorted(_CARRIERS, key=lambda c: _CARRIERS[c])


def result_is_blocked(r):
    """Block any result where a segment is operated by a blocked carrier."""
    all_segs = r.get("outbound_flights", []) + r.get("return_flights", [])
    for seg in all_segs:
        if seg.get("airline", "") in _BLOCKED:
            return True
        if seg.get("operated_by", "") in _BLOCKED:
            return True
    return False


# ─── DISPLAY HELPERS ─────────────────────────────────────────────────────────
def usd_to_hkd(usd):
    return f"HKD {usd * HKD_RATE:,.0f}"


def mins_to_hm(minutes):
    h, m = divmod(int(minutes), 60)
    return f"{h}h {m:02d}m" if m else f"{h}h"


def check_layovers(flights):
    """Return warning strings for any layover under MIN_LAYOVER_MINUTES."""
    warnings = []
    for seg in flights:
        for lay in seg.get("layovers", []):
            dur = lay.get("duration", 999)
            if dur < MIN_LAYOVER_MINUTES:
                name = lay.get("name", lay.get("id", "?"))
                warnings.append(
                    f"⚠️  Short layover {mins_to_hm(dur)} at {name} "
                    f"(min preferred: {mins_to_hm(MIN_LAYOVER_MINUTES)})"
                )
    return warnings

# ─── FORMATTING ───────────────────────────────────────────────────────────────

def fmt_segments(flights: list[dict], label: str):
    """Format one direction (outbound or return) into display lines."""
    if not flights:
        return []

    stops = len(flights) - 1
    stop_label = "Direct ✈" if stops == 0 else f"{stops} stop{'s' if stops > 1 else ''}"
    total_fly = sum(f.get("duration", 0) for f in flights)
    total_lay = sum(
        lay.get("duration", 0)
        for f in flights for lay in f.get("layovers", [])
    )
    total = total_fly + total_lay

    #lines is a list, includes all flight details for the leg, including airline, flight #, departure/arrival, flight duration, layover time, etc.
    lines = [f"  {label}  {stop_label}  |  Total: {mins_to_hm(total)}"]

    for seg in flights:
        dep = seg.get("departure_airport", {})
        arr = seg.get("arrival_airport", {})
        dep_t = dep.get("time", "")
        arr_t = arr.get("time", "")
        dep_date = dep_t[:10]
        arr_date = arr_t[:10]
        dep_time = dep_t[11:16] if len(dep_t) > 10 else dep_t[-5:]
        arr_time = arr_t[11:16] if len(arr_t) > 10 else arr_t[-5:]
        overnight = " 🌙" if seg.get("is_overnight") else ""
        date_chg = " (+1d)" if dep_date and arr_date and dep_date != arr_date else ""
        airline = seg.get("airline", "?")
        flt_no = seg.get("flight_number", "")
        airplane = seg.get("airplane", "")
        legroom = seg.get("legroom", "")
        dur = mins_to_hm(seg.get("duration", 0))

        lines.append(
            f"    {airline} {flt_no}  "
            f"{dep.get('id', '?')} {dep_time} → "
            f"{arr.get('id', '?')} {arr_time}{date_chg}{overnight}"
            f"  ({dur})"
        )
        detail_parts = []
        if airplane:
            detail_parts.append(airplane)
        if legroom:
            detail_parts.append(f"Legroom {legroom}")
        if detail_parts:
            lines.append(f"       {' · '.join(detail_parts)}")

        for lay in seg.get("layovers", []):
            lay_dur = mins_to_hm(lay.get("duration", 0))
            lay_name = lay.get("name", lay.get("id", "?"))
            ov_lay = " (overnight)" if lay.get("overnight") else ""
            lines.append(f"      ⏸  Layover {lay_dur} at {lay_name}{ov_lay}")

    return lines

def fmt_result(result: dict, idx: int, requested_date: str) -> str:
    """Takes the above and format into one complete flight result."""
    price = result.get("price", 0)
    travel_class = result.get("travel_class", "")
    search_date = result.get("_search_date", requested_date)
    outbound = result.get("outbound_flights", [])
    returning = result.get("return_flights", [])

    all_airlines = [f.get("airline", "") for f in outbound + returning]
    cx_badge = "  ⭐ Cathay Pacific" if "CX" in all_airlines else ""
    date_badge = f"  📅 Alt date: {search_date}" if search_date != requested_date else ""

    # Layover warnings across both legs
    lay_warns = check_layovers(outbound) + check_layovers(returning) #call check_layover functions

    #creates list of 2 way flight options.
    lines = [
            f"\n{'═' * 54}",  #formatting
            f"  Option {idx + 1}{cx_badge}{date_badge}",
            f"  💰 USD {price:,}  ({usd_to_hkd(price)})  |  {travel_class}", #calls usd_to_hkd function
        ]

    for w in lay_warns:
        lines.append(f"    {w}")

    # Price insights
    ins = result.get("price_insights", {})
    if ins:
        level = ins.get("price_level", "")
        rng = ins.get("typical_price_range", [])
        lowest = ins.get("lowest_price")
        emoji = {"low": "🟢", "typical": "🟡", "high": "🔴"}.get(level, "⚪")
        if len(rng) == 2:
            lines.append(
                f"  {emoji} Price is {level}  |  "
                f"Typical: USD {rng[0]:,}–{rng[1]:,}"
                )
        if lowest and lowest < price:
            lines.append(f"  💡 Lowest seen on route: USD {lowest:,}")

    # Extras (baggage, wifi etc — top 3 only)
    exts = result.get("extensions", [])
    if exts:
        lines.append(f"  📋 {' · '.join(exts[:3])}")

    lines += fmt_segments(outbound, "✈ OUTBOUND") #calls fmt_segments() function
    if returning:
        lines += fmt_segments(returning, "↩ RETURN")

    return "\n".join(lines)

# ─── API CALL ─────────────────────────────────────────────────────────────────

async def _get(client: httpx.AsyncClient, params: dict) -> dict:
    """Single SerpApi GET call. Returns parsed JSON or {'error': ...}."""
    # async def allows the function to pause and wait for API response without blocking/freezing everything else)
    # _get, the underscore means its internal and not called directly by the agent. Its a wrapper that makes one HTTP call to SerpAPI, vs being called and used repeatedly

    try:
        r = await client.get(
            SERPAPI_BASE,
            params={"api_key": SERPAPI_KEY, **params},
            timeout=20,
            )
        return r.json() if r.status_code == 200 else {"error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def _extract(data: dict, search_date: str = "") -> list[dict]:
    """Pull flight results out of a SerpApi response and normalise them."""
    #_extract, also internal. SerpApi returns a messy nested JSON blob, this function pulls out just the bits we care about
    results = []
    for key in ("best_flights", "other_flights"):
        for item in data.get(key, []):
            results.append({
                    "outbound_flights": item.get("flights", []),
                    "return_flights": [],
                    "price": item.get("price", 0),
                    "travel_class": item.get("type", ""),
                    "extensions": item.get("extensions", []),
                    "price_insights": data.get("price_insights", {}),
                    "departure_token": item.get("departure_token", ""),
                    "booking_token": item.get("booking_token", ""),
                    "_search_date": search_date,
                })
    return results

# ─── PUBLIC FUNCTIONS ─────────────────────────────────────────────────────────

async def search_flights(origin, destination, departure_date, return_date="", adults=1, travel_class="ECONOMY",
                             nonstop_only=True, region=""):
        """
        Search flights via SerpApi Google Flights.

        Checks exact date PLUS ±7 days to surface cheaper alternatives.
        Prefers Cathay Pacific. Enforces 2-hour minimum layover.
        For round trips, makes a second API call per outbound option to
        retrieve paired return flights (SerpApi's two-call model).

        Args:
            region: destination region key from Travel_Info.py route_preference
            (e.g. "japan", "uk", "australia"). The agent supplies this
            from its own world knowledge — no keyword matching needed.
            If omitted, falls back to global carrier preference order.
        """

        base = datetime.strptime(departure_date, "%Y-%m-%d")
        dates = [(base + timedelta(days=d)).strftime("%Y-%m-%d") for d in range(-7, 8)]
        cls_code = CLASS_MAP.get(travel_class.upper(), 1)
        stop_code = 1 if nonstop_only else 2
        trip_type = 1 if return_date else 2  # 1=round-trip, 2=one-way

        base_params = {
            "engine": "google_flights",
            "departure_id": origin.upper(),
            "arrival_id": destination.upper(),
            "travel_class": cls_code,
            "stops": stop_code,
            "type": trip_type,
            "adults": adults,
            "currency": "USD",
            "hl": "en",
            "gl": "us",
            }
        if return_date:
            base_params["return_date"] = return_date

        all_results = []

        async with httpx.AsyncClient() as client:
            for dep_date in dates:
                data = await _get(client, {**base_params, "outbound_date": dep_date})
                if "error" in data:
                    await asyncio.sleep(0.3)
                    continue

                outbound_options = _extract(data, dep_date)

                for opt in outbound_options:
                    dep_token = opt.get("departure_token")

                    # Round-trip: fetch paired return leg
                    if dep_token and return_date:
                        ret_data = await _get(
                            client,
                            {**base_params, "outbound_date": dep_date, "departure_token": dep_token}
                            )
                        if "error" not in ret_data:
                            ret_options = _extract(ret_data, dep_date)
                            if ret_options:
                                opt["return_flights"] = ret_options[0].get("outbound_flights", [])
                                # SerpApi returns combined price in the return call
                                if ret_options[0].get("price"):
                                    opt["price"] = ret_options[0]["price"]
                        await asyncio.sleep(0.3)

                    all_results.append(opt)

                await asyncio.sleep(0.3)

        if not all_results:
            return (
                f"❌ No flights found: {origin.upper()} → {destination.upper()} "
                f"around {departure_date}.\n"
                f"  Try: broader dates, allow 1 stop, or check IATA codes."
                )

        # Filter out results with short layovers using existing check_layovers()
        clean = [r for r in all_results if not check_layovers(r.get("outbound_flights", []) + r.get("return_flights", []))]  #returns True, ie layovers are long enough
        short_layover = [r for r in all_results if check_layovers(r.get("outbound_flights", []) + r.get("return_flights", []))] #gets a list, layovers are too short
        pool = clean if clean else all_results  #best avail results to work with, flights with no/sufficient layovers, everything else if it doesnt exist

        # Select exactly 3 options: CX first (HKG routes), then 2 approved alternatives
        region_pref = _ROUTE_PREF.get(region, _CARRIER_FALLBACK)
        selected, carrier_notes = select_three_options(pool, origin, destination, region_pref)

        # Header
        route = f"{origin.upper()} → {destination.upper()}"
        if return_date:
            route += f" → {origin.upper()}"

        out = [
            f"✈  FLIGHTS: {route}",
            f"Requested: {departure_date}"
            + (f"  →  return {return_date}" if return_date else ""),
            f"Showing 3 options across ±7 days  |  Class: {travel_class}  |  "
            + ("Nonstop only" if nonstop_only else "Up to 1 stop"),
            f"Passengers: {adults}  |  Prices in USD (HKD approx at {HKD_RATE})",
            "─" * 54,
            ]

        for note in carrier_notes:
            out.append(f"  {note}")

        # Cheapest-date callout (across all results, not just selected)
        if pool:
            cheapest_all = min(pool, key=lambda r: r.get("price", 9999))
            if cheapest_all.get("_search_date") != departure_date:
                cp = cheapest_all["price"]
                out.append(
                    f"\n💡 Cheapest found on {cheapest_all['_search_date']}: "
                    f"USD {cp:,} ({usd_to_hkd(cp)}) vs your requested date"
                    )

        out.append(f"\n3 Recommended Options:\n")
        for i, r in enumerate(selected):
            out.append(fmt_result(r, i, departure_date))

        if short_layover and not clean:
            out.append(
                f"\n\n⚠️  All results have layovers under {mins_to_hm(MIN_LAYOVER_MINUTES)}. "
                "Shown anyway — verify connection times before booking."
                )
        elif short_layover:
            out.append(
                f"\n\n⚠️  {len(short_layover)} result(s) hidden — layover under "
                f"{mins_to_hm(MIN_LAYOVER_MINUTES)}. "
                "Pass nonstop_only=False to review."
                )

        out.append(
            "\n\n⚠️  Nothing booked. Reply with option 1, 2, or 3 to proceed."
            )
        return "\n".join(out)


async def find_best_dates(origin, destination, duration_nights, departure_date="", month="", adults=1, travel_class="ECONOMY"):
    """
    Find the cheapest dates to fly. Two modes:

    1. Approximate dates — pass departure_date (e.g. "2025-05-16").
       Checks ±7 days and shows prices ranked cheapest first.

    2. Flexible on the whole month — pass month (e.g. "2025-05").
       Scans the full month and ranks all windows by price.
    """
    cls_code = CLASS_MAP.get(travel_class.upper(), 1)
    stop_code = 1 if travel_class == "BUSINESS" else 2
    lvl_emoji = {"low": "🟢", "typical": "🟡", "high": "🔴"}

    if departure_date:
        base = datetime.strptime(departure_date, "%Y-%m-%d")
        sample_dates = [(base + timedelta(days=d)).strftime("%Y-%m-%d") for d in range(-7, 8)]
        header = f"±7 days around {departure_date}"
    elif month:
        year, mon = map(int, month.split("-"))
        cur = datetime(year, mon, 1)
        month_end = (
                        datetime(year + 1, 1, 1) if mon == 12
                        else datetime(year, mon + 1, 1)
                    ) - timedelta(days=1)
        sample_dates = []
        while cur <= month_end:
            sample_dates.append(cur.strftime("%Y-%m-%d"))
            cur += timedelta(days=3)
        header = f"All of {datetime(year, mon, 1).strftime('%B %Y')}"
    else:
        return "❌ Provide either departure_date (approximate) or month (flexible)."

    out = [
        f"📅 PRICE SEARCH: {origin.upper()} → {destination.upper()}",
        f"{header}  |  Stay: {duration_nights} nights  |  Class: {travel_class}\n",
    ]

    price_rows = []

    async with httpx.AsyncClient() as client:
        for dep in sample_dates:
            ret = (datetime.strptime(dep, "%Y-%m-%d") + timedelta(days=duration_nights)).strftime("%Y-%m-%d")

            data = await _get(client, {
                "engine": "google_flights",
                "departure_id": origin.upper(),
                "arrival_id": destination.upper(),
                "outbound_date": dep,
                "return_date": ret,
                "travel_class": cls_code,
                "stops": stop_code,
                "type": 1,
                "adults": adults,
                "currency": "USD",
                "hl": "en",
                "gl": "us",
            })

            if "error" not in data:
                options = data.get("best_flights", []) + data.get("other_flights", [])
                if options:
                    ins = data.get("price_insights", {})
                    price_rows.append({
                        "dep": dep,
                        "ret": ret,
                        "price": min(f.get("price", 9999) for f in options),
                        "level": ins.get("price_level", ""),
                        "carrier": primary_carrier(options[0].get("flights", [])),
                        "is_requested": dep == departure_date,
                    })

            await asyncio.sleep(0.3)

    if not price_rows:
        return f"❌ No results found for {origin} → {destination}. Check IATA codes."

    price_rows.sort(key=lambda x: x["price"])

    #these denote size of column and left/right aligned
    out += [
        f"{'─' * 60}",
        f"{'DEPART':<12} {'RETURN':<12} {'USD':>8}  {'HKD':>10}  {'LEVEL':<8} CARRIER",
        f"{'─' * 60}",
    ]

    for row in price_rows[:12]:
        emoji = lvl_emoji.get(row["level"], "⚪")
        marker = "  ◀ your date" if row["is_requested"] else ""
        out.append(
            f"{row['dep']:<12} {row['ret']:<12} "
            f"USD {row['price']:>6,}  "
            f"HKD {row['price'] * HKD_RATE:>8,.0f}  "
            f"{emoji} {row['level']:<7} {row['carrier']}{marker}"
        )

    best = price_rows[0]
    out += [
        f"\n{'─' * 60}",
        f"💡 Best: depart {best['dep']}, return {best['ret']} — "
        f"USD {best['price']:,} ({usd_to_hkd(best['price'])})",
    ]

    return "\n".join(out)
