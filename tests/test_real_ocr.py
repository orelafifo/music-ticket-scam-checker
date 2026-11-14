"""End-to-end check with the real OCR model on the made-up example screenshot.

Slow (about 20 seconds, plus a one-off model download), so it only runs when asked:
    pytest -m slow
"""

from pathlib import Path

import pytest

from scam_checker.screenshot.image_prep import fingerprint, open_image
from scam_checker.screenshot.ocr import CachedTextReader, EasyOcrReader
from scam_checker.step1 import read_and_clean_screenshot

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "fake_whatsapp_chat.png"


@pytest.mark.slow
def test_example_screenshot_is_read_and_cleaned(spacy_name_finder):
    pytest.importorskip("easyocr")
    image_bytes = EXAMPLE.read_bytes()
    report = read_and_clean_screenshot(
        open_image(image_bytes),
        fingerprint(image_bytes),
        CachedTextReader(EasyOcrReader()),
        spacy_name_finder,
        artist="Dave",
        remove_bars=True,
    )
    text = report.cleaned_text
    # OCR sometimes reads "£" as "€", so only the amount is checked.
    for warning_sign in ["Bank transfer", "PayPal", "Twickets", "85 each", "Dave"]:
        assert warning_sign in text
    for personal_detail in ["Jess", "07123", "14:32", "14.32", "Seen", "Type a message"]:
        assert personal_detail not in text
