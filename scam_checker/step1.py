"""Step 1 from start to finish: screenshot in, clean text and context out.

Personal details are removed straight after the text is read, inside one
function, so the raw text is never returned, shown, saved or sent anywhere.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from PIL import Image

from .context.event_check import EventReport
from .context.link_check import LinkReport
from .context.seller import SellerAccount, SellerSource
from .privacy.cleaner import CleaningReport, clean_lines
from .privacy.names import NameFinder
from .screenshot.image_prep import shrink_for_reading, trim_app_bars
from .screenshot.ocr import CachedTextReader


def read_and_clean_screenshot(
    image: Image.Image,
    image_fingerprint: str,
    reader: CachedTextReader,
    name_finder: NameFinder,
    artist: str,
    remove_bars: bool,
) -> CleaningReport:
    if remove_bars:
        image = trim_app_bars(image)
    # Trimmed and untrimmed versions of one screenshot are cached separately.
    screenshot_id = f"{image_fingerprint}-{'trimmed' if remove_bars else 'full'}"
    lines = reader.read(shrink_for_reading(image), screenshot_id)
    report = clean_lines(lines, artist, name_finder)
    if remove_bars:
        report.removed_counts["top and bottom bars"] += 1
    return report


@dataclass
class Step1Result:
    """Everything Step 2 will receive. Contains no raw screenshot text."""

    artist: str
    where_found: str
    cleaned_text: str
    removed_counts: dict[str, int] = field(default_factory=dict)
    link: LinkReport | None = None
    seller_source_answer: str = ""
    seller_source: SellerSource = SellerSource.UNKNOWN
    seller_account: SellerAccount = field(default_factory=SellerAccount)
    event: EventReport | None = None

    def to_dict(self) -> dict:
        result = asdict(self)
        result["seller_source"] = self.seller_source.value
        return result
