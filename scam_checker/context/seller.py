"""What the user knows about the seller: how they met, follower count and account age.

Unknown is never treated as suspicious. Many apps hide follower counts and
account ages, so a missing answer must not count against a genuine seller.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
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


QUICK_PICKS: dict[str, SellerSource] = {
    "A stranger in a group chat": SellerSource.OPEN_GROUP_CHAT,
    "A comment or reply on social media": SellerSource.RANDOM_COMMENT,
    "A post from someone I don't know": SellerSource.STRANGERS_POST,
    "Someone I know": SellerSource.KNOWN_PERSON,
}

EXAMPLE_ANSWERS = [
    "A stranger joined an open group-chat link",
    "A random TikTok comment",
    "A post from someone I don't know on X",
]


class SourceCategoriser(Protocol):
    """Turns the user's own words into a SellerSource. Swappable for the Step 2 AI model."""

    def categorise(self, answer: str) -> SellerSource: ...


# Checked in this order, so the more specific situations win.
_KEYWORD_RULES: list[tuple[SellerSource, str]] = [
    (SellerSource.OPEN_GROUP_CHAT, r"group[ -]?chat|group link|community|discord|telegram group|whatsapp group"),
    (SellerSource.STRANGER_MESSAGED_FIRST, r"messaged me|dm'?d me|slid|reached out|contacted me|out of nowhere"),
    (SellerSource.RANDOM_COMMENT, r"comment|repl(y|ied)|under (a|my|the) (post|video|tweet)"),
    (SellerSource.KNOWN_PERSON, r"\b(friend|mate|cousin|colleague|classmate|sister|brother|know (them|him|her))\b"),
    (SellerSource.MARKETPLACE_OR_SITE, r"marketplace|gumtree|website|site|ebay|viagogo|stubhub|twickets"),
    (SellerSource.STRANGERS_POST, r"post|tweet|story|video|stranger|don'?t know|random"),
]


class KeywordSourceCategoriser:
    """Placeholder until the Step 2 AI model is chosen: matches simple keywords."""

    def categorise(self, answer: str) -> SellerSource:
        text = answer.lower()
        for source, pattern in _KEYWORD_RULES:
            if re.search(pattern, text):
                return source
        return SellerSource.UNKNOWN


@dataclass(frozen=True)
class SellerAccount:
    follower_count: int | None = None  # None = not available
    account_age_months: int | None = None  # None = not available

    def describe(self) -> list[str]:
        followers = "unknown" if self.follower_count is None else f"{self.follower_count:,}"
        age = "unknown" if self.account_age_months is None else f"{self.account_age_months} months"
        return [f"Followers: {followers}", f"Account age: {age}"]
