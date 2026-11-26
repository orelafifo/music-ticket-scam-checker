"""Next steps for the user, based on the warning signs found.

Advice follows Take Five (https://www.takefive-stopfraud.org.uk/protect-yourself/ticket-scams/)
and Report Fraud, which replaced Action Fraud in December 2025
(https://www.reportfraud.police.uk, 0300 123 2040).
"""

from __future__ import annotations

from .scoring.scorer import Verdict
from .scoring.step1_signals import Step1Signals

PAY_SAFELY = "Only pay with PayPal Goods and Services or a credit card, so you can get your money back. Never pay into someone else's account."  # noqa: E501
OFFICIAL_TRANSFER = "Ask the seller to transfer the tickets through the official app (Ticketmaster, AXS or DICE) or to list them on Twickets, before you pay."  # noqa: E501
CHECK_DETAILS = "Ask for the date, venue, section and row, and check them against the official event."
AVOID_SITE = "Don't use this website. Buy from the official ticket seller instead, typing its address yourself."
CHECK_SELLER = "Keep the chat where you found the seller, and check their profile: how old the account is, followers and past posts."  # noqa: E501

# Each warning sign (an AI question or a Step 1 signal) and the advice it leads to. Several signs can share one.
ADVICE: dict[str, str] = {
    "bank_transfer": PAY_SAFELY,
    "friends_and_family": PAY_SAFELY,
    "other_unprotected_payment": PAY_SAFELY,
    "someone_elses_account": PAY_SAFELY,
    "pay_first": OFFICIAL_TRANSFER,
    "part_payment": OFFICIAL_TRANSFER,
    "meet_outside_venue": OFFICIAL_TRANSFER,
    "screenshot_as_proof": "Screenshots and photos are easy to fake, so they don't prove the seller has the tickets.",
    "pdf_or_screenshot_ticket": "Many venues won't accept PDF or screenshot tickets. Ask for an official app transfer instead.",  # noqa: E501
    "pressure_to_pay": "Take your time. A genuine seller won't mind you checking first.",
    "asks_for_more_money": "Don't pay any extra fees after agreeing a price. Stop and don't send more money.",
    "very_cheap": "Be wary of tickets far below face value, especially for sold-out shows.",
    "sob_story": "Don't let a personal story rush you into paying.",
    "move_to_private_chat": CHECK_SELLER,
    "no_clear_details": CHECK_DETAILS,
    "refuses_call": "Be wary of a seller who won't talk on the phone or by video.",
    "giveaway": "Real giveaways never ask you to pay a fee.",
    "fake_official": "Ticket companies don't ask you to pay by message. Open their official app or website yourself, and don't use links in messages.",  # noqa: E501
    "seller_source: open_group_chat": CHECK_SELLER,
    "seller_source: stranger_messaged_first": CHECK_SELLER,
    "seller_source: random_comment": CHECK_SELLER,
    "seller_source: strangers_post": CHECK_SELLER,
    "new_account": CHECK_SELLER,
    "few_followers": CHECK_SELLER,
    "event_mismatch": "Check the date and venue on the artist's or venue's official website.",
    "event_not_found": "Check the event exists on the artist's or venue's official website.",
    "before_on_sale": "Tickets can't be resold before they go on general sale. Wait for the official sale.",
    "format_mismatch": "This event uses app tickets only, so a PDF or screenshot ticket won't get you in.",
    "on_blocklist": AVOID_SITE,
    "lookalike_site": AVOID_SITE,
    "new_website": AVOID_SITE,
}
IF_PAID = "If you've already paid, contact your bank straight away, then report it to Report Fraud at reportfraud.police.uk or on 0300 123 2040."  # noqa: E501


def next_steps(answers: dict[str, str], signals: Step1Signals, verdict: Verdict) -> list[str]:
    """Plain next steps, most important first, with no repeats."""
    found = [question for question, answer in answers.items() if answer == "yes"]
    found += [signal.id for signal in signals.found]
    steps: list[str] = []
    for sign in found:
        advice = ADVICE.get(sign)
        if advice and advice not in steps:
            steps.append(advice)
    if answers.get("official_transfer") != "yes" and OFFICIAL_TRANSFER not in steps:
        steps.append(OFFICIAL_TRANSFER)
    if answers.get("protected_payment") != "yes" and PAY_SAFELY not in steps:
        steps.append(PAY_SAFELY)
    if verdict.warning:
        steps.append(IF_PAID)
    return steps
