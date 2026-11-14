"""Music Ticket Scam Checker - Step 1 app.

Run with:  streamlit run app.py

Step 1 reads a screenshot, removes personal details and collects context.
It does not give a scam verdict yet; that arrives in Step 2.
"""

from __future__ import annotations

import streamlit as st
from PIL import Image

from scam_checker.context.artists import load_artist_suggestions
from scam_checker.context.link_check import LinkReport, check_link, lookup_domain_age_days
from scam_checker.context.seller import (
    EXAMPLE_ANSWERS,
    QUICK_PICKS,
    KeywordSourceCategoriser,
    SellerAccount,
    SellerSource,
)
from scam_checker.privacy.cleaner import CleaningReport
from scam_checker.privacy.names import SpacyNameFinder
from scam_checker.screenshot.image_prep import CropBox, crop_image, fingerprint, open_image
from scam_checker.screenshot.ocr import CachedTextReader, OllamaVisionReader, TextReadingError
from scam_checker.step1 import SOURCE_APPS, Step1Result, read_and_clean_screenshot

CHAT = "A chat"
POST = "A post or listing"


# --- shared, heavy resources (hold models only, never user data) -------------


@st.cache_resource(show_spinner=False)
def shared_vision_reader() -> OllamaVisionReader:
    return OllamaVisionReader()


@st.cache_resource(show_spinner="Loading the name finder (first time only)...")
def shared_name_finder() -> SpacyNameFinder:
    return SpacyNameFinder()


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def cached_domain_age(domain: str) -> int | None:
    return lookup_domain_age_days(domain)


def session_text_reader() -> CachedTextReader:
    # One cache per visitor: it holds text before cleaning, so it is never shared.
    if "text_reader" not in st.session_state:
        st.session_state.text_reader = CachedTextReader(shared_vision_reader())
    return st.session_state.text_reader


# --- page sections, in the order the user sees them --------------------------


def show_header() -> None:
    st.title("🎟️ Music Ticket Scam Checker")
    st.caption("Step 1 of the checker: read your screenshot and remove personal details. No verdict yet.")


def ask_for_artist() -> str:
    st.subheader("1. Which artist are the tickets for?")
    artist = st.selectbox(
        "Start typing to see suggestions. You can type any artist.",
        options=load_artist_suggestions(),
        index=None,
        placeholder="e.g. Taylor Swift",
        accept_new_options=True,
    )
    st.caption("We ask first so we never remove the artist's name by mistake.")
    return (artist or "").strip()


def ask_for_screenshot(artist: str) -> tuple[bytes | None, str, str]:
    st.subheader("2. Upload a screenshot")
    st.info("💡 Tip: try to capture **only** the listing or chat, not your whole screen.")
    left, right = st.columns(2)
    source_app = left.selectbox("Which app is it from?", SOURCE_APPS)
    kind = right.radio("What does it show?", [CHAT, POST], horizontal=True)
    upload = st.file_uploader(
        "Screenshot (PNG or JPG)",
        type=["png", "jpg", "jpeg"],
        disabled=not artist,
        help="Type the artist's name first." if not artist else None,
    )
    return (upload.getvalue() if upload else None), source_app, kind


def ask_for_crop(image: Image.Image) -> CropBox | None:
    if not st.checkbox("Crop the screenshot to just the listing or messages"):
        return None
    from streamlit_cropper import st_cropper

    st.caption("Drag the box over the part you want checked.")
    full_image = (0, image.width, 0, image.height)
    box = st_cropper(image, default_coords=full_image, return_type="box", box_color="#d6336c")
    crop_box = CropBox(box["left"], box["top"], box["width"], box["height"])
    return None if crop_box.covers_most_of(image.size) else crop_box


def ask_remove_bars(kind: str, crop_box: CropBox | None) -> bool:
    return st.checkbox(
        "Remove the top bar (name and number) and the typing bar",
        value=kind == CHAT and crop_box is None,
        help="Best for chat screenshots that haven't been cropped.",
    )


def read_screenshot(image_bytes: bytes, crop_box: CropBox | None, artist: str, remove_bars: bool) -> CleaningReport:
    image = crop_image(open_image(image_bytes), crop_box)
    try:
        with st.spinner("Reading the screenshot on this computer (the first one can take a minute)..."):
            return read_and_clean_screenshot(
                image,
                fingerprint(image_bytes, crop_box),
                session_text_reader(),
                shared_name_finder(),
                artist,
                remove_bars,
            )
    except TextReadingError as problem:
        st.error(str(problem))
        st.stop()


def show_cleaned_text(report: CleaningReport) -> str:
    st.subheader("3. Check the cleaned text")
    st.caption(report.summary())
    st.text_area("Text that will be checked", report.cleaned_text, disabled=True, height=150)
    return report.cleaned_text


def ask_for_link() -> LinkReport | None:
    st.subheader("4. Is the listing on a website? (optional)")
    link = st.text_input("Paste the link", placeholder="https://...")
    st.caption("We never open the link. We only look at the web address.")
    if not link.strip():
        return None
    report = check_link(link, lookup_age=cached_domain_age)
    for note in report.notes:
        st.markdown(f"- {note}")
    return report


def ask_how_seller_was_found() -> tuple[str, SellerSource]:
    st.subheader("5. How did you come across this seller?")
    quick_pick = st.pills("Quick pick", list(QUICK_PICKS))
    answer = st.text_input("Or describe it in your own words", placeholder="e.g. " + EXAMPLE_ANSWERS[0])
    st.caption("Examples: " + " · ".join(EXAMPLE_ANSWERS))
    if answer.strip():
        source = KeywordSourceCategoriser().categorise(answer)
    else:
        source = QUICK_PICKS.get(quick_pick, SellerSource.UNKNOWN)
    return answer.strip() or (quick_pick or ""), source


def ask_number_or_not_available(column, label: str, key: str) -> int | None:
    # The tick box sits under the number box but decides whether it's usable,
    # so its current value is read from session state before either is drawn.
    not_available = st.session_state.get(f"{key}-na", False)
    value = column.number_input(label, min_value=0, step=1, value=None, disabled=not_available, key=key)
    column.checkbox("N/A (not shown)", key=f"{key}-na")
    return None if not_available or value is None else int(value)


def ask_about_seller_account() -> SellerAccount:
    st.subheader("6. About the seller's account")
    st.caption("If the app doesn't show this, tick N/A. Not knowing never counts against the seller.")
    left, right = st.columns(2)
    followers = ask_number_or_not_available(left, "Follower count", "followers")
    age_months = ask_number_or_not_available(right, "Account age (months)", "account-age")
    return SellerAccount(follower_count=followers, account_age_months=age_months)


def show_handover(result: Step1Result) -> None:
    st.subheader("Ready for Step 2")
    st.success("Step 1 is done. The scam check itself arrives in Step 2.")
    with st.expander("See exactly what Step 2 will receive"):
        st.json(result.to_dict())


# --- the page ----------------------------------------------------------------


def wait_for_read_button(screenshot_id: str) -> bool:
    """Read only when asked, so dragging the crop box doesn't re-read the image each time."""
    if st.button("Read the screenshot", type="primary"):
        st.session_state.screenshot_to_read = screenshot_id
    return st.session_state.get("screenshot_to_read") == screenshot_id


def screenshot_steps(artist: str, image_bytes: bytes, kind: str) -> tuple[str, CleaningReport] | None:
    """Crop, read and clean. Returns (final text, report), or None until the user presses Read."""
    crop_box = ask_for_crop(open_image(image_bytes))
    remove_bars = ask_remove_bars(kind, crop_box)
    screenshot_id = fingerprint(image_bytes, crop_box)
    if not wait_for_read_button(screenshot_id):
        return None
    report = read_screenshot(image_bytes, crop_box, artist, remove_bars)
    return show_cleaned_text(report), report


def main() -> None:
    st.set_page_config(page_title="Music Ticket Scam Checker", page_icon="🎟️", layout="centered")
    show_header()
    artist = ask_for_artist()
    image_bytes, source_app, kind = ask_for_screenshot(artist)
    if not (artist and image_bytes):
        return
    screenshot_result = screenshot_steps(artist, image_bytes, kind)
    if screenshot_result is None:
        return
    final_text, report = screenshot_result
    link = ask_for_link()
    seller_answer, seller_source = ask_how_seller_was_found()
    show_handover(
        Step1Result(
            artist=artist,
            source_app=source_app,
            cleaned_text=final_text,
            removed_counts=dict(report.removed_counts),
            link=link,
            seller_source_answer=seller_answer,
            seller_source=seller_source,
            seller_account=ask_about_seller_account(),
        )
    )


if __name__ == "__main__":
    main()
