"""Create the before-and-after removal example for the report's privacy section.

Uses the made-up screenshot in examples/, so it's safe to show the "before" text.
Run:  python scripts/make_redaction_example.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scam_checker.privacy.names import SpacyNameFinder  # noqa: E402
from scam_checker.screenshot.image_prep import fingerprint, open_image, shrink_for_reading  # noqa: E402
from scam_checker.screenshot.layout import boxes_to_lines  # noqa: E402
from scam_checker.screenshot.ocr import CachedTextReader, EasyOcrReader  # noqa: E402
from scam_checker.step1 import read_and_clean_screenshot  # noqa: E402

SCREENSHOT = PROJECT_ROOT / "examples" / "fake_whatsapp_chat.png"
OUTPUT_FILE = PROJECT_ROOT / "docs" / "redaction_example.md"
ARTIST = "Dave"


def main() -> None:
    image_bytes = SCREENSHOT.read_bytes()
    image, screenshot_id = open_image(image_bytes), fingerprint(image_bytes)
    reader = CachedTextReader(EasyOcrReader())
    # Read exactly what the pipeline reads, so the cached result is shared.
    before = "\n".join(boxes_to_lines(reader.read(shrink_for_reading(image), screenshot_id)))
    report = read_and_clean_screenshot(image, screenshot_id, reader, SpacyNameFinder(), ARTIST, remove_bars=True)
    OUTPUT_FILE.write_text(build_markdown(before, report.cleaned_text, report.summary()), encoding="utf-8")
    print(f"Saved {OUTPUT_FILE}")


def build_markdown(before: str, after: str, summary: str) -> str:
    return "\n".join(
        [
            "# Personal-detail removal: before and after",
            "",
            f"Generated {date.today():%d %B %Y} from `examples/fake_whatsapp_chat.png` (all details invented).",
            f"Artist entered by the user: **{ARTIST}**.",
            "",
            "## Before: what OCR read",
            "",
            "```",
            before,
            "```",
            "",
            "## After: what Step 2 receives",
            "",
            "```",
            after,
            "```",
            "",
            f"**{summary}**",
            "",
            "The report counts what was removed but never keeps the removed values.",
            "",
        ]
    )


if __name__ == "__main__":
    main()
