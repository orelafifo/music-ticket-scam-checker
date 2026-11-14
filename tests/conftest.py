"""Shared test helpers."""

from __future__ import annotations

import re

import pytest

from scam_checker.privacy.names import NameSpan


class FakeNameFinder:
    """Treats every capitalised word in `names` as a person name. Fast and predictable."""

    def __init__(self, *names: str):
        self._names = names

    def find_names(self, text: str) -> list[NameSpan]:
        spans = []
        for name in self._names:
            for match in re.finditer(rf"\b{re.escape(name)}\b", text):
                spans.append(NameSpan(match.start(), match.end(), match.group()))
        return spans


@pytest.fixture(scope="session")
def spacy_name_finder():
    """The real spaCy finder. Tests using it are skipped if the model isn't installed."""
    spacy = pytest.importorskip("spacy")
    from scam_checker.privacy.names import DEFAULT_SPACY_MODEL, SpacyNameFinder

    if not spacy.util.is_package(DEFAULT_SPACY_MODEL):
        pytest.skip(f"spaCy model {DEFAULT_SPACY_MODEL} not installed")
    return SpacyNameFinder()
