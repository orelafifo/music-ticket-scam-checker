"""Turn the Step 1 answers into points for the scam score.

The points are fixed, not learned: the practice examples don't have Step 1
answers, so the data can't teach them. They were suggested by Claude with a
published source each, and approved by Orela on 23 Nov 2026.
See docs/step2_step1_weights.md for the sources.

Unknown answers ("not sure", N/A, not checked) always give 0 points: unknown is
never suspicious.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..context.seller import SellerSource

if TYPE_CHECKING:
    from ..step1 import Step1Result

HIGH, MEDIUM_HIGH, MEDIUM, LOW = 2.0, 1.5, 1.0, 0.5
OFFICIAL_SITE_POINTS = -1.5

NEW_ACCOUNT_MONTHS = 6
FEW_FOLLOWERS = 50

FILE_TICKET = re.compile(r"\bpdf\b|screenshot of the ticket|print(ed)?[ -]?(out|at home)|email (you )?the ticket", re.I)

SOCIAL_MEDIA = {"WhatsApp", "Instagram", "TikTok", "X (Twitter)", "Facebook (post, group or Marketplace)"}

SELLER_SOURCE_POINTS: dict[SellerSource, tuple[float, str]] = {
    SellerSource.OPEN_GROUP_CHAT: (
        HIGH,
        "The seller is a stranger in a group chat. Scammers join open group chats and advertise tickets straight away.",
    ),
    SellerSource.STRANGER_MESSAGED_FIRST: (HIGH, "A stranger contacted you first with an offer."),
    SellerSource.RANDOM_COMMENT: (MEDIUM_HIGH, "A stranger replied to a post offering tickets."),
    SellerSource.STRANGERS_POST: (MEDIUM, "The tickets are offered in a post by someone you don't know."),
    SellerSource.MARKETPLACE_OR_SITE: (LOW, "The tickets are on a marketplace or website you don't know."),
}

KNOWN_PERSON_TIP = "Check it's really them: friends' accounts are often hacked to sell fake tickets."


@dataclass(frozen=True)
class Signal:
    id: str
    points: float
    reason: str


@dataclass
class Step1Signals:
    found: list[Signal] = field(default_factory=list)
    always_warn: bool = False  # e.g. Google lists the website as dangerous
    tips: list[str] = field(default_factory=list)

    @property
    def total_points(self) -> float:
        return sum(signal.points for signal in self.found)


def step1_signals(result: Step1Result) -> Step1Signals:
    signals = Step1Signals()
    _seller_source(result, signals)
    _where_found(result, signals)
    _seller_account(result, signals)
    _website(result, signals)
    _event(result, signals)
    return signals


def _seller_source(result: Step1Result, signals: Step1Signals) -> None:
    if result.seller_source in SELLER_SOURCE_POINTS:
        points, reason = SELLER_SOURCE_POINTS[result.seller_source]
        signals.found.append(Signal(f"seller_source: {result.seller_source.name.lower()}", points, reason))
    elif result.seller_source is SellerSource.KNOWN_PERSON:
        signals.tips.append(KNOWN_PERSON_TIP)


def _where_found(result: Step1Result, signals: Step1Signals) -> None:
    if result.where_found in SOCIAL_MEDIA:
        signals.found.append(Signal("found_on_social_media", LOW, "Most ticket scams start on social media."))


def _seller_account(result: Step1Result, signals: Step1Signals) -> None:
    account = result.seller_account
    if account.account_age_months is not None and account.account_age_months < NEW_ACCOUNT_MONTHS:
        signals.found.append(Signal("new_account", MEDIUM, "The seller's account is new."))
    if account.follower_count is not None and account.follower_count < FEW_FOLLOWERS:
        signals.found.append(Signal("few_followers", LOW, "The seller's account has very few followers."))


def _website(result: Step1Result, signals: Step1Signals) -> None:
    link = result.link
    if link is None:
        return
    if link.on_blocklist:
        signals.always_warn = True
        signals.found.append(Signal("on_blocklist", HIGH, "Google lists this website as dangerous."))
    if link.imitates:
        signals.found.append(Signal("lookalike_site", HIGH, f"The web address looks like a copy of {link.imitates}."))
    if link.is_new_website:
        signals.found.append(Signal("new_website", HIGH, "This website was set up very recently."))
    if link.is_shortened:
        signals.found.append(
            Signal("shortened_link", MEDIUM, "The link is shortened, which hides where it really goes.")
        )
    if link.is_insecure:
        signals.found.append(Signal("insecure_website", MEDIUM, "The website is not secure (no https)."))
    if link.has_risky_ending:
        signals.found.append(
            Signal("risky_web_ending", MEDIUM, "The web address has an ending often used by scam sites.")
        )
    if link.site_category == "official":
        signals.found.append(Signal("official_site", OFFICIAL_SITE_POINTS, "This is an official ticket site."))


def _event(result: Step1Result, signals: Step1Signals) -> None:
    """Same as v2: a date or venue mismatch, or file tickets for an app-only event, is always a warning."""
    event = result.event
    if event is None:
        return
    if event.mismatch:
        signals.always_warn = True
        official = ", ".join(x for x in (event.official_venue, event.official_date) if x)
        signals.found.append(
            Signal("event_mismatch", HIGH, f"The date or venue doesn't match the official event ({official}).")
        )
    if event.app_only is True and FILE_TICKET.search(result.cleaned_text):
        signals.always_warn = True
        signals.found.append(
            Signal(
                "format_mismatch", HIGH, "This event uses app tickets only, but the seller offers a PDF or screenshot."
            )
        )
    if event.before_on_sale:
        signals.found.append(Signal("before_on_sale", HIGH, "Tickets are offered before the official general sale."))
    if event.found is False:
        signals.found.append(Signal("event_not_found", HIGH, "We couldn't find this event on official listings."))
    if event.high_demand:
        signals.found.append(Signal("high_demand", LOW, "This is a sold-out show, which scammers target."))
