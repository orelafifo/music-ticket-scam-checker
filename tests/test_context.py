import pytest

from scam_checker.context.artists import load_artist_suggestions, matches_artist
from scam_checker.context.seller import KeywordSourceCategoriser, SellerAccount, SellerSource

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
    ],
)
def test_free_text_answer_becomes_a_category(answer, expected):
    assert KeywordSourceCategoriser().categorise(answer) == expected


def test_not_available_is_shown_as_unknown():
    assert SellerAccount().describe() == ["Followers: unknown", "Account age: unknown"]
