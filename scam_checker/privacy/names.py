"""Find person names and replace every one that isn't the artist with [name].

Two finders run together and any name either one finds is removed:
  * spaCy, a language toolkit whose small English model labels words that look
    like person names. It is fast but relies on capital letters, so it misses
    names like "hi jess" or "~Megan 💜".
  * Qwen, the local AI model (see ai_names.py), which understands the text and
    can tell a person from an artist or venue.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Protocol

from ..context.artists import matches_artist
from .protected_words import contains_protected_word

PERSON = "name"
CHAT_TITLE = "chat title"
PLACEHOLDERS = {PERSON: "[name]", CHAT_TITLE: "[title]"}
DEFAULT_SPACY_MODEL = "en_core_web_sm"


@dataclass(frozen=True)
class NameSpan:
    start: int
    end: int
    text: str
    kind: str = PERSON  # PERSON, or CHAT_TITLE for a group chat or channel name


class NameFinder(Protocol):
    """Anything that can find names (people, chat titles) in text. Lets tests use a fake finder."""

    def find_names(self, text: str) -> list[NameSpan]: ...


class SpacyNameFinder:
    def __init__(self, model_name: str = DEFAULT_SPACY_MODEL):
        import spacy

        self._nlp = spacy.load(model_name, disable=["parser", "lemmatizer"])

    def find_names(self, text: str) -> list[NameSpan]:
        entities = self._nlp(text).ents
        return [NameSpan(ent.start_char, ent.end_char, ent.text) for ent in entities if ent.label_ == "PERSON"]


class CombinedNameFinder:
    """Runs several finders and returns every name any of them found."""

    def __init__(self, *finders: NameFinder):
        self._finders = finders

    def find_names(self, text: str) -> list[NameSpan]:
        return [span for finder in self._finders for span in finder.find_names(text)]


class CachedNameFinder:
    """Remembers the latest result, so the app doesn't ask the AI again on every screen refresh.

    Create one per user session: it holds names found in that user's text.
    """

    def __init__(self, finder: NameFinder):
        self._finder = finder
        self._results: dict[str, list[NameSpan]] = {}

    def find_names(self, text: str) -> list[NameSpan]:
        if text not in self._results:
            self._results = {text: self._finder.find_names(text)}  # keep only the latest
        return self._results[text]


def should_keep(span: NameSpan, artist: str) -> bool:
    if "[" in span.text or "]" in span.text or matches_artist(span.text, artist):
        return True
    # A group called "Twickets resale UK" still identifies a group, so platform
    # and payment words only save people's names that were mistaken for them.
    return span.kind == PERSON and contains_protected_word(span.text)


def redact_names(text: str, artist: str, name_finder: NameFinder) -> tuple[str, Counter]:
    """Returns (text with names and chat titles replaced, count per kind)."""
    artist_spans = find_word(text, artist)
    to_replace = [
        span
        for span in _without_overlaps(name_finder.find_names(text))
        if not should_keep(span, artist) and not _inside_any(span, artist_spans)
    ]
    # Work from the end so earlier character positions stay correct.
    for span in reversed(to_replace):
        text = text[: span.start] + PLACEHOLDERS[span.kind] + text[span.end :]
    return text, Counter(span.kind for span in to_replace)


def find_word(text: str, word: str, kind: str = PERSON) -> list[NameSpan]:
    """Every whole-word, case-insensitive occurrence of `word` in `text`."""
    if not word.strip():
        return []
    pattern = rf"(?<!\w){re.escape(word.strip())}(?!\w)"
    return [NameSpan(m.start(), m.end(), m.group(), kind) for m in re.finditer(pattern, text, re.IGNORECASE)]


def _inside_any(span: NameSpan, others: list[NameSpan]) -> bool:
    # Stops a first name alone ("Olivia") being removed from inside the artist's name ("Olivia Rodrigo"),
    # while a longer name that only starts with the artist's ("Dave Smith") is still removed.
    return any(other.start <= span.start and span.end <= other.end for other in others)


def _without_overlaps(spans: list[NameSpan]) -> list[NameSpan]:
    """Keep the longest span where two overlap, e.g. "Jess Smith" over "Jess". Sorted by position."""
    kept: list[NameSpan] = []
    for span in sorted(spans, key=lambda s: (s.start, -(s.end - s.start))):
        if not kept or span.start >= kept[-1].end:
            kept.append(span)
    return kept
