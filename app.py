"""Music Ticket Scam Checker - Step 1 app.

Run with:  streamlit run app.py

Step 1 reads a screenshot, removes personal details and collects context.
It does not give a scam verdict yet; that arrives in Step 2.
"""

from __future__ import annotations

import sys
from datetime import date

import streamlit as st
from dotenv import load_dotenv
from PIL import Image

from scam_checker.context import website_records
from scam_checker.context.artists import load_artist_suggestions
from scam_checker.context.event_check import EventReport
from scam_checker.context.event_check import check_event as look_up_event
from scam_checker.context.event_details import read_event_details
from scam_checker.context.link_check import LinkReport, WebsiteLookups, check_link
from scam_checker.context.seller import (
    EXAMPLE_ANSWERS,
    QUICK_PICKS,
    KeywordSourceCategoriser,
    SellerAccount,
    SellerSource,
)
from scam_checker.context.where_found import OTHER, WEBSITE, WHERE_FOUND_OPTIONS
from scam_checker.local_ai import LocalAIError
from scam_checker.privacy.ai_names import OllamaNameFinder
from scam_checker.privacy.cleaner import CleaningReport
from scam_checker.privacy.names import CachedNameFinder, CombinedNameFinder, NameFinder, SpacyNameFinder
from scam_checker.screenshot.image_prep import CropBox, crop_image, fingerprint, open_image
from scam_checker.screenshot.ocr import CachedTextReader, OllamaVisionReader
from scam_checker.step1 import Step1Result, read_and_clean_screenshot

load_dotenv()  # reads the optional Google Safe Browsing key from a local .env file

# Developer mode shows what Step 1 hands to Step 2. Users never see it.
# Turn it on with:  streamlit run app.py -- --debug
DEVELOPER_MODE = "--debug" in sys.argv[1:]


# --- shared, heavy resources (hold models only, never user data) -------------


@st.cache_resource(show_spinner=False)
def shared_vision_reader() -> OllamaVisionReader:
    return OllamaVisionReader()


@st.cache_resource(show_spinner="Loading the name finder (first time only)...")
def shared_spacy_finder() -> SpacyNameFinder:
    return SpacyNameFinder()


@st.cache_resource(show_spinner=False)
def shared_ai_name_finder() -> OllamaNameFinder:
    return OllamaNameFinder()


# Public records about a website change slowly, so each is looked up at most once a day.
@st.cache_data(ttl=24 * 3600, show_spinner=False)
def cached_domain_age(domain: str) -> int | None:
    return website_records.lookup_domain_age_days(domain)


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def cached_certificate_age(domain: str) -> int | None:
    return website_records.lookup_certificate_age_days(domain)


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def cached_blocklist(domain: str) -> bool | None:
    return website_records.lookup_on_blocklist(domain)


CACHED_LOOKUPS = WebsiteLookups(cached_domain_age, cached_certificate_age, cached_blocklist)


def session_text_reader() -> CachedTextReader:
    # One cache per visitor: it holds text before cleaning, so it is never shared.
    if "text_reader" not in st.session_state:
        st.session_state.text_reader = CachedTextReader(shared_vision_reader())
    return st.session_state.text_reader


def session_name_finder() -> NameFinder:
    """spaCy and the AI together: a name either one finds is removed."""
    # The AI's answers are cached per visitor, because they come from that visitor's text.
    if "ai_name_finder" not in st.session_state:
        st.session_state.ai_name_finder = CachedNameFinder(shared_ai_name_finder())
    return CombinedNameFinder(shared_spacy_finder(), st.session_state.ai_name_finder)


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


def ask_where_tickets_were_found() -> tuple[str, LinkReport | None]:
    st.subheader("2. Where did you find the tickets?")
    choice = st.selectbox(
        "Where did you find the tickets?",
        WHERE_FOUND_OPTIONS,
        index=None,
        placeholder="Choose one",
        label_visibility="collapsed",
    )
    if choice == OTHER:
        return st.text_input("Where was it?", placeholder="e.g. a Discord server").strip(), None
    if choice == WEBSITE:
        return WEBSITE, ask_for_link()
    return choice or "", None


def ask_for_link() -> LinkReport | None:
    link = st.text_input("Paste the website link", placeholder="https://...")
    st.caption("We never open the link. We only check the address and public records about it.")
    if not link.strip():
        return None
    with st.spinner("Checking the website..."):
        report = check_link(link, CACHED_LOOKUPS)
    for note in report.notes:
        st.markdown(f"- {note}")
    return report


def ask_for_screenshot(artist: str) -> bytes | None:
    st.subheader("3. Upload a screenshot")
    st.info("💡 Tip: try to capture **only** the listing or chat, not your whole screen.")
    upload = st.file_uploader(
        "Screenshot (PNG or JPG)",
        type=["png", "jpg", "jpeg"],
        disabled=not artist,
        help="Type the artist's name first." if not artist else None,
    )
    return upload.getvalue() if upload else None


def ask_for_crop(image: Image.Image) -> CropBox | None:
    if not st.checkbox("Crop the screenshot to just the listing or messages"):
        return None
    from streamlit_cropper import st_cropper

    st.caption("Drag the box over the part you want checked.")
    full_image = (0, image.width, 0, image.height)
    box = st_cropper(image, default_coords=full_image, return_type="box", box_color="#d6336c")
    crop_box = CropBox(box["left"], box["top"], box["width"], box["height"])
    return None if crop_box.covers_most_of(image.size) else crop_box


def read_screenshot(image_bytes: bytes, crop_box: CropBox | None, artist: str, remove_bars: bool) -> CleaningReport:
    image = crop_image(open_image(image_bytes), crop_box)
    try:
        with st.spinner("Reading the screenshot and removing personal details (the first one can take a minute)..."):
            return read_and_clean_screenshot(
                image,
                fingerprint(image_bytes, crop_box),
                session_text_reader(),
                session_name_finder(),
                artist,
                remove_bars,
            )
    except LocalAIError as problem:
        st.error(str(problem))
        st.stop()


def show_cleaned_text(report: CleaningReport) -> str:
    st.subheader("4. Check the cleaned text")
    st.caption(report.summary())
    st.text_area("Text that will be checked", report.cleaned_text, disabled=True, height=150)
    return report.cleaned_text


@st.cache_data(show_spinner="Checking the event...", ttl=3600)
def cached_event_check(artist: str, venue: str, event_date_iso: str) -> EventReport:
    # Only the artist's name (and the month, for Skiddle) is sent, never the listing.
    return look_up_event(artist, venue, date.fromisoformat(event_date_iso) if event_date_iso else None)


def check_event(artist: str, cleaned_text: str) -> EventReport:
    """Reads the venue and date from the listing and checks them. No extra step for the user."""
    details = read_event_details(cleaned_text)
    event_date = details.event_date.isoformat() if details.event_date else ""
    report = cached_event_check(artist, details.venue, event_date)
    show_event_result(report)
    return report


def show_event_result(report: EventReport) -> None:
    if report.mismatch:
        official = ", ".join(x for x in (report.official_venue, report.official_date) if x)
        st.error(f"Event check: this doesn't match the official event. The closest official date is {official}.")
    elif report.found:
        st.success(f"✓ Event confirmed: {report.official_venue}, {report.official_date}")
        if report.before_on_sale:
            st.warning("These tickets are offered before the official general sale.")
    else:
        st.caption("Event check: we couldn't confirm this event (it may not be listed on Ticketmaster or Skiddle).")
    if "Skiddle" in report.source:
        st.caption("Event data from Skiddle.")


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
    st.caption("If not shown or available, tick N/A.")
    left, right = st.columns(2)
    followers = ask_number_or_not_available(left, "Follower count", "followers")
    age_months = ask_number_or_not_available(right, "Account age (months)", "account-age")
    return SellerAccount(follower_count=followers, account_age_months=age_months)


def show_developer_view(result: Step1Result) -> None:
    if not DEVELOPER_MODE:
        return
    st.divider()
    # Uncleaned text, shown only on the developer's own machine to check what the model read.
    st.caption("Developer mode: what Qwen read, before cleaning")
    st.text_area("Raw reading", "\n".join(session_text_reader().latest_lines), disabled=True, height=150)
    st.caption("Developer mode: what Step 1 hands to Step 2")
    st.json(result.to_dict(), expanded=False)


# --- the page ----------------------------------------------------------------


def wait_for_read_button(screenshot_id: str) -> bool:
    """Read only when asked, so dragging the crop box doesn't re-read the image each time."""
    if st.button("Read the screenshot", type="primary"):
        st.session_state.screenshot_to_read = screenshot_id
    return st.session_state.get("screenshot_to_read") == screenshot_id


def screenshot_steps(artist: str, image_bytes: bytes) -> tuple[str, CleaningReport] | None:
    """Crop, read and clean. Returns (final text, report), or None until the user presses Read."""
    crop_box = ask_for_crop(open_image(image_bytes))
    # Bars are always removed for privacy, unless the user cropped: then they
    # chose the area themselves, and trimming more could cut off the listing.
    remove_bars = crop_box is None
    screenshot_id = fingerprint(image_bytes, crop_box)
    if not wait_for_read_button(screenshot_id):
        return None
    report = read_screenshot(image_bytes, crop_box, artist, remove_bars)
    return show_cleaned_text(report), report


def main() -> None:
    st.set_page_config(page_title="Music Ticket Scam Checker", page_icon="🎟️", layout="centered")
    show_header()
    artist = ask_for_artist()
    where_found, link = ask_where_tickets_were_found()
    image_bytes = ask_for_screenshot(artist)
    if not (artist and image_bytes):
        return
    screenshot_result = screenshot_steps(artist, image_bytes)
    if screenshot_result is None:
        return
    final_text, report = screenshot_result
    event = check_event(artist, final_text)
    seller_answer, seller_source = ask_how_seller_was_found()
    show_developer_view(
        Step1Result(
            artist=artist,
            where_found=where_found,
            cleaned_text=final_text,
            removed_counts=dict(report.removed_counts),
            link=link,
            seller_source_answer=seller_answer,
            seller_source=seller_source,
            seller_account=ask_about_seller_account(),
            event=event,
        )
    )


if __name__ == "__main__":
    main()
