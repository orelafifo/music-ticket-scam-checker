"""Read the venue and date out of the cleaned listing text, as in v2.

The artist is already known (asked first in Step 1), so only the venue and
date are read. All on this computer, nothing is sent anywhere:
  1. a list of known UK venues ("The O2", "Wembley Stadium" ...);
  2. spaCy named-entity recognition for places (FAC) and dates (DATE);
  3. patterns like "@ The O2" and "21st June".
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
DATE_TEXT = re.compile(
    r"\b\d{1,2}(st|nd|rd|th)?\s+(of\s+)?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*(\s+20\d\d)?"
    r"|\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}(st|nd|rd|th)?(,?\s+20\d\d)?"
    r"|\b\d{1,2}/\d{1,2}(/\d{2,4})?\b",
    re.IGNORECASE,
)


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


def find_date(text: str, today: date) -> date | None:
    match = DATE_TEXT.search(text)
    if match:
        return parse_date(match.group(0), today)
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
    return EventDetails(venue=find_venue(text), event_date=find_date(text, today))
