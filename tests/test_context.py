import pytest

from scam_checker.context.artists import load_artist_suggestions, matches_artist
from scam_checker.context.link_check import check_link
from scam_checker.context.seller import KeywordSourceCategoriser, SellerAccount, SellerSource


def never_called(domain):
    raise AssertionError("the age lookup should not run for this link")


# --- artist -----------------------------------------------------------------


def test_artist_suggestions_load_from_the_data_file():
    assert "Taylor Swift" in load_artist_suggestions()


@pytest.mark.parametrize("candidate", ["Taylor Swift", "taylor swift's", "Taylor Swfit"])
def test_artist_matching_is_forgiving(candidate):
    assert matches_artist(candidate, "Taylor Swift")


def test_first_name_alone_is_not_the_artist():
    assert not matches_artist("Taylor", "Taylor Swift")


# --- link check (the link is never opened) ----------------------------------


def test_official_site_recognised():
    report = check_link("https://www.ticketmaster.co.uk/event/123", lookup_age=never_called)
    assert (report.site_category, report.site_name) == ("official", "Ticketmaster")


def test_lookalike_site_caught_and_age_checked():
    report = check_link("ticketrnaster-uk.com/tickets", lookup_age=lambda domain: 12)
    assert report.imitates == "Ticketmaster"
    assert report.is_new_website


def test_shortened_and_insecure_links_flagged():
    report = check_link("http://bit.ly/abc", lookup_age=never_called)
    assert report.is_shortened and report.is_insecure


def test_unknown_age_is_not_treated_as_new():
    report = check_link("some-gig-tickets.com", lookup_age=lambda domain: None)
    assert not report.is_new_website


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
