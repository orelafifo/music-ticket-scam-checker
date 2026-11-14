from PIL import Image

from scam_checker.screenshot.ocr import CachedTextReader, TextBox
from scam_checker.step1 import Step1Result, read_and_clean_screenshot

from .conftest import FakeNameFinder

CHAT_SCREENSHOT_BOXES = [
    TextBox("Jess Smith", 0.02, 0.05, 0.2),
    TextBox("+44 7123 456789", 0.06, 0.09, 0.2),
    TextBox("Hi Jess, still got the Dave tickets?", 0.30, 0.33, 0.1),
    TextBox("14:02", 0.30, 0.33, 0.8),
    TextBox("Yes £85 each, bank transfer only, PayPal is down", 0.40, 0.43, 0.1),
    TextBox("Seen", 0.45, 0.48, 0.8),
    TextBox("Type a message", 0.95, 0.98, 0.1),
]


class FixedReader:
    def read(self, image):
        return CHAT_SCREENSHOT_BOXES


def run_pipeline(remove_bars: bool) -> str:
    report = read_and_clean_screenshot(
        image=Image.new("RGB", (100, 200)),
        image_fingerprint="test",
        reader=CachedTextReader(FixedReader()),
        name_finder=FakeNameFinder("Jess Smith", "Jess"),
        artist="Dave",
        remove_bars=remove_bars,
    )
    return report.cleaned_text


def test_chat_screenshot_is_cleaned_end_to_end():
    assert run_pipeline(remove_bars=True) == (
        "Hi [name], still got the Dave tickets?\nYes £85 each, bank transfer only, PayPal is down"
    )


def test_without_bar_removal_the_patterns_still_catch_personal_details():
    cleaned = run_pipeline(remove_bars=False)
    assert "Jess" not in cleaned and "7123" not in cleaned
    assert cleaned.startswith("[name]\n[phone]")


def test_step1_result_can_be_handed_on_as_plain_data():
    result = Step1Result(artist="Dave", source_app="WhatsApp", cleaned_text="hello")
    data = result.to_dict()
    assert data["seller_source"] == "not sure"
    assert data["seller_account"] == {"follower_count": None, "account_age_months": None}
