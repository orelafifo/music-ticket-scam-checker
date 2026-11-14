"""Find person names with spaCy and replace every one that isn't the artist with [name].

spaCy is a language toolkit; its small English model labels words that look
like person names. It learned from examples rather than fixed rules, so it
will miss some names (see "Known limits" in the README).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..context.artists import matches_artist
from .protected_words import contains_protected_word

NAME_PLACEHOLDER = "[name]"
DEFAULT_SPACY_MODEL = "en_core_web_sm"


@dataclass(frozen=True)
class NameSpan:
    start: int
    end: int
    text: str


class NameFinder(Protocol):
    """Anything that can find person names in text. Lets tests use a fake finder."""

    def find_names(self, text: str) -> list[NameSpan]: ...


class SpacyNameFinder:
    def __init__(self, model_name: str = DEFAULT_SPACY_MODEL):
        import spacy

        self._nlp = spacy.load(model_name, disable=["parser", "lemmatizer"])

    def find_names(self, text: str) -> list[NameSpan]:
        entities = self._nlp(text).ents
        return [NameSpan(ent.start_char, ent.end_char, ent.text) for ent in entities if ent.label_ == "PERSON"]


def should_keep_name(name: str, artist: str) -> bool:
    is_placeholder = "[" in name or "]" in name
    return is_placeholder or matches_artist(name, artist) or contains_protected_word(name)


def redact_names(text: str, artist: str, name_finder: NameFinder) -> tuple[str, int]:
    """Returns (text with names replaced, number of names replaced)."""
    names_to_replace = [
        span for span in _without_overlaps(name_finder.find_names(text)) if not should_keep_name(span.text, artist)
    ]
    # Work from the end so earlier character positions stay correct.
    for span in reversed(names_to_replace):
        text = text[: span.start] + NAME_PLACEHOLDER + text[span.end :]
    return text, len(names_to_replace)


def _without_overlaps(spans: list[NameSpan]) -> list[NameSpan]:
    """Keep the longest span where two overlap, e.g. "Jess Smith" over "Jess". Sorted by position."""
    kept: list[NameSpan] = []
    for span in sorted(spans, key=lambda s: (s.start, -(s.end - s.start))):
        if not kept or span.start >= kept[-1].end:
            kept.append(span)
    return kept
