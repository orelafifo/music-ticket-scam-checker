"""End-to-end checks with the real Qwen2.5-VL model.

Needs the Ollama app open and the model downloaded. Slow, so it only runs when asked:
    pytest -m slow
"""

from pathlib import Path

import pytest
import requests

from scam_checker.local_ai import OLLAMA_URL
from scam_checker.privacy.ai_names import OllamaNameFinder
from scam_checker.privacy.names import CombinedNameFinder, redact_names
from scam_checker.screenshot.image_prep import fingerprint, open_image
from scam_checker.screenshot.ocr import CachedTextReader, OllamaVisionReader
from scam_checker.step1 import read_and_clean_screenshot

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "fake_whatsapp_chat.png"


def ollama_is_running() -> bool:
    try:
        return requests.get(OLLAMA_URL, timeout=2).ok
    except requests.ConnectionError:
        return False


@pytest.mark.slow
def test_example_screenshot_is_read_and_cleaned(spacy_name_finder):
    if not ollama_is_running():
        pytest.skip("Ollama isn't running")
    image_bytes = EXAMPLE.read_bytes()
    report = read_and_clean_screenshot(
        open_image(image_bytes),
        fingerprint(image_bytes),
        CachedTextReader(OllamaVisionReader()),
        CombinedNameFinder(spacy_name_finder, OllamaNameFinder()),
        artist="Dave",
        remove_bars=True,
    )
    for warning_sign in ["Bank transfer", "PayPal", "Twickets", "85 each", "Dave"]:
        assert warning_sign in report.cleaned_text
    for personal_detail in ["Jess Smith", "07123", "14:32", "Type a message"]:
        assert personal_detail not in report.cleaned_text


@pytest.mark.slow
def test_ai_finds_names_spacy_misses():
    if not ollama_is_running():
        pytest.skip("Ollama isn't running")
    text = "~Megan 💜💖💜\nHey guys, anyone want Olivia Rodrigo at The O2? text me x\nthanks jess"
    cleaned, _ = redact_names(text, "Olivia Rodrigo", OllamaNameFinder())
    assert "Megan" not in cleaned and "jess" not in cleaned
    assert "Olivia Rodrigo" in cleaned and "The O2" in cleaned


@pytest.mark.slow
def test_ai_finds_group_chat_titles():
    if not ollama_is_running():
        pytest.skip("Ollama isn't running")
    text = "Taylor Swift Eras Resale UK 🎟️\n~Megan: still got 2 for Wembley, PayPal friends and family only"
    cleaned, _ = redact_names(text, "Taylor Swift", OllamaNameFinder())
    assert "Eras Resale UK" not in cleaned and "Megan" not in cleaned
    assert "Wembley" in cleaned and "PayPal" in cleaned


@pytest.mark.slow
@pytest.mark.parametrize(
    "text",
    ["Hi I am Oreoluwa, still selling the tickets", "hi its orela, still got them?", "Thanks Zayba, sending now"],
)
def test_ai_finds_less_common_names(text):
    if not ollama_is_running():
        pytest.skip("Ollama isn't running")
    cleaned, removed = redact_names(text, "Dave", OllamaNameFinder())
    assert removed["name"] == 1, cleaned


@pytest.mark.slow
def test_ai_finds_usernames_shown_without_an_at_sign():
    if not ollama_is_running():
        pytest.skip("Ollama isn't running")
    text = "megs.tix selling 2 for Wembley, dm me\nzayba_22 how much?"
    cleaned, _ = redact_names(text, "Dave", OllamaNameFinder())
    assert "megs.tix" not in cleaned and "zayba_22" not in cleaned
    assert "Wembley" in cleaned
