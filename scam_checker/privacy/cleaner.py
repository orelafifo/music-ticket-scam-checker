"""Run every cleaning stage in order and report what was removed.

The report only counts removals by kind ("2 phone numbers"); it never keeps
the removed values, so it is safe to show and to save as evidence.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from . import clutter
from .names import NameFinder, redact_names
from .patterns import redact_patterns


@dataclass
class CleaningReport:
    cleaned_text: str
    removed_counts: Counter = field(default_factory=Counter)

    def summary(self) -> str:
        if not self.removed_counts:
            return "Nothing needed removing."
        parts = [f"{count} × {kind}" for kind, count in self.removed_counts.most_common()]
        return "Removed: " + ", ".join(parts)


def clean_lines(lines: list[str], artist: str, name_finder: NameFinder) -> CleaningReport:
    """Clean text line by line (lines keep the chat's shape), then remove names."""
    removed: Counter = Counter()
    kept_lines = [line for line in (_clean_one_line(line, removed) for line in lines) if line]
    text, pattern_counts = redact_patterns("\n".join(kept_lines))
    removed.update(pattern_counts)
    text, redacted = redact_names(text, artist, name_finder)
    removed.update(redacted)
    return CleaningReport(text, removed)


def clean_text(text: str, artist: str, name_finder: NameFinder) -> CleaningReport:
    return clean_lines(text.splitlines(), artist, name_finder)


def _clean_one_line(line: str, removed: Counter) -> str:
    """Returns the cleaned line, or "" if the whole line should go."""
    if clutter.is_timestamp_line(line):
        removed["timestamp"] += 1
        return ""
    line, time_count = clutter.remove_clock_times(line)
    if time_count:
        removed["timestamp"] += time_count
    line, trailing_count = clutter.strip_trailing_app_words(line)
    if trailing_count:
        removed["app word"] += trailing_count
    if clutter.is_app_clutter_line(line):
        removed["app word"] += 1
        return ""
    return line
