from datetime import date

import pytest

from scam_checker.context.artists import load_artist_suggestions, matches_artist
from scam_checker.context.seller import KeywordSourceCategoriser, SellerAccount, SellerSource, months_since

# --- artist -----------------------------------------------------------------


def test_artist_suggestions_load_from_the_data_file():
    assert "Taylor Swift" in load_artist_suggestions()


@pytest.mark.parametrize("candidate", ["Taylor Swift", "taylor swift's", "Taylor Swfit"])
def test_artist_matching_is_forgiving(candidate):
    assert matches_artist(candidate, "Taylor Swift")


def test_first_name_alone_is_not_the_artist():
    assert not matches_artist("Taylor", "Taylor Swift")


def test_a_longer_name_containing_the_artist_is_not_the_artist():
    assert not matches_artist("Dave Smith", "Dave")


# --- seller -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ("A stranger joined an open group-chat link", SellerSource.OPEN_GROUP_CHAT),
        ("A random TikTok comment", SellerSource.RANDOM_COMMENT),
        ("A post from someone I don't know on X", SellerSource.STRANGERS_POST),
        ("they messaged me out of nowhere", SellerSource.STRANGER_MESSAGED_FIRST),
        ("my mate from uni", SellerSource.KNOWN_PERSON),
        ("no idea", SellerSource.UNKNOWN),
        # Screenshot test, 27 Nov 2026: a known person in a private group was read as a stranger.
        ("someone I know from my Whatsapp university netball group chat", SellerSource.KNOWN_PERSON),
        ("Someone I know", SellerSource.KNOWN_PERSON),
        ("A stranger in a group chat", SellerSource.OPEN_GROUP_CHAT),
        ("A stranger in my uni group chat", SellerSource.OPEN_GROUP_CHAT),
        ("An unknown website", SellerSource.MARKETPLACE_OR_SITE),
        ("A random seller account on X replied to my post asking for tickets", SellerSource.RANDOM_COMMENT),
        ("A stranger messaged me first after I commented on a post", SellerSource.STRANGER_MESSAGED_FIRST),
    ],
)
def test_free_text_answer_becomes_a_category(answer, expected):
    assert KeywordSourceCategoriser().categorise(answer) == expected


def test_account_age_from_the_join_date():
    today = date(2026, 11, 27)
    assert months_since(2026, 9, today) == 2
    assert months_since(2024, 3, today) == 32
    # No month: January is assumed, so the account never looks newer than it could be.
    assert months_since(2026, None, today) == 10


def test_not_available_is_shown_as_unknown():
    assert SellerAccount().describe() == ["Followers: unknown", "Account age: unknown"]
