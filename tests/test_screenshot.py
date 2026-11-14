from PIL import Image

from scam_checker.screenshot.image_prep import CropBox, crop_image, fingerprint, shrink_for_reading
from scam_checker.screenshot.layout import boxes_to_lines, remove_app_bars
from scam_checker.screenshot.ocr import CachedTextReader, TextBox


def box(text: str, top: float, left: float = 0.1, height: float = 0.03) -> TextBox:
    return TextBox(text=text, top=top, bottom=top + height, left=left)


class CountingReader:
    def __init__(self, boxes: list[TextBox]):
        self.boxes = boxes
        self.times_called = 0

    def read(self, image):
        self.times_called += 1
        return self.boxes


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


def test_same_screenshot_and_crop_give_the_same_fingerprint():
    crop = CropBox(0, 0, 10, 10)
    assert fingerprint(b"abc", crop) == fingerprint(b"abc", crop)
    assert fingerprint(b"abc", crop) != fingerprint(b"abc", None)


def test_same_screenshot_is_only_read_once():
    reader = CountingReader([box("hello", 0.5)])
    cached = CachedTextReader(reader)
    image = Image.new("RGB", (10, 10))
    cached.read(image, "same-id")
    cached.read(image, "same-id")
    assert reader.times_called == 1


def test_top_and_bottom_bars_removed_using_positions():
    boxes = [box("Jess Smith", 0.03), box("tickets still available?", 0.5), box("Type a message", 0.95)]
    kept, removed_count = remove_app_bars(boxes)
    assert [b.text for b in kept] == ["tickets still available?"]
    assert removed_count == 2


def test_boxes_on_the_same_row_become_one_line_left_to_right():
    boxes = [box("each", 0.30, left=0.6), box("£85", 0.30, left=0.2), box("Block 112", 0.40)]
    assert boxes_to_lines(boxes) == ["£85 each", "Block 112"]


def test_pound_sign_misread_as_e_is_fixed():
    assert boxes_to_lines([box("Yes 2 left, E85 each", 0.5)]) == ["Yes 2 left, £85 each"]


def test_words_starting_with_e_are_untouched():
    assert boxes_to_lines([box("Each ticket E-ticket", 0.5)]) == ["Each ticket E-ticket"]
