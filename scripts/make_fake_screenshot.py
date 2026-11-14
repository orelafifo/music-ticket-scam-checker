"""Draw a made-up WhatsApp-style chat for demos and tests.

Every name and number in it is invented. Run:  python scripts/make_fake_screenshot.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUTPUT_FILE = Path(__file__).resolve().parents[1] / "examples" / "fake_whatsapp_chat.png"
WIDTH, HEIGHT = 1170, 2532  # an iPhone screenshot's size
GREY = (120, 120, 120)

MESSAGES = [  # (text, sent by the buyer?)
    ("Hi, still got the Dave tickets?", True),
    ("Yes 2 left, £85 each", False),
    ("Bank transfer only, PayPal", False),
    ("is down. Call 07123 456789", False),
    ("Can you do Twickets?", True),
    ("Sorry Jess, bank only", False),
]
BUBBLE_GAP = 250


def font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default(size)


def draw_top_bar(draw: ImageDraw.ImageDraw) -> None:
    draw.rectangle([0, 0, WIDTH, 260], fill=(7, 94, 84))
    draw.text((60, 120), "Jess Smith", fill="white", font=font(56))
    draw.text((60, 190), "online", fill="white", font=font(36))


def draw_bubble(draw: ImageDraw.ImageDraw, top: int, text: str, from_buyer: bool) -> None:
    left = WIDTH - 900 if from_buyer else 40
    colour = (220, 248, 198) if from_buyer else "white"
    draw.rounded_rectangle([left, top, left + 860, top + 170], 30, fill=colour)
    draw.text((left + 30, top + 25), text, fill="black", font=font(44))
    draw.text((left + 700, top + 115), "14:32", fill=GREY, font=font(32))


def draw_bottom_bar(draw: ImageDraw.ImageDraw) -> None:
    draw.text((WIDTH - 200, 420 + len(MESSAGES) * BUBBLE_GAP), "Seen", fill=GREY, font=font(36))
    draw.rectangle([0, HEIGHT - 200, WIDTH, HEIGHT], fill="white")
    draw.text((80, HEIGHT - 140), "Type a message", fill=(150, 150, 150), font=font(48))


def main() -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), (236, 229, 221))
    draw = ImageDraw.Draw(image)
    draw_top_bar(draw)
    for number, (text, from_buyer) in enumerate(MESSAGES):
        draw_bubble(draw, 400 + number * BUBBLE_GAP, text, from_buyer)
    draw_bottom_bar(draw)
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    image.save(OUTPUT_FILE)
    print(f"Saved {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
