"""Read the venue and date out of the cleaned listing text, as in v2.

The artist is already known (asked first in Step 1), so only the venue and
date are read. All on this computer, nothing is sent anywhere:
  1. a list of known UK venues ("The O2", "Wembley Stadium" ...);
  2. spaCy named-entity recognition for places (FAC) and dates (DATE);
  3. patterns like "@ The O2", "21st June", "April 9/27", "9/4/2027" and "2027-04-09".
Line breaks are treated as spaces, and dates are read the UK way (day before month).
The user can always correct what was read before the event is checked.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache

from dateutil import parser as date_parser

VENUES = [
    "OVO Arena Wembley", "Wembley Stadium", "Wembley", "The O2", "O2 Arena", "O2 Academy Brixton",
    "Brixton Academy", "Co-op Live", "AO Arena", "Manchester Arena", "Utilita Arena", "Tottenham Hotspur Stadium",
    "Emirates Stadium", "London Stadium", "Hyde Park", "Royal Albert Hall", "Alexandra Palace", "Ally Pally",
    "Eventim Apollo", "Hammersmith Apollo", "OVO Hydro", "Principality Stadium", "Murrayfield", "Hampden Park",
    "Bp Pulse Live", "Resorts World Arena", "First Direct Arena", "Motorpoint Arena", "SSE Arena", "3Arena",
    "Roundhouse", "Printworks", "Electric Ballroom", "M&S Bank Arena", "Piece Hall", "Villa Park", "Anfield",
    "Etihad Stadium", "Old Trafford", "Heaton Park", "Finsbury Park", "Victoria Park", "Hydro",
]  # fmt: skip
VENUE_WORDS = r"(arena|stadium|academy|hall|park|apollo|live|centre|center|ballroom|o2|hydro|palace|field)"
AT_VENUE = re.compile(r"(?:@|\bat)\s+((?:the\s+)?[A-Z0-9][\w'&-]*(?:\s+[A-Z0-9][\w'&-]*){0,3})")
MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}  # fmt: skip
_MONTH = (
    r"(?P<month>jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?"
    r"|sept?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?"
)
_DAY = r"(?P<day>[0-3]?\d)(?:st|nd|rd|th)?"
_YEAR = r"(?P<year>20\d\d|'?\d\d)"
_SEP = r"[\s,/.'-]+"
# The ways people write dates in listings, most reliable first. All read as UK dates (day before month).
DATE_PATTERNS = [
    re.compile(r"\b(?P<year>20\d\d)-(?P<month>\d{1,2})-(?P<day>\d{1,2})\b"),  # 2027-04-09
    # 9 April 2027, 9th April '27, 9th of Apr 27, Fri 9 April, 9-Apr-27
    re.compile(rf"\b{_DAY}(?:\s+of)?[\s-]*{_MONTH}(?![a-z])(?:{_SEP}{_YEAR}(?![\d:]))?", re.IGNORECASE),
    # April 9 2027, April 9th, 27, April 9/2027, Apr 9th '27
    re.compile(rf"\b{_MONTH}(?![a-z])\s*{_DAY}(?![\d:])(?:{_SEP}{_YEAR}(?![\d:]))?", re.IGNORECASE),
    # 9/4/2027, 09.04.27, 9-4-27
    re.compile(r"\b(?P<day>[0-3]?\d)[/.-](?P<month>[01]?\d)[/.-](?P<year>20\d\d|\d\d)\b"),
    re.compile(r"(?<![\d.£$€])\b(?P<day>[0-3]?\d)/(?P<month>[01]?\d)\b(?![/.]\d)"),  # 9/4 (no year)
]


@dataclass
class EventDetails:
    venue: str = ""
    event_date: date | None = None


@lru_cache(maxsize=1)
def _spacy():
    try:
        import spacy

        return spacy.load("en_core_web_sm")
    except Exception:  # model not installed: patterns only
        return None


def parse_date(text: str, today: date) -> date | None:
    if not re.search(r"\d", text):  # "Friday" alone isn't a usable date
        return None
    cleaned = re.sub(r"(\d+)(st|nd|rd|th)\b", r"\1", text, flags=re.IGNORECASE)
    try:
        found = date_parser.parse(cleaned, fuzzy=True, dayfirst=True, default=datetime(today.year, 1, 1)).date()
    except (ValueError, OverflowError):
        return None
    if not re.search(r"\b20\d\d\b", text) and found < today:  # "21 June" with no year = the next one
        found = found.replace(year=found.year + 1)
    return found


def find_venue(text: str) -> str:
    lower = text.lower()
    for venue in VENUES:  # longest names are listed first
        if re.search(rf"\b{re.escape(venue.lower())}\b", lower):
            return venue
    nlp = _spacy()
    if nlp is not None:
        for entity in nlp(text).ents:
            if entity.label_ == "FAC" or (entity.label_ == "ORG" and re.search(VENUE_WORDS, entity.text, re.I)):
                return entity.text.strip(" ,.")
    match = AT_VENUE.search(text)
    if match and re.search(VENUE_WORDS, match.group(1), re.IGNORECASE):
        return re.sub(r"^the\s+", "The ", match.group(1).strip(" ,."), flags=re.IGNORECASE)
    return ""


def _date_from_match(match: re.Match, today: date) -> date | None:
    month_text = match.group("month").lower().rstrip(".")
    month = int(month_text) if month_text.isdigit() else MONTHS.get(month_text[:3])
    year_text = (match.groupdict().get("year") or "").lstrip("'")
    year = None
    if year_text:
        year = int(year_text) if len(year_text) == 4 else 2000 + int(year_text)
        if not today.year - 1 <= year <= today.year + 3:  # "15 tickets" read as a year: ignore it
            year = None
    try:
        found = date(year or today.year, month, int(match.group("day")))
    except (TypeError, ValueError):  # e.g. 31 April, or month 20
        return None
    if year is None and found < today:  # "21 June" with no year = the next one
        found = found.replace(year=found.year + 1)
    return found


def find_date(text: str, today: date) -> date | None:
    for pattern in DATE_PATTERNS:
        for match in pattern.finditer(text):
            found = _date_from_match(match, today)
            if found:
                return found
    nlp = _spacy()
    if nlp is not None:
        for entity in nlp(text).ents:
            if entity.label_ == "DATE":
                found = parse_date(entity.text, today)
                if found:
                    return found
    return None


def read_event_details(text: str, today: date | None = None) -> EventDetails:
    today = today or date.today()
    text = " ".join(text.split())  # line breaks from the screenshot ("The" / "O2") become spaces
    return EventDetails(venue=find_venue(text), event_date=find_date(text, today))
