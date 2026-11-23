"""The fixed yes/no questions the AI answers about each listing (Step 2).

Each question is either a red flag (a "yes" points towards a scam) or a good
sign (a "yes" points towards a genuine sale). The scoring step learns how much
each one matters, but it is told this direction so it can warn if the data
disagrees.

This is the starting list of 6. It will be extended, with a source for each
question, before any AI model is tested.
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
        text="Does the seller ask for payment by bank transfer?",
        reason="The seller wants a bank transfer, which gives you no protection if the tickets never arrive.",
        direction=Direction.RED_FLAG,
    ),
    Question(
        id="pay_first",
        text="Does the seller want the money before the tickets are sent?",
        reason="The seller wants paying before you get the tickets.",
        direction=Direction.RED_FLAG,
    ),
    Question(
        id="sob_story",
        text="Does the seller give a sad or personal reason for selling (illness, break-up, family problem)?",
        reason="The seller gives a sad story, which scammers often use to make you trust them.",
        direction=Direction.RED_FLAG,
    ),
    Question(
        id="move_to_private_chat",
        text="Does the seller ask you to message them privately (DM, PM, inbox, WhatsApp)?",
        reason="The seller wants to move to a private chat, away from where others could warn you.",
        direction=Direction.RED_FLAG,
    ),
    Question(
        id="price_given",
        text="Is a price for the tickets given in the listing?",
        reason="A price is given openly.",
        direction=Direction.GOOD_SIGN,
    ),
    Question(
        id="official_transfer",
        text=(
            "Does the seller offer to sell or transfer through an official site or app"
            " (e.g. Ticketmaster, Twickets, AXS, DICE)?"
        ),
        reason="The seller offers an official ticket transfer, which protects you.",
        direction=Direction.GOOD_SIGN,
    ),
)

QUESTION_IDS: tuple[str, ...] = tuple(question.id for question in QUESTIONS)
ANSWERS = ("yes", "no", "unclear")


def find_question(question_id: str) -> Question:
    for question in QUESTIONS:
        if question.id == question_id:
            return question
    raise KeyError(f"Unknown question: {question_id}")
