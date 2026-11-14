"""Remove timestamps and app words ("Reply", "Seen", "Typing…") that OCR picks up.

These carry no meaning for a scam check, and timestamps can help identify a
conversation, so they go before anything else happens to the text.
"""

from __future__ import annotations

import re

CLOCK_TIME = re.compile(r"\b(?:[01]?\d|2[0-3]):[0-5]\d(?:\s?[ap]\.?m\.?)?\b", re.IGNORECASE)
# OCR often reads the colon in "14:32" as a dot. A dotted time is only trusted
# at the very end of a line (where chat apps print it) and never after a
# currency sign, so prices like "£12.50" are left alone.
DOTTED_TIME_AT_END = re.compile(r"(?<![£$€\d.,])\b(?:[01]?\d|2[0-3])\.[0-5]\d(?:\s?[ap]m)?$", re.IGNORECASE)

# A whole line that is only a time or date marker, e.g. "2h", "Yesterday", "Mon", "14/11/2026".
TIMESTAMP_LINE = re.compile(
    r"(?:today|yesterday|now|just now|"
    r"\d+\s?(?:s|m|min|mins|h|hr|hrs|d|w|wk|y)(?:\s?ago)?|"
    r"\d+\s(?:second|minute|hour|day|week|month|year)s?\sago|"
    r"(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*|"
    r"\d{1,2}/\d{1,2}(?:/\d{2,4})?|"
    r"(?:[01]?\d|2[0-3])[:.][0-5]\d(?:\s?[ap]m)?)",
    re.IGNORECASE,
)

# Whole lines made only of these are removed, whatever their capitals.
APP_WORDS = {
    "reply",
    "replies",
    "view replies",
    "like",
    "likes",
    "liked",
    "seen",
    "typing",
    "typing...",
    "typing…",
    "online",
    "offline",
    "active now",
    "delivered",
    "read",
    "edited",
    "sent",
    "follow",
    "following",
    "message",
    "share",
    "translate",
    "see translation",
    "send message",
    "add comment",
    "add a comment...",
    "type a message",
}
LIKE_COUNT = re.compile(r"\d[\d,.]*k?\s(?:likes?|replies|comments?)", re.IGNORECASE)
LAST_SEEN = re.compile(r"last seen.*", re.IGNORECASE)
TICK_MARKS = re.compile(r"[✓✔]+")

# At the END of a line, only the capitalised app spellings (and short ages like
# "2d" before TikTok's "Reply") are removed. This keeps ordinary sentences such
# as "...if you'd like" intact.
TRAILING_APP_WORD = re.compile(r"\s+(?:Reply|Like|Seen|Delivered|Read|Edited|Sent|\d{1,2}[smhdw])$")


def remove_clock_times(line: str) -> tuple[str, int]:
    cleaned, colon_count = CLOCK_TIME.subn("", line)
    cleaned, dotted_count = DOTTED_TIME_AT_END.subn("", _tidy_spaces(cleaned))
    return _tidy_spaces(cleaned), colon_count + dotted_count


def is_timestamp_line(line: str) -> bool:
    return bool(TIMESTAMP_LINE.fullmatch(line.strip(" ·•.,")))


def is_app_clutter_line(line: str) -> bool:
    text = line.strip(" ·•").lower()
    return text in APP_WORDS or bool(LIKE_COUNT.fullmatch(text) or LAST_SEEN.fullmatch(text))


def strip_trailing_app_words(line: str) -> tuple[str, int]:
    """Returns (line without trailing app words or ticks, number of words removed)."""
    line = TICK_MARKS.sub("", line).rstrip()
    removed_count = 0
    while match := TRAILING_APP_WORD.search(line):
        line = line[: match.start()].rstrip()
        removed_count += 1
    return line, removed_count


def _tidy_spaces(text: str) -> str:
    return re.sub(r"\s{2,}", " ", text).strip()
