

def carrier_preference():
    # Used when no region-specific rule matches.
    # Lower score = more preferred. Carriers not listed get score 99 (allowed, last).
    carriers = {
            "CX": 0,    # Cathay Pacific

        # Premium Asian
            "JL": 10,   # Japan Airlines      — 5-star Skytrax
            "NH": 11,   # ANA                 — 5-star Skytrax
            "BR": 12,  # EVA Air
            "SQ": 13,   # Singapore Airlines  — 5-star Skytrax
            "OZ": 14,   # Asiana
            "KE": 15,   # Korean Air
            "TG": 17,   # Thai Airways
            "MH": 18,   # Malaysia Airlines
            "GA": 19,   # Garuda Indonesia
        # Premium Gulf
            "QR": 20,   # Qatar Airways       — 5-star Skytrax
            "EK": 21,   # Emirates            — 5-star Skytrax
            "EY": 22,   # Etihad
            # Premium European
            "BA": 23,   # British Airways
            "LH": 24,   # Lufthansa
            "AF": 25,   # Air France
            "KL": 26,   # KLM
            "LX": 27,   # Swiss
            "OS": 28,   # Austrian
            "SK": 29,   # SAS
            "AY": 30,   # Finnair
            "IB": 31,   # Iberia
            "TP": 32,   # TAP Portugal
        # Premium Oceanic
            "QF": 33,   # Qantas              — 5-star Skytrax
            "NZ": 34,   # Air New Zealand
            # North American full-service
            "AC": 40,   # Air Canada
            "AS": 41,   # Alaska Airlines
            "DL": 42,   # Delta
        # Chinese full-service
            "CA": 43,   # Air China
            "MU": 44,   # China Eastern
            "CZ": 45,   # China Southern

        }

    blocked = {
        # ── Asia-Pacific LCC ──────────────────────────────────────────────────────
        "AK",  # AirAsia Malaysia
        "FD",  # Thai AirAsia
        "QZ",  # AirAsia Indonesia
        "D7",  # AirAsia X (long-haul LCC)
        "XT",  # AirAsia X Indonesia
        "Z2",  # AirAsia Philippines
        "XJ",  # Thai AirAsia X
        "TR",  # Scoot
        "TZ",  # Scoot (old code)
        "3K",  # Jetstar Asia
        "GK",  # Jetstar Japan
        "JQ",  # Jetstar Australia
        "BL",  # Pacific Airlines (Jetstar Vietnam)
        "VJ",  # VietJet Air
        "VZ",  # Thai VietJet
        "HX",  # Hong Kong Airlines (chronic financial instability)
        "UO",  # HK Express (Cathay Group budget brand — CX itself preferred)
        "MM",  # Peach Aviation
        "BC",  # Skymark Japan
        "6J",  # Solaseed Air
        "SL",  # Thai Lion Air
        "JT",  # Lion Air Indonesia
        "IW",  # Wings Air
        "QG",  # Citilink
        "ID",  # Batik Air Indonesia
        "OD",  # Batik Air Malaysia (ex-Malindo)
        "PQ",  # PhilippineAirAsia
        "5J",  # Cebu Pacific (Philippines)
        "DG",  # Cebgo
        "Z2",  # AirAsia Zest
        "8K",  # Astana Air / FlyArystan
        "KC",  # Air Astana (acceptable but not preferred — leave unlisted not blocked)
        # ── Indian Subcontinent LCC ───────────────────────────────────────────────
        "6E",  # IndiGo
        "SG",  # SpiceJet
        "G8",  # Go First (defunct — guard against stale data)
        "I5",  # Air Asia India
        # ── European LCC ─────────────────────────────────────────────────────────
        "FR",  # Ryanair
        "U2",  # easyJet
        "W6",  # Wizz Air
        "VY",  # Vueling
        "HV",  # Transavia Netherlands
        "TO",  # Transavia France
        "PC",  # Pegasus Turkey
        "BV",  # Blue Air Romania
        "V7",  # Volotea
        "X3",  # TUI Fly Germany
        "BY",  # TUI UK
        "OR",  # TUI Netherlands
        "LS",  # Jet2
        "MT",  # Thomas Cook (defunct — stale data guard)
        "DE",  # Condor
        # ── North American LCC ────────────────────────────────────────────────────
        "WN",  # Southwest
        "F9",  # Frontier
        "NK",  # Spirit
        "SY",  # Sun Country
        "G4",  # Allegiant
        "WS",  # WestJet (budget positioning)
        "PD",  # Porter Airlines (regional only)
        "K1",  # Wow Air (defunct)
        # ── Middle East / Africa LCC ─────────────────────────────────────────────
        "FZ",  # flydubai
        "G9",  # Air Arabia
        "XY",  # flynas
        "J9",  # Jazeera Airways
        "OQ",  # Citilink (duplicate guard)
    }

    route_preference = {

        "canada": [
            "AC",  # Air Canada — flag carrier, direct YVR/YYZ/YUL from HKG
            "CX",  # (already slot 1, kept here so logic can skip it cleanly)
            "JL",  # JAL via Tokyo is a reasonable connection to Canada
            "NH",  # ANA via Tokyo
        ],

        "usa": [
            "JL",  # JAL — excellent Pacific product, good US gateway coverage
            "NH",  # ANA — same, Star Alliance US connections
            "QR",  # Qatar via Doha (East Coast US)
            "EK",  # Emirates via Dubai (East Coast US)
            "AC",  # Air Canada — connects well at YVR/YYZ to US cities
            # UA, DL, AA intentionally omitted — product quality below standard
        ],

        "australia": [
            "SQ",  # Singapore Airlines — outstanding, excellent HKG-SIN-AUS routing
            "QF",  # Qantas — Australian flag carrier, direct or via SIN/DXB
        ],

        "new_zealand": [
            "NZ",  # Air New Zealand — flag carrier
            "SQ",  # Singapore Airlines via SIN
            "QF",  # Qantas via Sydney
        ],

        "uk": [
            "QR",  # Qatar Airways — excellent HKG-DOH-LHR/LGW, 5-star product
            "EK",  # Emirates — HKG-DXB-LHR/MAN/BHX etc, great frequency
            "BA",  # British Airways — flag carrier, direct LHR
            "LH",  # Lufthansa via FRA (connects to LHR via FRA)
            "KL",  # KLM via AMS
            "AF",  # Air France via CDG
        ],

        "europe_western": [
            "QR",  # Qatar — superb product, HKG-DOH-[CDG/FRA/AMS/ZRH/FCO etc]
            "EK",  # Emirates — massive Europe network via Dubai
            "LH",  # Lufthansa — FRA hub, excellent intra-Europe
            "AF",  # Air France — CDG hub
            "KL",  # KLM — AMS hub
            "LX",  # Swiss — ZRH hub
            "BA",  # British Airways via LHR
        ],

        "europe_southern": [
            "QR",  # Qatar — strong Southern Europe network
            "EK",  # Emirates
            "AF",  # Air France via CDG
            "LH",  # Lufthansa via FRA
        ],

        "europe_northern": [
            "LH",  # Lufthansa
            "KL",  # KLM
            "QR",  # Qatar via Doha
            "EK",  # Emirates
        ],

        "europe_eastern": [
            "LH",  # Lufthansa — best connections to Eastern Europe via FRA
            "QR",  # Qatar
            "EK",  # Emirates
            "AF",  # Air France
            "KL",  # KLM
        ],

        "japan": [
            "JL",  # Japan Airlines — flag carrier, excellent product
            "NH",  # ANA — 5-star, alternative to JL
            # (CX already does HKG-TYO/OSA directly — these are alternatives)
        ],

        "korea": [
            "KE",  # Korean Air — flag carrier, direct HKG-ICN
            "OZ",  # Asiana — second Korean flag carrier
        ],

        "southeast_asia": [
            "SQ",  # Singapore Airlines — best in class for SE Asia
            "TG",  # Thai Airways — good for Bangkok hub
            "MH",  # Malaysia Airlines — good for KUL hub
            "GA",  # Garuda Indonesia — flag carrier for Indonesia
            "PR",  # Philippine Airlines — flag carrier
            "VN",  # Vietnam Airlines — decent full-service
        ],


        "middle_east": [
            "QR",  # Qatar Airways — if destination IS Qatar, still valid connector
            "EK",  # Emirates — if going to UAE or connecting
            "SQ",  # Singapore Airlines via SIN (for Gulf destinations)
        ],

        "africa": [
            "EK",  # Emirates — unmatched Africa network via Dubai
            "QR",  # Qatar via Doha — strong Africa coverage
        ],

        "south_america": [
            "QR",  # Qatar via Doha — surprisingly good HKG to South America
            "EK",  # Emirates via Dubai — some South America routes
            "LH",  # Lufthansa via FRA — good South America connections
            "AF",  # Air France via CDG — strong South America (Air France/KLM group)
        ],

        "china_mainland": [
            "CA",  # Air China — flag carrier, direct from HKG
            "MU",  # China Eastern — strong domestic China network
            "CZ",  # China Southern — Guangzhou hub
        ],

        "taiwan": [
            "CI",  # China Airlines — flag carrier Taiwan
            "BR",  # EVA Air — excellent 5-star Taiwanese carrier
        ],
      }

    return carriers, blocked, route_preference


# ─── CONSTANTS ────────────────────────────────────────────────────────────────

HKG_CODES: frozenset = frozenset({"HKG", "HKI"})

CLASS_MAP: dict = {
    "ECONOMY": 1,
    "PREMIUM_ECONOMY": 2,
    "BUSINESS": 3,
    "FIRST": 4,
}


# ─── LOGIC FUNCTIONS ──────────────────────────────────────────────────────────

def is_cx(carrier):
    return carrier in ("CX", "KA")


def result_has_cx(r):
    all_segs = r.get("outbound_flights", []) + r.get("return_flights", [])
    return any(is_cx(seg.get("airline", "")) for seg in all_segs)


def primary_carrier(flights):
    return flights[0].get("airline", "??") if flights else "??"


def hkg_route(origin, destination):
    return origin.upper() in HKG_CODES or destination.upper() in HKG_CODES


def select_three_options(all_results, origin, destination, region_pref = None):
    """
    Select exactly 3 options from raw SerpApi results.
    Slot 1 — CX if HKG route. Slots 2 & 3 — best from region_pref or global order.
    Returns (selected, notes).
    """
    carriers, blocked, _ = carrier_preference()
    notes = []
    is_hkg = hkg_route(origin, destination)

    def is_result_blocked(r):
        all_segs = r.get("outbound_flights", []) + r.get("return_flights", [])
        for seg in all_segs:
            if seg.get("airline", "") in blocked:
                return True
            if seg.get("operated_by", "") in blocked:
                return True
        return False

    approved = [r for r in all_results if not is_result_blocked(r)]
    if not approved:
        approved = all_results
        notes.append(
            "⚠️  No major full-service carrier found on this route. "
            "Showing best available — verify safety record before booking."
        )

    # Deduplicate — one result per airline, best price wins
    by_carrier = {}
    for r in approved:
        c = primary_carrier(r.get("outbound_flights", []))
        if c not in by_carrier or r.get("price", 9999) < by_carrier[c].get("price", 9999):
            by_carrier[c] = r

    # Sort: CX pinned to slot 1 on HKG routes, then region preference, then global
    def sort_key(r):
        c = primary_carrier(r.get("outbound_flights", []))
        cx_pin = 0 if (is_hkg and is_cx(c)) else 1
        if region_pref and c in region_pref:
            route_score = region_pref.index(c)
        else:
            route_score = 100 + carriers.get(c, 99)
        return (cx_pin, route_score, r.get("price", 9999))

    selected = sorted(by_carrier.values(), key=sort_key)[:3]

    if is_hkg and selected and result_has_cx(selected[0]):
        notes.append("Option 1: Cathay Pacific (CX) — home carrier from HKG.")
    elif is_hkg:
        notes.append(
            "ℹ️  Cathay Pacific has no direct service on this route — "
            "showing best full-service alternatives."
        )
    if len(selected) < 3:
        notes.append(
            f"ℹ️  Only {len(selected)} approved full-service carrier(s) "
            "found for these dates and route."
        )

    return selected, notes