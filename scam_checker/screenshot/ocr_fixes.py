"""Fix OCR misreads that would hide a warning sign from Step 2."""

from __future__ import annotations

import re

# The pound sign is often read as a capital E ("E85" for "£85"). Only fixed
# when E stands alone in front of digits, so ordinary words are untouched.
POUND_READ_AS_E = re.compile(r"(?<![A-Za-z0-9])E(?=\d)")


def fix_common_misreads(line: str) -> str:
    return POUND_READ_AS_E.sub("£", line)
