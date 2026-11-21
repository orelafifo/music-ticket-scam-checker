"""Remove personal details that have a clear shape: emails, @handles, phone, bank and card numbers."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass


@dataclass(frozen=True)
class RedactionPattern:
    kind: str
    pattern: re.Pattern
    replacement: str


# Order matters: longer or more specific shapes go first, so an email isn't
# half-removed as an @handle, and a card number isn't read as a phone number.
REDACTION_PATTERNS = [
    # WhatsApp shows a sender who isn't in your contacts as "~ Name" at the start
    # of a line. Whatever follows the "~" is a display name, even an ordinary word
    # like "Me", so it goes: up to a colon, else the whole short line, else one word.
    RedactionPattern(
        "name",
        re.compile(r"^~\s?(?:[^:\n]{1,40}(?=:)|[^:\n]{1,40}$|\S+)", re.MULTILINE),
        "~[name]",
    ),
    # X (Twitter) posts start with a header line: "Display Name @handle · 2h".
    # The "·" after the handle marks it as a header, so a message that merely
    # mentions someone ("DM me @megs_tix") keeps its words.
    RedactionPattern(
        "name",
        re.compile(r"^(?![~\[])[^@\n]{1,40}?(?=\s@[A-Za-z0-9_]{2,30}\s*·)", re.MULTILINE),
        "[name]",
    ),
    RedactionPattern("email", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[email]"),
    # Keep the payment service (a warning sign), remove the person's username.
    RedactionPattern(
        "payment username",
        re.compile(r"\b((?:paypal|monzo|revolut)\.me|venmo\.com|cash\.app)/[\w.$-]+", re.IGNORECASE),
        r"\1/[handle]",
    ),
    RedactionPattern("handle", re.compile(r"(?<![\w@])@[A-Za-z0-9_.]{2,30}"), "[handle]"),
    RedactionPattern("card number", re.compile(r"(?<!\d)\d{4}(?:[ -]?\d{4}){3}(?!\d)"), "[card number]"),
    RedactionPattern(
        "sort code",
        re.compile(r"(?<![\d-])\d{2}-\d{2}-\d{2}(?![\d-])|(?<=sort code )\d{2}\s?\d{2}\s?\d{2}", re.IGNORECASE),
        "[sort code]",
    ),
    # Starts with + (country code) or 0, then 9-12 more digits, spaces allowed.
    RedactionPattern(
        "phone number",
        re.compile(r"(?<![\w+])(?:\+\d{1,3}[\s-]?\d|0\d)(?:[\s-]?\d){8,11}(?!\d)"),
        "[phone]",
    ),
    RedactionPattern("account number", re.compile(r"(?<![\d-])\d{8}(?![\d-])"), "[account number]"),
]


def redact_patterns(text: str) -> tuple[str, Counter]:
    """Replace every pattern match with a placeholder. Returns (text, count per kind)."""
    removed: Counter = Counter()
    for redaction in REDACTION_PATTERNS:
        text, count = redaction.pattern.subn(redaction.replacement, text)
        if count:
            removed[redaction.kind] += count
    return text, removed
