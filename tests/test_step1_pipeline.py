from PIL import Image

from scam_checker.screenshot.ocr import CachedTextReader
from scam_checker.step1 import Step1Result, read_and_clean_screenshot

from .conftest import FakeNameFinder

# What the reading model might return for a full, untrimmed chat screenshot.
FULL_CHAT_LINES = [
    "Jess Smith",
    "+44 7123 456789",
    "Hi Jess, still got the Dave tickets? 14:02",
    "Yes £85 each, bank transfer only, PayPal is down",
    "Seen",
]


class RecordingReader:
    """Returns fixed lines and remembers the size of the image it was given."""

    def __init__(self):
        self.image_sizes = []

    def read(self, image):
        self.image_sizes.append(image.size)
        return FULL_CHAT_LINES


def run_pipeline(reader, remove_bars: bool) -> str:
    report = read_and_clean_screenshot(
        image=Image.new("RGB", (100, 1000)),
        image_fingerprint="test",
        reader=CachedTextReader(reader),
        name_finder=FakeNameFinder("Jess Smith", "Jess"),
        artist="Dave",
        remove_bars=remove_bars,
    )
    return report.cleaned_text


def test_chat_screenshot_is_cleaned_end_to_end():
    cleaned = run_pipeline(RecordingReader(), remove_bars=False)
    assert cleaned == (
        "[name]\n[phone]\nHi [name], still got the Dave tickets?\nYes £85 each, bank transfer only, PayPal is down"
    )


def test_bars_are_cut_off_before_the_model_sees_the_image():
    reader = RecordingReader()
    run_pipeline(reader, remove_bars=True)
    assert reader.image_sizes == [(100, 800)]


def test_step1_result_can_be_handed_on_as_plain_data():
    result = Step1Result(artist="Dave", where_found="WhatsApp", cleaned_text="hello")
    data = result.to_dict()
    assert data["seller_source"] == "not sure"
    assert data["seller_account"] == {"follower_count": None, "account_age_months": None}


def test_website_screenshots_keep_their_top_and_bottom():
    """Wide screenshots have no phone bars, so nothing is cut (a "high demand" banner was lost, 27 Nov 2026)."""
    reader = RecordingReader()
    read_and_clean_screenshot(
        image=Image.new("RGB", (1100, 640)),
        image_fingerprint="wide",
        reader=CachedTextReader(reader),
        name_finder=FakeNameFinder(),
        artist="Dave",
        remove_bars=True,
    )
    assert reader.image_sizes == [(1100, 640)]


def test_listing_words_are_never_removed_as_names():
    from scam_checker.privacy.names import NameSpan, should_keep

    assert should_keep(NameSpan(0, 4, "Sold"), "Noah Kahan")
