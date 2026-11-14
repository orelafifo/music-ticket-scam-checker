"""Step 1 from start to finish: screenshot in, clean text and context out.

Personal details are removed straight after the text is read, inside one
function, so the raw text is never returned, shown, saved or sent anywhere.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from PIL import Image

from .context.link_check import LinkReport
from .context.seller import SellerAccount, SellerSource
from .privacy.cleaner import CleaningReport, clean_lines
from .privacy.names import NameFinder
from .screenshot.image_prep import shrink_for_reading
from .screenshot.layout import boxes_to_lines, remove_app_bars
from .screenshot.ocr import CachedTextReader

SOURCE_APPS = ["WhatsApp", "Instagram", "TikTok", "X (Twitter)", "Other"]


def read_and_clean_screenshot(
    image: Image.Image,
    image_fingerprint: str,
    reader: CachedTextReader,
    name_finder: NameFinder,
    artist: str,
    remove_bars: bool,
) -> CleaningReport:
    boxes = reader.read(shrink_for_reading(image), image_fingerprint)
    bars_removed = 0
    if remove_bars:
        boxes, bars_removed = remove_app_bars(boxes)
    report = clean_lines(boxes_to_lines(boxes), artist, name_finder)
    if bars_removed:
        report.removed_counts["top or bottom bar text"] += bars_removed
    return report


@dataclass
class Step1Result:
    """Everything Step 2 will receive. Contains no raw screenshot text."""

    artist: str
    source_app: str
    cleaned_text: str
    removed_counts: dict[str, int] = field(default_factory=dict)
    link: LinkReport | None = None
    seller_source_answer: str = ""
    seller_source: SellerSource = SellerSource.UNKNOWN
    seller_account: SellerAccount = field(default_factory=SellerAccount)

    def to_dict(self) -> dict:
        result = asdict(self)
        result["seller_source"] = self.seller_source.value
        return result
