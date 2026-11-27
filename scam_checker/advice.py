"""What to do next, based on the warning signs found and the risk level.

Each step says how to do it, the most important come first, and at most 4 are shown,
followed by a closing line that fits the risk level. Advice follows Take Five
(https://www.takefive-stopfraud.org.uk/protect-yourself/ticket-scams/) and Report Fraud,
which replaced Action Fraud in December 2025 (https://www.reportfraud.police.uk, 0300 123 2040).
"""

from __future__ import annotations

from .scoring.step1_signals import Step1Signals

MAX_STEPS = 4

CHECK_EVENT = "Check the date and venue on the artist's or venue's official website before you go any further."
AVOID_SITE = "Don't buy from this website. Type the official ticket seller's address yourself and buy there instead."
FAKE_OFFICIAL = (
    "Ticket companies don't ask you to pay by message or through a link. Open their official app or website "
    "yourself to check."
)
PAY_SAFELY = (
    "Only pay with PayPal Goods and Services or a credit card, so you can get your money back. "
    "Never pay by bank transfer to a stranger, or into someone else's account."
)
OFFICIAL_TRANSFER = (
    "Ask the seller to transfer the tickets on the official app (Ticketmaster, AXS or DICE) or list them on "
    "Twickets, and wait until the tickets are in your app before you pay."
)
NOT_FILE_TICKETS = (
    "Don't accept a PDF, screenshot or photo of a ticket: they're easy to fake and often won't get you in. "
    "Ask for an app transfer instead."
)
CHECK_SELLER = (
    "Check the seller's profile: a real account usually has an older join date, real photos, past posts and "
    'friends or followers you recognise. Search their name or handle with the word "scam".'
)
NO_RUSH = 'Don\'t let a deadline, a sad story or "other buyers" rush you. A genuine seller will wait while you check.'
CHECK_DETAILS = (
    "Ask for the block, row and seat (or standing), and check they exist for this event on the official site."
)
NO_EXTRA_FEES = "Don't pay any extra fee after agreeing a price. That's a common scam trick."
CALL_THEM = "Ask for a quick video call, and check the seller can show the tickets in their official app."
REAL_GIVEAWAYS = "Real giveaways never ask you to pay a fee or share your bank details."

# Most important first. Each warning sign (an AI question or a Step 1 signal) leads to one piece of advice.
PRIORITY: list[tuple[str, set[str]]] = [
    (CHECK_EVENT, {"event_mismatch", "event_not_found", "before_on_sale"}),
    (AVOID_SITE, {"on_blocklist", "lookalike_site", "new_website", "risky_web_ending"}),
    (FAKE_OFFICIAL, {"fake_official"}),
    (PAY_SAFELY, {"bank_transfer", "friends_and_family", "other_unprotected_payment", "someone_elses_account"}),
    (OFFICIAL_TRANSFER, {"pay_first", "part_payment", "meet_outside_venue"}),
    (NOT_FILE_TICKETS, {"pdf_or_screenshot_ticket", "screenshot_as_proof", "format_mismatch"}),
    (NO_EXTRA_FEES, {"asks_for_more_money"}),
    (NO_RUSH, {"pressure_to_pay", "sob_story", "very_cheap"}),
    (
        CHECK_SELLER,
        {
            "move_to_private_chat",
            "new_account",
            "few_followers",
            "seller_source: open_group_chat",
            "seller_source: stranger_messaged_first",
            "seller_source: random_comment",
        },
    ),
    (CHECK_DETAILS, {"no_clear_details"}),
    (CALL_THEM, {"refuses_call"}),
    (REAL_GIVEAWAYS, {"giveaway"}),
]

CLOSING = {
    "High": (
        "If you're unsure, don't pay. Buy from the official seller or its resale site instead. If you've already "
        "paid, contact your bank straight away and report it to Report Fraud (reportfraud.police.uk, 0300 123 2040)."
    ),
    "Medium": "If anything doesn't add up, don't pay until you've checked the points above.",
    "Low": "This looks OK. Still pay with a protected method, and keep the messages until after the event.",
}


def next_steps(answers: dict[str, str], signals: Step1Signals, risk: str) -> list[str]:
    """Up to 4 steps, most important first. Low risk only gets the basic protections."""
    found = {question for question, answer in answers.items() if answer == "yes"}
    found |= {signal.id for signal in signals.found}
    steps = [advice for advice, signs in PRIORITY if risk != "Low" and found & signs]
    if answers.get("official_transfer") != "yes" and OFFICIAL_TRANSFER not in steps:
        steps.append(OFFICIAL_TRANSFER)
    if answers.get("protected_payment") != "yes" and PAY_SAFELY not in steps:
        steps.append(PAY_SAFELY)
    return steps[:MAX_STEPS]


def closing_line(risk: str) -> str:
    return CLOSING[risk]
