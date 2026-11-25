"""The fixed yes/no questions the AI answers about each listing (Step 2).

Each question is either a red flag (a "yes" points towards a scam) or a good
sign (a "yes" points towards a genuine sale). The scoring step learns how much
each one matters, but it is told this direction so it can warn if the data
disagrees.

22 questions (18 red flags, 4 good signs), each with a source. Approved by Orela
on 23 Nov 2026; clearer wording, clear_details and fake_official added 24 Nov 2026 (prompt
version 2, Step 2 context engineering). See docs/step2_questions.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Direction(Enum):
    RED_FLAG = "red flag"
    GOOD_SIGN = "good sign"


@dataclass(frozen=True)
class Question:
    id: str
    text: str  # what the AI is asked
    reason: str  # what the user is shown when the answer is "yes"
    direction: Direction
    source: str = ""  # where the warning sign comes from (added in the next step)


QUESTIONS: tuple[Question, ...] = (
    Question(
        id="bank_transfer",
        text=(
            "Does the seller ask for payment by bank transfer? No if bank transfer is only offered as an option "
            "next to an official transfer or a protected payment."
        ),
        reason="The seller wants a bank transfer, which gives you no protection if the tickets never arrive.",
        direction=Direction.RED_FLAG,
        source="Take Five: https://www.takefive-stopfraud.org.uk/protect-yourself/ticket-scams/",
    ),
    Question(
        id="friends_and_family",
        text='Does the seller ask for PayPal "Friends and Family"?',
        reason='The seller wants PayPal "Friends and Family", which has no buyer protection.',
        direction=Direction.RED_FLAG,
        source="PayPal UK: https://paypal.com/uk/security/learn-about-scams",
    ),
    Question(
        id="other_unprotected_payment",
        text=(
            "Does the seller ask for another payment with no protection (gift cards, crypto, Western Union, cash sent "
            "in advance)? Not bank transfer: that is a separate question."
        ),
        reason="The seller wants a payment that can't be refunded (gift cards, crypto, money transfer or cash).",
        direction=Direction.RED_FLAG,
        source="Aura (US, weaker): https://aura.com/learn/ticketmaster-scams",
    ),
    Question(
        id="pay_first",
        text="Does the seller want the money before the tickets are sent?",
        reason="The seller wants paying before you get the tickets.",
        direction=Direction.RED_FLAG,
        source="Get Safe Online via Croydon Council: https://news.croydon.gov.uk/trading-standards-advise-residents-not-to-fall-victim-to-ticket-scams-during-uefa-euro-2024",  # noqa: E501
    ),
    Question(
        id="part_payment",
        text=(
            "Does the seller ask you to pay part of the money first (a deposit, half now, instalments)? "
            "The seller mentioning a deposit they paid themselves is no."
        ),
        reason="The seller asks for a deposit or part of the money first.",
        direction=Direction.RED_FLAG,
        source="MoneySavingExpert: https://blog.moneysavingexpert.com/news/2020/03/paypal-scam-victims-warn-against-fraudsters-who-ask-for--family-",  # noqa: E501
    ),
    Question(
        id="someone_elses_account",
        text=(
            "Does the seller ask you to pay into someone else's account (a friend, partner, relative,"
            " colleague), or say the name won't match?"
        ),
        reason="The seller wants the money sent to someone else's account.",
        direction=Direction.RED_FLAG,
        source="Leicestershire Police 2025: https://www.leics.police.uk/news/leicestershire/news/2025/april/warning-to-people-buying-concert-tickets-via-social-media/",  # noqa: E501
    ),
    Question(
        id="asks_for_more_money",
        text="After agreeing a price, does the seller ask for more money (a fee, name change, delivery)?",
        reason="The seller asks for extra money after the price was agreed.",
        direction=Direction.RED_FLAG,
        source="Hackettstown Police via CBS (US, weaker): https://cbsnews.com/newyork/news/taylor-swift-ticket-scam-new-jersey",  # noqa: E501
    ),
    Question(
        id="pressure_to_pay",
        text=(
            "Does the seller urge you to pay quickly (others interested, today only, quick sale)? "
            "Asking for offers is no."
        ),
        reason="The seller is rushing you to pay.",
        direction=Direction.RED_FLAG,
        source="Take Five; Lloyds Bank: https://www.lloydsbank.com/help-guidance/protecting-yourself-from-fraud/ticket-scams.html",  # noqa: E501
    ),
    Question(
        id="very_cheap",
        text=(
            "Is the price unrealistically cheap (for example less than half of face value)? "
            "A small discount, or selling at or just below face value, is no."
        ),
        reason="The tickets are much cheaper than usual, which is too good to be true.",
        direction=Direction.RED_FLAG,
        source="Take Five: https://www.takefive-stopfraud.org.uk/protect-yourself/ticket-scams/",
    ),
    Question(
        id="sob_story",
        text=(
            "Does the seller give a personal story or reason for selling (illness, family, a baby, exams, work, "
            "money problems)? Just 'can't go any more' or 'no longer available' with no story is no."
        ),
        reason="The seller gives a personal story, which scammers often use to make you trust them.",
        direction=Direction.RED_FLAG,
        source="North West Regional Organised Crime Unit: https://www.rocu.police.uk/syssiteassets2/media/images/news/nwrocu/nwrocu_lbobs_5th-edition_rgb_2025-online.pdf",  # noqa: E501
    ),
    Question(
        id="move_to_private_chat",
        text=("Does the seller ask you to message them privately (DM, PM, inbox, email) or move to WhatsApp?"),
        reason="The seller wants to move to a private chat, away from where others could warn you.",
        direction=Direction.RED_FLAG,
        source="Lloyds Bank 2026: https://www.lloydsbank.com/media-centre/2026/football-fans-urged-to-show-fraudsters-the-red-card.html",  # noqa: E501
    ),
    Question(
        id="screenshot_as_proof",
        text=(
            "Does the seller offer a screenshot or photo as proof that they have the tickets? "
            "Only when it is offered as proof, not as the ticket itself."
        ),
        reason="The seller offers a screenshot as proof, which is easy to fake.",
        direction=Direction.RED_FLAG,
        source="An Post: https://www.anpost.com/Money/Managing-Finances/Blog/How-To-Spot-Concert-Ticket-Scams",
    ),
    Question(
        id="pdf_or_screenshot_ticket",
        text=(
            "Does the seller offer the ticket itself as a PDF, screenshot or printout? "
            "Posting paper tickets, or an official e-ticket or app transfer, is no."
        ),
        reason="The ticket is offered as a PDF or screenshot, which many venues won't accept.",
        direction=Direction.RED_FLAG,
        source="Ticketmaster: https://help.ticketmaster.com/hc/en-us/articles/9611493057425-Can-I-print-my-mobile-ticket-and-take-the-paper-ticket-to-get-in",  # noqa: E501
    ),
    Question(
        id="no_clear_details",
        text="Does the seller avoid giving clear details (date, venue, seats, booking confirmation)?",
        reason="The seller doesn't give clear ticket details.",
        direction=Direction.RED_FLAG,
        source="Take Five: https://www.takefive-stopfraud.org.uk/protect-yourself/ticket-scams/",
    ),
    Question(
        id="meet_outside_venue",
        text="Does the seller suggest meeting outside the venue to hand over the tickets?",
        reason="The seller wants to hand the tickets over outside the venue.",
        direction=Direction.RED_FLAG,
        source="Take Five: https://www.takefive-stopfraud.org.uk/protect-yourself/ticket-scams/",
    ),
    Question(
        id="refuses_call",
        text="Does the seller refuse a phone or video call?",
        reason="The seller won't talk on the phone or by video.",
        direction=Direction.RED_FLAG,
        source="Refundee (commercial, weaker): https://www.refundee.com/blog/ticket-scams-uk",
    ),
    Question(
        id="giveaway",
        text="Is it a giveaway or competition asking you to like, share, comment or pay a fee?",
        reason="It's a giveaway or competition, which scammers often fake.",
        direction=Direction.RED_FLAG,
        source="Which?: https://www.which.co.uk/news/article/five-tips-to-avoid-tickets-scams-and-dud-deals-aDALz5M722Ld",  # noqa: E501
    ),
    Question(
        id="fake_official",
        text=(
            "Does the message claim to be from a ticket company or resale team (e.g. Ticketmaster, Twickets) "
            "and ask you to pay or confirm through a link, a message or a bank transfer?"
        ),
        reason="The message claims to be from a ticket company but asks you to pay outside its official app or website.",  # noqa: E501
        direction=Direction.RED_FLAG,
        source=(
            "Twickets founder via PA/STV (2025): fake Twickets accounts and websites set up to trick fans. "
            "https://news.stv.tv/world/music-fans-urged-to-be-wary-of-last-minute-glastonbury-and-oasis-offers"
        ),
    ),
    Question(
        id="official_transfer",
        text=(
            "Does the seller offer to sell or transfer through an official site or app? Yes if they offer to "
            "transfer through Ticketmaster, AXS, DICE, See Tickets, Twickets, or the venue's or festival's own resale. "
            "A message that claims to BE a ticket company is not this (see fake_official)."
        ),
        reason="The seller offers an official ticket transfer, which protects you.",
        direction=Direction.GOOD_SIGN,
        source="Take Five: https://www.takefive-stopfraud.org.uk/protect-yourself/ticket-scams/",
    ),
    Question(
        id="protected_payment",
        text=(
            "Does the seller offer a protected way to pay (PayPal Goods and Services, or card)? "
            "Just 'PayPal' with no detail is unclear."
        ),
        reason="The seller offers a payment method with buyer protection.",
        direction=Direction.GOOD_SIGN,
        source="PayPal UK: https://paypal.com/uk/security/learn-about-scams",
    ),
    Question(
        id="price_given",
        text="Is a price for the tickets given in the listing?",
        reason="A price is given openly.",
        direction=Direction.GOOD_SIGN,
        source="Linked to Take Five's clear details sign (judgement call): https://www.takefive-stopfraud.org.uk/protect-yourself/ticket-scams/",  # noqa: E501
    ),
    Question(
        id="clear_details",
        text="Does the seller give specific ticket details (date, venue, section, row or seat)?",
        reason="The seller gives specific ticket details.",
        direction=Direction.GOOD_SIGN,
        source="Take Five (clear booking details, seat information): https://www.takefive-stopfraud.org.uk/protect-yourself/ticket-scams/",  # noqa: E501
    ),
)

QUESTION_IDS: tuple[str, ...] = tuple(question.id for question in QUESTIONS)
ANSWERS = ("yes", "no", "unclear")


def find_question(question_id: str) -> Question:
    for question in QUESTIONS:
        if question.id == question_id:
            return question
    raise KeyError(f"Unknown question: {question_id}")


def questions_answered(columns) -> tuple[Question, ...]:
    """The questions present in a saved answers file (prompt version 1 files have 20, version 2 have 21)."""
    return tuple(question for question in QUESTIONS if question.id in set(columns))
