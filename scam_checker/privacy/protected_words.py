"""Words that must survive cleaning, because Step 2 needs them as warning signs or context.

The name finder sometimes mistakes these for people (e.g. it tags "Monzo" and
"Wembley" as person names), so the name remover checks this list first.
"""

from __future__ import annotations

import re

PAYMENT_WORDS = {
    "paypal",
    "revolut",
    "monzo",
    "starling",
    "wise",
    "venmo",
    "cash app",
    "cashapp",
    "zelle",
    "apple pay",
    "google pay",
    "bank transfer",
    "crypto",
    "bitcoin",
    "usdt",
    "gift card",
    "amazon",
    "itunes",
    "steam",
}
PLATFORM_WORDS = {
    "ticketmaster",
    "twickets",
    "axs",
    "see tickets",
    "seetickets",
    "dice",
    "skiddle",
    "eventim",
    "gigantic",
    "viagogo",
    "stubhub",
    "live nation",
    "livenation",
    "whatsapp",
    "telegram",
    "instagram",
    "tiktok",
    "facebook",
    "snapchat",
    "gumtree",
}
# Venues give Step 2 context about the event. Big UK venues only; this is short
# and stable, unlike a list of artists.
VENUE_WORDS = {
    "wembley",
    "o2",
    "the o2",
    "ovo arena",
    "co-op live",
    "ao arena",
    "utilita arena",
    "tottenham hotspur stadium",
    "principality stadium",
    "murrayfield",
    "hampden",
    "etihad",
    "anfield",
    "brixton academy",
    "alexandra palace",
    "ally pally",
    "hyde park",
    "finsbury park",
    "heaton park",
    "emirates stadium",
    "london stadium",
}
PROTECTED_WORDS = PAYMENT_WORDS | PLATFORM_WORDS | VENUE_WORDS

_PROTECTED_PATTERN = re.compile(
    r"\b(" + "|".join(sorted((re.escape(word) for word in PROTECTED_WORDS), key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


def contains_protected_word(text: str) -> bool:
    return bool(_PROTECTED_PATTERN.search(text))
