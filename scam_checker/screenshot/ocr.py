"""Read text from an image with a local OCR model (nothing is sent online).

OCR = optical character recognition: turning the pixels of text into text.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Protocol

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class TextBox:
    """One piece of text found by OCR. Positions are shares of the image (0 = top/left, 1 = bottom/right)."""

    text: str
    top: float
    bottom: float
    left: float

    @property
    def middle(self) -> float:
        return (self.top + self.bottom) / 2

    @property
    def height(self) -> float:
        return self.bottom - self.top


class TextReader(Protocol):
    """Anything that can turn an image into text boxes. Lets tests use a fake reader."""

    def read(self, image: Image.Image) -> list[TextBox]: ...


class EasyOcrReader:
    """Reads text with EasyOCR, running on this computer's processor."""

    def __init__(self, languages: tuple[str, ...] = ("en",)):
        self._languages = list(languages)
        self._model = None

    def read(self, image: Image.Image) -> list[TextBox]:
        raw_results = self._load_model().readtext(np.array(image))
        return [_to_text_box(corners, text, image.size) for corners, text, _confidence in raw_results]

    def _load_model(self):
        # Imported and loaded on first use: the model is large and slow to start.
        if self._model is None:
            import easyocr

            self._model = easyocr.Reader(self._languages, gpu=False, verbose=False)
        return self._model


def _to_text_box(corners, text: str, image_size: tuple[int, int]) -> TextBox:
    width, height = image_size
    ys = [point[1] for point in corners]
    xs = [point[0] for point in corners]
    return TextBox(text=text, top=min(ys) / height, bottom=max(ys) / height, left=min(xs) / width)


class CachedTextReader:
    """Remembers results by screenshot fingerprint, so the same screenshot is only read once.

    Create one per user session: the cache holds the screenshot's text before
    personal details are removed, so it must never be shared between users.
    """

    def __init__(self, reader: TextReader):
        self._reader = reader
        self._results: dict[str, list[TextBox]] = {}

    def read(self, image: Image.Image, image_fingerprint: str) -> list[TextBox]:
        if image_fingerprint not in self._results:
            self._results = {image_fingerprint: self._reader.read(image)}  # keep only the latest
        return self._results[image_fingerprint]

    def forget(self) -> None:
        self._results.clear()


def group_into_lines(boxes: list[TextBox]) -> list[list[TextBox]]:
    """Group boxes that sit on the same row, top to bottom, each row left to right."""
    if not boxes:
        return []
    row_tolerance = median(box.height for box in boxes) / 2
    rows: list[list[TextBox]] = []
    for box in sorted(boxes, key=lambda b: b.middle):
        if rows and abs(rows[-1][0].middle - box.middle) <= row_tolerance:
            rows[-1].append(box)
        else:
            rows.append([box])
    return [sorted(row, key=lambda b: b.left) for row in rows]


def row_text(row: list[TextBox]) -> str:
    return " ".join(box.text.strip() for box in row if box.text.strip())
