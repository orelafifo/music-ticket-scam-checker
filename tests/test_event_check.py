"""Tests for the event check, with made-up official events (no internet needed)."""

from __future__ import annotations

from datetime import date

from scam_checker.context.event_check import OfficialEvent, check_event, venue_matches
from scam_checker.context.event_details import read_event_details

TODAY = date(2026, 11, 23)
TOUR = [
    OfficialEvent(date(2027, 4, 9), "The O2", on_sale=date(2026, 10, 1), status="onsale", app_only=True),
    OfficialEvent(date(2027, 4, 10), "The O2", on_sale=date(2026, 10, 1), status="offsale", high_demand=True),
    OfficialEvent(date(2027, 6, 20), "Co-op Live", on_sale=date(2026, 12, 5), status="onsale"),
]


def fake_source(events):
    return {"Fake": lambda artist, event_date: events}


def test_matching_event():
    report = check_event("Olivia Rodrigo", "O2 Arena", date(2027, 4, 9), TODAY, fake_source(TOUR))
    assert report.found and report.details_match and not report.mismatch
    assert report.app_only is True


def test_wrong_date_is_a_mismatch():
    report = check_event("Olivia Rodrigo", "The O2", date(2027, 4, 12), TODAY, fake_source(TOUR))
    assert report.mismatch
    assert report.official_venue == "The O2"


def test_selling_before_general_sale():
    report = check_event("Olivia Rodrigo", "Co-op Live", date(2027, 6, 20), TODAY, fake_source(TOUR))
    assert report.details_match and report.before_on_sale


def test_sold_out_show_is_high_demand():
    report = check_event("Olivia Rodrigo", "The O2", date(2027, 4, 10), TODAY, fake_source(TOUR))
    assert report.high_demand


def test_no_sources_means_not_checked():
    report = check_event("Olivia Rodrigo", "The O2", date(2027, 4, 9), TODAY, sources={})
    assert report.found is None and not report.mismatch
    assert "Event not checked." in report.notes


def test_nothing_found_means_not_checked_not_suspicious():
    report = check_event("Tiny Local Band", "", None, TODAY, fake_source([]))
    assert report.found is None and not report.mismatch


def test_a_failed_lookup_never_crashes():
    def broken(artist, event_date):
        raise ConnectionError

    report = check_event("Olivia Rodrigo", "The O2", None, TODAY, {"Broken": broken})
    assert report.found is None
    assert any("lookup failed" in note for note in report.notes)


def test_venue_names_match_loosely():
    assert venue_matches("O2 Arena", "The O2")
    assert not venue_matches("Wembley Stadium", "Co-op Live")


def test_reads_venue_and_date_from_listing():
    text = "Selling 3x Olivia Rodrigo tickets @ The O2 Arena, London on Friday 9th April 2027. DM me"
    details = read_event_details(text, TODAY)
    assert details.venue == "The O2"
    assert details.event_date == date(2027, 4, 9)


def test_date_without_year_means_the_next_one():
    assert read_event_details("2 tickets Wembley Stadium 21st June", TODAY).event_date == date(2027, 6, 21)


def test_nothing_to_read():
    details = read_event_details("spare ticket for tonight, dm", TODAY)
    assert details.venue == "" and details.event_date is None


def test_venue_split_over_two_lines_from_a_screenshot():
    text = (
        "Hey guys... would anyone be\ninterested in Olivia Rodrigo at The\nO2, Greater London, United Kingdom\n"
        "on April 9/2027? I'm looking to\nsell mine"
    )
    details = read_event_details(text, TODAY)
    assert details.venue == "The O2"
    assert details.event_date == date(2027, 4, 9)


def test_many_ways_of_writing_a_date():
    april_9 = date(2027, 4, 9)
    for written in [
        "9 April 2027", "9th April 2027", "9th of April 27", "9 Apr '27", "Fri 9th April", "9-Apr-27",
        "April 9 2027", "April 9th, 2027", "April 9/2027", "Apr 9/27", "April 9th 27", "april 9",
        "9/4/2027", "09/04/27", "9.4.27", "9-4-2027", "9/4", "2027-04-09",
    ]:  # fmt: skip
        assert read_event_details(f"2 tickets for {written}, The O2", TODAY).event_date == april_9, written


def test_prices_and_counts_are_not_read_as_dates():
    assert read_event_details("2 tickets £85.50 each, 15 people interested", TODAY).event_date is None
    assert read_event_details("Selling 2 tickets for 9 April, 15 tickets left", TODAY).event_date == date(2027, 4, 9)
