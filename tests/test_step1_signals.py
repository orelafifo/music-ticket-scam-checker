"""Tests for how Step 1 answers count in the scam score."""

from __future__ import annotations

from scam_checker.context.link_check import LinkReport
from scam_checker.context.seller import SellerAccount, SellerSource
from scam_checker.scoring.scorer import ScoringModel
from scam_checker.scoring.step1_signals import KNOWN_PERSON_TIP, step1_signals
from scam_checker.step1 import Step1Result


def step1(**changes) -> Step1Result:
    values = {"artist": "Oasis", "where_found": "A forum (e.g. Reddit)", "cleaned_text": "2 tickets for sale"}
    values.update(changes)
    return Step1Result(**values)


SIMPLE_MODEL = ScoringModel(["bank_transfer"], {"bank_transfer": 2.0}, intercept=-1.0, warning_level=0.5)


def test_unknown_answers_give_no_points():
    signals = step1_signals(step1(seller_source=SellerSource.UNKNOWN, seller_account=SellerAccount()))
    assert signals.found == [] and signals.total_points == 0 and not signals.always_warn


def test_stranger_in_group_chat_is_riskier_than_someone_you_know():
    stranger = step1_signals(step1(where_found="WhatsApp", seller_source=SellerSource.OPEN_GROUP_CHAT))
    friend = step1_signals(step1(where_found="WhatsApp", seller_source=SellerSource.KNOWN_PERSON))
    assert stranger.total_points > friend.total_points
    assert KNOWN_PERSON_TIP in friend.tips


def test_every_seller_source_is_riskier_than_someone_you_know():
    friend = step1_signals(step1(seller_source=SellerSource.KNOWN_PERSON)).total_points
    for source in SellerSource:
        if source not in (SellerSource.KNOWN_PERSON, SellerSource.UNKNOWN):
            assert step1_signals(step1(seller_source=source)).total_points > friend


def test_new_account_and_few_followers_count_but_na_does_not():
    new = step1_signals(step1(seller_account=SellerAccount(follower_count=12, account_age_months=2)))
    assert {s.id for s in new.found} == {"new_account", "few_followers"}
    older = step1_signals(step1(seller_account=SellerAccount(follower_count=5000, account_age_months=48)))
    assert older.found == []


def test_dangerous_website_always_warns():
    link = LinkReport(domain="tickets-oasis.shop", on_blocklist=True)
    verdict = SIMPLE_MODEL.verdict({"bank_transfer": "no"}, step1_signals(step1(where_found="A website", link=link)))
    assert verdict.warning
    assert verdict.reasons[0] == "Google lists this website as dangerous."


def test_official_site_lowers_the_score():
    official = LinkReport(domain="ticketmaster.co.uk", site_category="official")
    with_site = SIMPLE_MODEL.scam_probability({"bank_transfer": "yes"}, step1_signals(step1(link=official)))
    without = SIMPLE_MODEL.scam_probability({"bank_transfer": "yes"})
    assert with_site < without


def test_step1_reasons_are_shown_with_ai_reasons_strongest_first():
    signals = step1_signals(step1(where_found="WhatsApp", seller_source=SellerSource.OPEN_GROUP_CHAT))
    model = ScoringModel(["bank_transfer"], {"bank_transfer": 1.0}, intercept=-1.0, warning_level=0.5)
    verdict = model.verdict({"bank_transfer": "yes"}, signals)  # group chat (2 points) beats bank transfer (1)
    assert verdict.warning
    assert verdict.reasons[0].startswith("The seller is a stranger in a group chat")
    assert any(reason.startswith("The seller wants a bank transfer") for reason in verdict.reasons)
    assert "Most ticket scams start on social media." in verdict.reasons


def test_event_mismatch_always_warns():
    from scam_checker.context.event_check import EventReport

    event = EventReport("Oasis", "Wembley", "2027-07-04", found=True, details_match=False, official_venue="Wembley")
    verdict = SIMPLE_MODEL.verdict({"bank_transfer": "no"}, step1_signals(step1(event=event)))
    assert verdict.warning
    assert verdict.reasons[0].startswith("The date or venue doesn't match")


def test_pdf_ticket_for_app_only_event_always_warns():
    from scam_checker.context.event_check import EventReport

    event = EventReport("Oasis", found=True, details_match=True, app_only=True)
    signals = step1_signals(step1(event=event, cleaned_text="Will send the PDF once paid"))
    assert signals.always_warn


def test_event_not_checked_adds_nothing():
    from scam_checker.context.event_check import EventReport

    signals = step1_signals(step1(event=EventReport("Tiny Local Band", notes=["Event not checked."])))
    assert signals.found == [] and not signals.always_warn


def test_selling_before_general_sale_adds_high_points():
    from scam_checker.context.event_check import EventReport

    event = EventReport("Oasis", found=True, details_match=True, before_on_sale=True)
    assert step1_signals(step1(event=event)).total_points == 2.0
