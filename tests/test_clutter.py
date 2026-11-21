import pytest

from scam_checker.privacy.cleaner import clean_text

from .conftest import FakeNameFinder

NO_NAMES = FakeNameFinder()


def clean(text: str) -> str:
    return clean_text(text, artist="Dave", name_finder=NO_NAMES).cleaned_text


def test_timestamp_removed():
    assert clean("Still got the tickets? 14:32") == "Still got the tickets?"


def test_twelve_hour_timestamp_removed():
    assert clean("yes still available 9:05 pm") == "yes still available"


@pytest.mark.parametrize("line", ["Yesterday", "2h", "3d ago", "Mon", "14/11/2026", "5 minutes ago"])
def test_timestamp_only_lines_removed(line):
    assert clean(f"hello\n{line}\nbye") == "hello\nbye"


@pytest.mark.parametrize("line", ["Reply", "Like", "Seen", "Typing…", "Online", "last seen today at 10:01", "12 likes"])
def test_app_clutter_lines_removed(line):
    assert clean(f"hello\n{line}\nbye") == "hello\nbye"


def test_app_word_at_end_of_comment_removed():
    assert clean("anyone selling? 2d Reply") == "anyone selling?"


def test_ordinary_use_of_like_is_kept():
    assert clean("pay however you'd like") == "pay however you'd like"


def test_prices_are_not_mistaken_for_times():
    assert clean("£12.50 booking fee") == "£12.50 booking fee"


def test_payment_and_platform_words_kept():
    text = "PayPal friends and family or Revolut\nno Ticketmaster transfer, sorry"
    assert clean(text) == text


def test_x_post_header_after_timestamp_removal():
    assert clean("Megan 💜 @megs_tix · 2h\nSelling 2 for Wembley") == "[name] [handle] ·\nSelling 2 for Wembley"


def test_report_counts_removals_without_keeping_values():
    report = clean_text("ring 07123 456789\nSeen", artist="Dave", name_finder=NO_NAMES)
    assert report.removed_counts == {"phone number": 1, "app word": 1}
    assert "07123" not in report.summary()


def test_time_read_with_a_dot_by_ocr_is_removed():
    assert clean("is down. Call me 14.32") == "is down. Call me"


def test_dotted_time_on_its_own_line_is_removed():
    assert clean("hello\n14.32\nbye") == "hello\nbye"


def test_price_at_end_of_line_is_not_mistaken_for_a_time():
    assert clean("selling for £12.50") == "selling for £12.50"


def test_phone_number_followed_by_a_time_does_not_swallow_the_time():
    assert clean("Call 07123 456789 14.32") == "Call [phone]"
