# 🎟️ Music Ticket Scam Checker (v3)

A prototype that checks screenshots of music ticket listings and chats for signs of a scam.
It is designed to sit inside a banking app, so people can check before they pay a stranger for tickets.

> **Status: Step 1 of 3 is built.** The app reads a screenshot, removes personal details and
> collects some context. It does **not** say "scam" or "not scam" yet; that is Step 2.

The earlier versions (v1 to v2.7) are archived at
[orelafifo/ticket-scam-checker](https://github.com/orelafifo/ticket-scam-checker).

---

## How the checker will work

| Step | What happens | Status |
|---|---|---|
| **1. Read and clean** | Read the text in the screenshot on this computer, then remove names, numbers, timestamps and app clutter | ✅ Built |
| 2. Ask questions | A small AI model running on this computer answers fixed yes/no questions, e.g. "Does it ask for a bank transfer?" | Not started |
| 3. Score | A simple scoring step turns the answers into a verdict with reasons | Not started |

The AI model only *reads* the text. It never makes the final decision.

---

## What Step 1 does

In the order the user sees it in the app:

1. **Asks for the artist first**, with suggestions as you type. This stops the artist's name being removed by mistake.
2. **Shows a tip:** "Try to capture ONLY the listing or chat."
3. **Takes the screenshot** (X, TikTok, Instagram, WhatsApp or other) and lets you **crop** it.
4. **Reads the text on this computer** with EasyOCR. Nothing is sent online. Big screenshots are shrunk first, and the same screenshot is never read twice.
5. **Removes personal details straight away**, before anything is shown or saved:
   - the top bar (where the other person's name and number sit) and the typing bar, using where the text sits on screen
   - timestamps ("14:32", "2h", "Yesterday") and app words ("Reply", "Like", "Seen", "Typing…", "Online")
   - emails, @handles, phone numbers, sort codes, account numbers and card numbers
   - person names found by spaCy, except the artist you typed (small spelling differences are allowed, so "Taylor Swfit" still counts as Taylor Swift)
6. **Never removes warning signs**: payment and platform words (PayPal, Revolut, Monzo, Ticketmaster, Twickets, AXS…) and big venue names are always kept, because Step 2 needs them.
7. **Shows the cleaned text** that will be checked.
8. **Checks a link** if the listing is on a website: is it a known site, a copy of a known site, shortened, insecure, or brand new? **The link is never opened.**
9. **Asks how you came across the seller**, with quick-pick buttons or your own words, and turns the answer into a category.
10. **Asks for the seller's follower count and account age**, with an N/A option. N/A means "unknown", never "suspicious".

At the end the app shows exactly what Step 2 will receive.

---

## Set up (once)

You need Python 3.10 to 3.13. In the VS Code terminal, inside this folder, run each line one at a time.

Create a private Python environment for this project:

```bash
python3 -m venv .venv
```

Switch it on (do this every time you open a new terminal):

```bash
source .venv/bin/activate
```

Install everything the app needs:

```bash
pip install -r requirements-dev.txt
```

The first time you read a screenshot, EasyOCR downloads its model (about 100 MB). After that it works offline.

## Run the app

```bash
streamlit run app.py
```

It opens in your browser. To try it without a real screenshot, upload `examples/fake_whatsapp_chat.png` and type **Dave** as the artist. Everything in that image is made up.

## Run the tests

The quick tests take a few seconds:

```bash
pytest
```

The slow test uses the real OCR model on the example screenshot:

```bash
pytest -m slow
```

---

## Folder map

```
app.py                         The Streamlit app (only screens and buttons, no checking logic)
scam_checker/
  step1.py                     Runs Step 1 from start to finish
  screenshot/
    image_prep.py              Open, crop, shrink and fingerprint the image
    ocr.py                     Read text with EasyOCR; remember results so nothing is read twice
    ocr_fixes.py               Fix OCR misreads, e.g. "E85" back to "£85"
    layout.py                  Drop the top and bottom bars using where text sits
  privacy/
    cleaner.py                 Runs every cleaning stage and counts what was removed
    clutter.py                 Timestamps and app words
    patterns.py                Emails, @handles, phone, bank and card numbers
    names.py                   Person names (spaCy), keeping the artist
    protected_words.py         Words that are never removed (payment, platform, venue)
  context/
    artists.py                 Artist suggestions and forgiving name matching
    link_check.py              Checks a web address without opening it
    known_sites.py             The list of ticket, resale and social sites
    seller.py                  How you met the seller, followers and account age
data/artist_suggestions.txt    Artists suggested while typing (add more any time)
examples/                      A made-up screenshot for demos and tests
scripts/                       Make the example screenshot and the before/after evidence
docs/redaction_example.md      Before-and-after removal example (for the privacy section)
tests/                         Automatic tests
```

## Privacy by design

- **Text is read on this computer.** No screenshot or text is sent to an online service in Step 1.
- **Removal happens straight after reading,** inside one function, so the uncleaned text is never shown or saved.
- **The app only counts what it removed** ("1 × phone number"). It never keeps the removed details.
- **Remembered reading results belong to one visitor only.** If the app is put online, one person's screenshot is never kept where another visitor could reach it.
- **Links are never opened.** Only the web address is checked, plus its public registration date.

See [`docs/redaction_example.md`](docs/redaction_example.md) for a real before-and-after run. To recreate it:

```bash
python scripts/make_redaction_example.py
```

## Known limits

- **spaCy's small model misses some names**, especially in lower case, and sometimes takes a nearby word with the name ("Sorry Jess" becomes "[name]"). Cropping the screenshot to just the messages helps.
- **OCR misreads some symbols:** "£" can come out as "E" (fixed automatically) or "€" (not fixed yet).
- **The top and bottom bar sizes are averages** for common phones. Cropping is the most reliable way to remove them.
- **Clock times inside a message are removed too**, e.g. "doors at 19:30". Dates are kept.
- **"How you met the seller" uses simple keywords for now.** It is built so the Step 2 AI model can replace it without changing the app.
- **The website-age check needs the internet.** If it can't connect, it is skipped and never counts against the seller.
