"""Check the listing against the real event, the same way as in v2.

Answers four questions:
  1. Does this event exist?                -> found
  2. Do the date and venue match?          -> details_match
  3. Is it a sold-out / high-demand show?  -> high_demand
  4. Is it being sold before general sale? -> before_on_sale
It also records whether the event uses app-only tickets, the event status
(e.g. cancelled) and the official date and venue.

Sources (free keys go in .env, see .env.example):
  * Ticketmaster Discovery API: TICKETMASTER_API_KEY (developer.ticketmaster.com)
  * Skiddle Events API: SKIDDLE_API_KEY (skiddle.com/api/join.php). Skiddle's terms
    say its name must be credited wherever its data is shown.
  * AXS, See Tickets, DICE, Eventim and Gigantic have no public API.

Only the artist's name (and the month, for Skiddle) is sent. Never the listing.

True / False / None: None means "couldn't check", which never counts against
the seller. With no key, no internet or no result, the check says so honestly.
An event is only "not found" if every source was searched and none had it; as
the official seller is not asked, a missing event is treated as "couldn't check".
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime
from difflib import SequenceMatcher

import requests

TICKETMASTER_URL = "https://app.ticketmaster.com/discovery/v2/events.json"
SKIDDLE_URL = "https://www.skiddle.com/api/v1/events/search/"
GENERIC_VENUE_WORDS = {"the", "arena", "stadium", "london", "manchester", "birmingham", "live", "hall"}
TIMEOUT_SECONDS = 6


@dataclass
class OfficialEvent:
    date: date | None
    venue: str
    on_sale: date | None = None
    status: str | None = None  # onsale / offsale / cancelled / postponed
    high_demand: bool = False
    app_only: bool | None = None


@dataclass
class EventReport:
    artist: str
    venue_in_listing: str = ""
    date_in_listing: str = ""  # ISO date, or "" if none was read
    found: bool | None = None  # None = couldn't check
    details_match: bool | None = None
    high_demand: bool = False
    before_on_sale: bool = False
    app_only: bool | None = None
    status: str | None = None
    official_date: str | None = None
    official_venue: str | None = None
    source: str = "none"
    notes: list[str] = field(default_factory=list)

    @property
    def mismatch(self) -> bool:
        return self.found is True and self.details_match is False


EventFetcher = Callable[[str, date | None], list[OfficialEvent]]


# --- matching ----------------------------------------------------------------


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", str(text).lower()).strip()


def venue_matches(a: str, b: str) -> bool:
    """'O2 Arena' should match 'The O2'. Share a meaningful word, or look similar."""
    a, b = _norm(a), _norm(b)
    if not a or not b:
        return False
    if (set(a.split()) - GENERIC_VENUE_WORDS) & (set(b.split()) - GENERIC_VENUE_WORDS):
        return True
    return SequenceMatcher(None, a, b).ratio() > 0.75


def artist_matches(query: str, name: str) -> bool:
    return _norm(query) in _norm(name) or SequenceMatcher(None, _norm(query), _norm(name)).ratio() > 0.85


FESTIVAL = re.compile(r"festival|\bfest\b|weekender", re.IGNORECASE)


def is_festival(name: str) -> bool:
    return bool(FESTIVAL.search(name))


def dates_match(official: date | None, listed: date, festival: bool) -> bool:
    """Gigs must match exactly. Festivals run over several days but are listed under one date
    (e.g. Reading on its first day), so any day from 1 day before to 5 days after counts."""
    if official is None:
        return False
    if festival:
        return -1 <= (listed - official).days <= 5
    return official == listed


def judge(
    events: list[OfficialEvent], artist: str, venue: str, event_date: date | None, today: date, source: str
) -> EventReport:
    report = EventReport(artist, venue, event_date.isoformat() if event_date else "", source=source)
    if not events:
        report.found = False
        report.notes.append("No official event found for this artist.")
        return report

    festival = is_festival(artist)

    def is_match(event: OfficialEvent) -> bool:
        ok_venue = venue_matches(venue, event.venue) if venue else True
        ok_date = dates_match(event.date, event_date, festival) if event_date else True
        return ok_venue and ok_date

    matches = [event for event in events if is_match(event)]
    # Show the closest official event: same venue first, then nearest date.
    best = (
        matches[0]
        if matches
        else min(
            events,
            key=lambda e: (
                not (venue and venue_matches(venue, e.venue)),
                abs((e.date - (event_date or today)).days) if e.date else 9999,
            ),
        )
    )
    report.found = True
    report.details_match = bool(matches)
    report.high_demand = best.high_demand
    report.before_on_sale = bool(best.on_sale and today < best.on_sale)
    report.app_only = best.app_only
    report.status = best.status
    report.official_date = best.date.isoformat() if best.date else None
    report.official_venue = best.venue
    report.notes.append(
        "Matched an official event." if matches else "The artist is touring, but not on this date or at this venue."
    )
    return report


# --- sources -----------------------------------------------------------------


def ticketmaster_events(api_key: str, get=requests.get) -> EventFetcher:
    def fetch(artist: str, event_date: date | None) -> list[OfficialEvent]:
        params = {
            "apikey": api_key,
            "keyword": artist,
            "countryCode": "GB",
            "classificationName": "music",
            "size": 100,
            "sort": "date,asc",
        }
        response = get(TICKETMASTER_URL, timeout=TIMEOUT_SECONDS, params=params)
        response.raise_for_status()
        events = []
        for e in response.json().get("_embedded", {}).get("events", []):
            names = [e.get("name", "")] + [a.get("name", "") for a in e.get("_embedded", {}).get("attractions", [])]
            if not any(artist_matches(artist, name) for name in names):
                continue
            start = e.get("dates", {}).get("start", {}).get("localDate")
            status = e.get("dates", {}).get("status", {}).get("code")
            on_sale = e.get("sales", {}).get("public", {}).get("startDateTime")
            day = date.fromisoformat(start) if start else None
            events.append(
                OfficialEvent(
                    date=day,
                    venue=(e.get("_embedded", {}).get("venues") or [{}])[0].get("name", ""),
                    on_sale=datetime.fromisoformat(on_sale.replace("Z", "+00:00")).date() if on_sale else None,
                    status=status,
                    # "offsale" before the show has happened usually means sold out
                    high_demand=status == "offsale" and day is not None and day >= date.today(),
                    # Assumption (as in v2): UK Ticketmaster shows use app tickets. Verify per tour.
                    app_only=True,
                )
            )
        return events

    return fetch


def skiddle_events(api_key: str, get=requests.get) -> EventFetcher:
    def fetch(artist: str, event_date: date | None) -> list[OfficialEvent]:
        params = {"api_key": api_key, "keyword": artist, "limit": 100, "description": 1}
        if event_date:  # narrow the search to the month around the date
            params["minDate"] = date(event_date.year, event_date.month, 1).isoformat()
        response = get(SKIDDLE_URL, timeout=TIMEOUT_SECONDS, params=params)
        response.raise_for_status()
        events = []
        for e in response.json().get("results", []) or []:
            names = [e.get("eventname", "")] + [a.get("name", "") for a in (e.get("artists") or [])]
            if not any(artist_matches(artist, name) for name in names):
                continue
            day = e.get("date") or (e.get("startdate") or "")[:10]
            events.append(
                OfficialEvent(
                    date=date.fromisoformat(day) if day else None,
                    venue=(e.get("venue") or {}).get("name", ""),
                    status="cancelled" if str(e.get("cancelled", "0")) == "1" else "onsale",
                    app_only=None,  # Skiddle often uses e-tickets, so don't assume
                )
            )
        return events

    return fetch


def sources_from_env() -> dict[str, EventFetcher]:
    sources = {}
    if os.getenv("TICKETMASTER_API_KEY"):
        sources["Ticketmaster"] = ticketmaster_events(os.environ["TICKETMASTER_API_KEY"])
    if os.getenv("SKIDDLE_API_KEY"):
        sources["Skiddle"] = skiddle_events(os.environ["SKIDDLE_API_KEY"])
    return sources


# --- the check ---------------------------------------------------------------


def check_event(
    artist: str,
    venue: str = "",
    event_date: date | None = None,
    today: date | None = None,
    sources: dict[str, EventFetcher] | None = None,
) -> EventReport:
    today = today or date.today()
    sources = sources_from_env() if sources is None else sources
    if not artist.strip():
        return EventReport(artist, venue, notes=["No artist entered, so the event wasn't checked."])

    events, hits, problems = [], [], []
    for name, fetch in sources.items():
        try:
            found = fetch(artist, event_date)
        except Exception as error:  # network down, bad key, rate limit: carry on, never crash
            problems.append(f"{name} lookup failed ({error.__class__.__name__})")
            continue
        events += found
        if found:
            hits.append(name)

    if events:
        return judge(events, artist, venue, event_date, today, " + ".join(hits))
    if not sources:
        problems.append("No event data source set up (add TICKETMASTER_API_KEY or SKIDDLE_API_KEY to .env)")
    else:
        problems.append(
            f"Not found on {' or '.join(sources)}. Tickets may be sold by a site we can't search "
            "(e.g. AXS, See Tickets, DICE), so check the artist's official website"
        )
    report = EventReport(artist, venue, event_date.isoformat() if event_date else "")
    report.notes = problems + ["Event not checked."]
    return report
