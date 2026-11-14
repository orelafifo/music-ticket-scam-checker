"""The artist the user is buying tickets for: suggestions while typing, and forgiving name matching."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

ARTIST_SUGGESTIONS_FILE = Path(__file__).resolve().parents[2] / "data" / "artist_suggestions.txt"

# 0.85 lets through small OCR or typing slips ("Taylor Swfit", "Beyonce" vs
# "Beyoncé") but not a different name that only shares a first name ("Taylor").
SIMILARITY_NEEDED = 0.85


def load_artist_suggestions(path: Path = ARTIST_SUGGESTIONS_FILE) -> list[str]:
    """Suggestions only: the user can always type an artist that isn't on the list."""
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return sorted({line.strip() for line in lines if line.strip() and not line.startswith("#")}, key=str.lower)


def normalise_name(name: str) -> str:
    without_possessive = re.sub(r"['’]s\b", "", name.lower())
    letters_only = re.sub(r"[^a-z0-9 ]", " ", _strip_accents(without_possessive))
    return " ".join(letters_only.split())


def matches_artist(candidate: str, artist: str) -> bool:
    """True if the candidate is the artist's full name, allowing small spelling differences."""
    candidate, artist = normalise_name(candidate), normalise_name(artist)
    if not candidate or not artist:
        return False
    if candidate == artist or f" {artist} " in f" {candidate} ":
        return True
    return SequenceMatcher(None, candidate, artist).ratio() >= SIMILARITY_NEEDED


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char))
