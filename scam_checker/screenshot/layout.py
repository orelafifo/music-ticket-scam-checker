"""Use where text sits on the screen to drop app furniture before reading it as words."""

from __future__ import annotations

from .ocr import TextBox, group_into_lines, row_text
from .ocr_fixes import fix_common_misreads

# In chat apps the top bar holds the other person's name, number and photo,
# and the bottom bar holds the "Type a message" box. These shares cover both
# on common phones; they are only used for chat screenshots that weren't cropped.
TOP_BAR_SHARE = 0.12
BOTTOM_BAR_SHARE = 0.08


def remove_app_bars(
    boxes: list[TextBox],
    top_share: float = TOP_BAR_SHARE,
    bottom_share: float = BOTTOM_BAR_SHARE,
) -> tuple[list[TextBox], int]:
    """Drop boxes inside the top and bottom bars. Returns (kept boxes, number removed)."""
    kept = [box for box in boxes if top_share <= box.middle <= 1 - bottom_share]
    return kept, len(boxes) - len(kept)


def boxes_to_lines(boxes: list[TextBox]) -> list[str]:
    lines = (fix_common_misreads(row_text(row)) for row in group_into_lines(boxes))
    return [line for line in lines if line]
