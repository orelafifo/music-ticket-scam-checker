from PIL import Image

from scam_checker.screenshot.image_prep import CropBox, crop_image, fingerprint, shrink_for_reading, trim_app_bars
from scam_checker.screenshot.ocr import CachedTextReader


class CountingReader:
    def __init__(self):
        self.times_called = 0

    def read(self, image):
        self.times_called += 1
        return ["hello"]


def test_large_screenshot_is_shrunk_keeping_its_shape():
    shrunk = shrink_for_reading(Image.new("RGB", (1170, 2532)))
    assert max(shrunk.size) == 1600
    assert abs(shrunk.width / shrunk.height - 1170 / 2532) < 0.01


def test_small_screenshot_is_never_enlarged():
    assert shrink_for_reading(Image.new("RGB", (400, 800))).size == (400, 800)


def test_crop_keeps_only_the_chosen_area():
    cropped = crop_image(Image.new("RGB", (100, 200)), CropBox(left=10, top=20, width=50, height=60))
    assert cropped.size == (50, 60)


def test_a_box_around_the_whole_image_counts_as_not_cropped():
    assert CropBox(0, 0, 99, 198).covers_most_of((100, 200))
    assert not CropBox(0, 50, 100, 100).covers_most_of((100, 200))


def test_top_and_bottom_bars_are_cut_off():
    trimmed = trim_app_bars(Image.new("RGB", (100, 1000)), top_share=0.1, bottom_share=0.05)
    assert trimmed.size == (100, 850)


def test_same_screenshot_and_crop_give_the_same_fingerprint():
    crop = CropBox(0, 0, 10, 10)
    assert fingerprint(b"abc", crop) == fingerprint(b"abc", crop)
    assert fingerprint(b"abc", crop) != fingerprint(b"abc", None)


def test_same_screenshot_is_only_read_once():
    reader = CountingReader()
    cached = CachedTextReader(reader)
    image = Image.new("RGB", (10, 10))
    cached.read(image, "same-id")
    cached.read(image, "same-id")
    assert reader.times_called == 1
