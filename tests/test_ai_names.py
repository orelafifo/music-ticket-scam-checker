"""Tests for the AI name finder and for combining it with spaCy. Ollama is faked."""

import pytest

from scam_checker.local_ai import LocalAIError, OllamaChat
from scam_checker.privacy.ai_names import OllamaNameFinder, parse_names
from scam_checker.privacy.names import CachedNameFinder, CombinedNameFinder, redact_names

from .conftest import FakeNameFinder
from .fakes import fake_post

MEGAN_POST = "~Megan 💜💖💜\nHey guys, anyone want Olivia Rodrigo at The O2? text me x\nthanks jess"


def ai_finder(model_reply: str, sent: list | None = None) -> OllamaNameFinder:
    return OllamaNameFinder(OllamaChat(post=fake_post(model_reply, sent)))


def test_names_spacy_misses_are_removed():
    finder = ai_finder('{"names": ["Megan", "Jess"]}')
    cleaned, removed = redact_names(MEGAN_POST, "Olivia Rodrigo", finder)
    assert cleaned == "~[name] 💜💖💜\nHey guys, anyone want Olivia Rodrigo at The O2? text me x\nthanks [name]"
    assert removed == 2


def test_names_the_model_invents_are_ignored():
    finder = ai_finder('{"names": ["Bob Smith"]}')
    assert finder.find_names(MEGAN_POST) == []


def test_artist_is_kept_even_if_the_model_lists_part_of_it():
    finder = ai_finder('{"names": ["Olivia", "Megan"]}')
    cleaned, _ = redact_names(MEGAN_POST, "Olivia Rodrigo", finder)
    assert "Olivia Rodrigo" in cleaned and "Megan" not in cleaned


def test_venue_listed_by_mistake_is_kept():
    finder = ai_finder('{"names": ["The O2"]}')
    cleaned, removed = redact_names(MEGAN_POST, "Olivia Rodrigo", finder)
    assert "The O2" in cleaned and removed == 0


def test_text_is_sent_as_data_and_a_json_reply_is_requested():
    sent = []
    ai_finder('{"names": []}', sent).find_names("hello")
    assert sent[0]["format"] == "json"
    assert "<text>\nhello\n</text>" in sent[0]["messages"][0]["content"]


def test_broken_reply_stops_the_check_rather_than_risk_missing_names():
    with pytest.raises(LocalAIError):
        parse_names("sorry, I can't help with that")


def test_combined_finder_removes_a_name_either_finder_found():
    combined = CombinedNameFinder(FakeNameFinder("Jess"), ai_finder('{"names": ["Megan"]}'))
    cleaned, removed = redact_names("~Megan and Jess", "Dave", combined)
    assert cleaned == "~[name] and [name]" and removed == 2


def test_ai_is_asked_only_once_for_the_same_text():
    sent = []
    cached = CachedNameFinder(ai_finder('{"names": ["Megan"]}', sent))
    cached.find_names(MEGAN_POST)
    cached.find_names(MEGAN_POST)
    assert len(sent) == 1
