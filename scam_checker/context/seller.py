"""What the user knows about the seller: how they met, follower count and account age.

Unknown is never treated as suspicious. Many apps hide follower counts and
account ages, so a missing answer must not count against a genuine seller.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Protocol


class SellerSource(str, Enum):
    OPEN_GROUP_CHAT = "stranger in an open group chat"
    RANDOM_COMMENT = "stranger replying to a comment or post"
    STRANGERS_POST = "post from someone you don't know"
    STRANGER_MESSAGED_FIRST = "stranger messaged you first"
    KNOWN_PERSON = "someone you know (their account could be hacked)"
    MARKETPLACE_OR_SITE = "marketplace or website listing"
    UNKNOWN = "not sure"


EXAMPLE_ANSWERS = [
    "An unknown website",
    "A random seller account on X replied to my post asking for tickets",
]
ANSWER_TIP = "Say if they're a stranger or someone you know, and where: private chat, open group or public post."


class SourceCategoriser(Protocol):
    """Turns the user's own words into a SellerSource. Swappable for the Step 2 AI model."""

    def categorise(self, answer: str) -> SellerSource: ...


STRANGER = re.compile(
    r"stranger|don'?t know|didn'?t know|random|unknown|anyone can join|open (group|chat|link)|group link|"
    r"invite link|public group|joined (the|a|an|via|through)",
    re.IGNORECASE,
)
KNOWN = re.compile(
    r"someone i know|people i know|i know (them|him|her)|\bknow (them|him|her)\b|"
    r"\b(friend|mate|cousin|colleague|classmate|flatmate|housemate|teammate|sister|brother|family)s?\b|"
    r"private (group|chat)|\bmy (uni|university|work|school|college|team|class|netball|football|family)\b.*group",
    re.IGNORECASE,
)
# Checked in this order, so the more specific situations win. Knowing the seller is checked
# first, so "someone I know from my uni group chat" isn't read as a stranger in an open group.
_KEYWORD_RULES: list[tuple[SellerSource, str]] = [
    (SellerSource.OPEN_GROUP_CHAT, r"group[ -]?chat|group link|community|discord|telegram group|whatsapp group"),
    (SellerSource.STRANGER_MESSAGED_FIRST, r"messaged me|dm'?d me|slid|reached out|contacted me|out of nowhere"),
    (SellerSource.RANDOM_COMMENT, r"comment|repl(y|ied)|under (a|my|the) (post|video|tweet)"),
    (SellerSource.MARKETPLACE_OR_SITE, r"marketplace|gumtree|website|site|ebay|viagogo|stubhub|twickets"),
    (SellerSource.STRANGERS_POST, r"post|tweet|story|video|stranger|don'?t know|random"),
]


class KeywordSourceCategoriser:
    """Matches simple keywords in the user's own description of how they met the seller."""

    def categorise(self, answer: str) -> SellerSource:
        text = answer.lower()
        if KNOWN.search(text) and not STRANGER.search(text):
            return SellerSource.KNOWN_PERSON
        for source, pattern in _KEYWORD_RULES:
            if re.search(pattern, text):
                return source
        return SellerSource.UNKNOWN


def months_since(year: int, month: int | None, today: date) -> int:
    """Account age in months from the join date apps show ("Joined March 2024").

    With no month, January is assumed: the oldest the account could be, so an unknown
    month never makes an account look newer than it is.
    """
    return max(0, (today.year - year) * 12 + today.month - (month or 1))


@dataclass(frozen=True)
class SellerAccount:
    follower_count: int | None = None  # None = not available
    account_age_months: int | None = None  # None = not available

    def describe(self) -> list[str]:
        followers = "unknown" if self.follower_count is None else f"{self.follower_count:,}"
        age = "unknown" if self.account_age_months is None else f"{self.account_age_months} months"
        return [f"Followers: {followers}", f"Account age: {age}"]
