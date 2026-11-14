"""Prepare a screenshot for text reading: open it, crop it, shrink it, fingerprint it."""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass

from PIL import Image, ImageOps

# Phone screenshots are often 2,500+ pixels tall. Text stays readable at this
# size, and reading a smaller image is several times faster.
MAX_LONG_SIDE_PIXELS = 1600


@dataclass(frozen=True)
class CropBox:
    """A rectangle in pixels, measured from the top-left corner of the image."""

    left: int
    top: int
    width: int
    height: int

    def as_pillow_box(self) -> tuple[int, int, int, int]:
        return (self.left, self.top, self.left + self.width, self.top + self.height)

    def covers_most_of(self, image_size: tuple[int, int], share: float = 0.95) -> bool:
        """True if the box barely trims the image, so it counts as "not cropped"."""
        image_width, image_height = image_size
        return self.width >= image_width * share and self.height >= image_height * share


def open_image(image_bytes: bytes) -> Image.Image:
    """Open uploaded bytes as an upright RGB image."""
    image = Image.open(io.BytesIO(image_bytes))
    # Phone photos can carry a "rotate me" tag instead of being stored upright.
    return ImageOps.exif_transpose(image).convert("RGB")


def crop_image(image: Image.Image, crop_box: CropBox | None) -> Image.Image:
    if crop_box is None:
        return image
    return image.crop(crop_box.as_pillow_box())


def shrink_for_reading(image: Image.Image, max_long_side: int = MAX_LONG_SIDE_PIXELS) -> Image.Image:
    """Return a smaller copy if the image is bigger than needed; never enlarges."""
    long_side = max(image.size)
    if long_side <= max_long_side:
        return image
    scale = max_long_side / long_side
    new_size = (round(image.width * scale), round(image.height * scale))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def fingerprint(image_bytes: bytes, crop_box: CropBox | None = None) -> str:
    """A short ID that is the same whenever the same screenshot and crop come back."""
    digest = hashlib.sha256(image_bytes)
    digest.update(repr(crop_box).encode())
    return digest.hexdigest()[:16]
