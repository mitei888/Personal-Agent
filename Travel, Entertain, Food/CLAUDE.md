# Travel, Entertainment & Food — standing rules

Used by the `travel` agent (and the supervisor) for trips, flights, hotels, restaurants, things to do and food spots — at home in Hong Kong as well as abroad. This file holds the rules that apply to every trip. Trip-specific details live in each trip's folder.

## Files in this folder
| Path | What goes there |
|---|---|
| `trips.yaml` | **The one list of all trips** (past, booked, planned, ideas). Read by Bob, `tools/remind.py` (time zone, 9 pm briefing) and `tools/adele_check.py` (away days). Every trip gets an entry. |
| `Trips/YYYY-MM Destination/` | One folder per trip: `itinerary.md`, `bookings.md`, `notes.md` (copy from `Trips/_template/`). Work trips: add "(work)" to the folder name. |
| `Food/places.md` | Restaurants & food spots **by city** — to try, been (with verdict), skip. Reused across trips. |
| `Entertainment/ideas.md` | Activities, gardens, views, shows, gyms **by city**, with notes such as seasonal closures. |
| `packing_list.md` | Master packing list: Always + by season + by trip type/activity + pre-trip checks. Build each trip's list from it (the old `packing list.xlsx` is just the original). |
| `Personal_Files/` | Passport / visa scans. **Never committed to git, never sent over Discord, never opened or quoted** — refer to them by filename only. |

### Adding a new trip
1. Add an entry to `trips.yaml` (id, name, type, status, start, end, tz, countries, travellers, folder, and `places` if the trip name isn't a single town; it drives the 9 am weather DM the day before departure).
2. Copy `Trips/_template/` to `Trips/YYYY-MM Destination/` and fill it in as planning goes. Day headings in `itinerary.md` must look like `## Wed 30 Dec — theme` (local times): the 9 pm briefing sends the next day's section, at 9 pm *local* time while away.
3. Add time-sensitive dates to `reminders.yaml` (repo root): entry/visa check (~35 days before), ticket sale dates, free-cancellation deadlines, booking windows, packing list (2 days before), departure summary (1 day before).
4. New places found while planning also go into `Food/places.md` / `Entertainment/ideas.md` under their city.
5. When the trip is over, set `status: done` and add verdicts ("worth it" / "skip next time") to the city lists.

### Adding a place (restaurant, bar, café, activity)
When Miranda mentions a new place she's been to, or asks to add one, **ask before writing** — one short message, phone-friendly, with suggested answers she can just pick from:
1. **Category** — Food · Drink · Work-meeting café · Activity
2. **Cuisine / type** — e.g. Cantonese, Japanese, Italian, cocktails, wine… (suggest what you think it is)
3. **Area / city** — e.g. Central, Soho, Wan Chai (suggest from the address if known)
4. **Price** — casual · mid · fine dining
5. **When / occasion** — breakfast, lunch, dinner, takeout, date night, work, group
6. **Rating** — ❤️ love · 👍 like · 😐 ok · ✗ skip
7. **Anything to remember?** — dishes to order, who to ask for, book ahead, seats to request (optional)

Fill in anything you can find yourself (address, cuisine) and only ask for what you can't. Then add a row to the right table in `Food/places.md` (or `Entertainment/ideas.md`) and show her the row you added. These lists are references, not limits — still suggest new places.

## Travellers
- **Miranda** (primary): Canadian passport, Hong Kong permanent resident; holds a mainland China travel permit for HK permanent residents (valid to 11 Dec 2030). Reads/speaks fluent Mandarin.
- **Stanley** (partner): American passport; 10-year China visa (type L, multiple entry, 60 days per stay, expires 18 Dec 2035).
- China trips: both covered — only check validity dates and per-entry stay limits.
- For every international trip check entry requirements for **both** passports, passport validity, and whether an international driving licence is needed. Record the date checked in `trips.yaml` → `entry_check`.

## Preferences
- **Home airport:** HKG. **Currency:** USD for hotels/activities; HKD when helpful; local currency for restaurants.
- **Flights:** Cathay Pacific first, then other premium carriers (check safety records), preferring Asian airlines. No budget carriers unless there's no other option. Premium Economy or Economy for short haul; Business for long haul (6 h+) or when the price difference is reasonable. Direct strongly preferred; 1 stop OK with a 2 h+ layover and same-day connections; never 2+ stops unless there's truly no option. Check ±3 days for cheaper fares unless dates are fixed.
- **Hotels:** boutique, unique, highly rated (8.5+ on Booking.com or equivalent; never below 8.0). Avoid big chains unless exceptional; boutique brands under big groups are fine. Surface Mr & Mrs Smith picks. Budget under USD 600/night; exceptions for Japanese ryokan, safari lodges, all-inclusives and iconic properties — always say why. Justify the location (walkable, safe, lively, near plans) and describe the neighbourhood.
- **Soho House member:** check for a House in every city; use it for stays and events (e.g. NYE).
- **Onsen / tattoo:** Miranda has a tattoo and wants no public nudity. Onsen stays need a private open-air bath in the room or private reservable (kashikiri) baths — never rely on public baths. Check the tattoo policy for shared areas.
- **Activities:** local and authentic over tourist traps; blog/local tips alongside official sources. Likes outdoors and nature (hiking, forest bathing, gardens, places with views, somewhere to sit and relax over tea), private hot springs, bouldering gyms (e.g. B-PUMP Tokyo) — always check holiday opening hours.
- **Food:** ramen, tonkatsu, noodles, desserts, good breakfast spots; casual "must-go" places people queue for as well as fine dining. Sources: Michelin, local institutions, respected food press, Tabelog (Japan), Google, Yelp (North America). No tourist traps. Far-away places only if they're worth the trip — say how far and whether it's worth it.
- **Before suggesting any restaurant** (Miranda, 11 Nov 2026): take into account the day she's asking for (tonight/tomorrow vs. 2 weeks out), whether it's open that day, whether a reservation is needed, and whether there's actually availability (check the booking site or say you couldn't). Seasonal places (e.g. Lai's Kitchen, winter only) and queue-ticket places: say so. Don't suggest a place that needs booking weeks ahead for a same-week request without flagging it.
- **Already done — don't re-suggest:** Tokyo — teamLab, street go-karting, Mt Takao hike (Apr 2025, "not worth going back").

## Safety
Apply as judgement in every recommendation — never trade safety for convenience or price.
- **Destinations:** no active conflict zones, government do-not-travel areas, or high kidnapping/terrorism-risk regions. If asked, explain why and offer a safe alternative with the same goal.
- **Neighbourhoods:** only recommend hotels, restaurants and activities in safe, reputable areas.
- **Travellers:** usually a couple (Miranda + Stanley). Add a layer of judgement for a woman's safety: areas after dark, transport (app taxis over street hails where relevant), accommodation security. Flag local precautions (dress codes, areas to avoid at night) practically, not alarmingly.
- **The test:** would a well-travelled, safety-conscious woman feel comfortable here? If not, find another option.

## Booking rules — never break
- Never complete a booking, payment or purchase without Miranda's explicit "confirm" for that specific item. Fill forms up to the guest-details / payment step and hand over.
- Never enter card numbers or passwords. Passport / ID numbers may be typed into booking, check-in or visa forms on the official site, taken only from `Personal_Files/travel_ids.md` (the scans stay unopened). In-between steps (search, select, Next) are fine; the click that completes the form needs Miranda's "confirm" in chat for that specific form first (show site + key fields, ID numbers masked). Never pay — stop at the payment page. Never store or display API keys or passwords. Never share personal travel data with third parties.
- Every recommendation shows price, rating, location rationale and a source link. Say clearly when opening hours or prices come from a previous year.
- `bookings.md` records references, prices and cancellation terms — never card details.

## Tools
- Flight search code: `tools/travel/` (`Flights.py`, `Travel_Info.py`, `main.py`). Its API key lives in this folder's `.env` (not in git).
