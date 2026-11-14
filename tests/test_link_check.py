"""Website checks. Public-record lookups are faked, so no internet is needed and the link is never opened."""

from scam_checker.context import website_records
from scam_checker.context.link_check import NO_LOOKUPS, WebsiteLookups, check_link


def never_called(domain):
    raise AssertionError("public records should not be looked up for this link")


NEVER_LOOK_UP = WebsiteLookups(never_called, never_called, never_called)


def fake_lookups(domain_age=None, certificate_age=None, on_blocklist=None) -> WebsiteLookups:
    return WebsiteLookups(lambda d: domain_age, lambda d: certificate_age, lambda d: on_blocklist)


def test_official_site_recognised_without_lookups():
    report = check_link("https://www.ticketmaster.co.uk/event/123", NEVER_LOOK_UP)
    assert (report.site_category, report.site_name) == ("official", "Ticketmaster")


def test_lookalike_site_caught():
    report = check_link("ticketrnaster-uk.com/tickets", NO_LOOKUPS)
    assert report.imitates == "Ticketmaster"


def test_shortened_and_insecure_links_flagged():
    report = check_link("http://bit.ly/abc", NEVER_LOOK_UP)
    assert report.is_shortened and report.is_insecure


def test_site_on_googles_blocklist_is_flagged():
    report = check_link("cheap-gig-tickets.com", fake_lookups(on_blocklist=True))
    assert report.on_blocklist
    assert any("Google lists this website" in note for note in report.notes)


def test_new_certificate_marks_an_old_address_as_a_new_website():
    report = check_link("cheap-gig-tickets.com", fake_lookups(domain_age=3000, certificate_age=12))
    assert report.is_new_website


def test_risky_address_ending_noted():
    report = check_link("gig-tickets.shop", NO_LOOKUPS)
    assert report.has_risky_ending


def test_twickets_dot_live_is_not_treated_as_risky():
    report = check_link("https://www.twickets.live/event/1", NEVER_LOOK_UP)
    assert not report.has_risky_ending and report.site_name == "Twickets"


def test_unknown_records_never_count_against_the_website():
    report = check_link("some-gig-tickets.com", fake_lookups())
    assert not report.is_new_website and report.on_blocklist is None


def test_blocklist_is_skipped_without_a_key(monkeypatch):
    monkeypatch.delenv(website_records.SAFE_BROWSING_KEY_SETTING, raising=False)
    assert website_records.lookup_on_blocklist("example.com") is None


def test_only_the_website_address_is_sent_to_google():
    request = website_records._blocklist_request("cheap-gig-tickets.com")
    sent_urls = [entry["url"] for entry in request["threatInfo"]["threatEntries"]]
    assert sent_urls == ["http://cheap-gig-tickets.com/", "https://cheap-gig-tickets.com/"]
