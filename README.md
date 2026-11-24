# 🎟️ Music Ticket Scam Checker (v3)

[![Tests](https://github.com/orelafifo/music-ticket-scam-checker/actions/workflows/tests.yml/badge.svg)](https://github.com/orelafifo/music-ticket-scam-checker/actions/workflows/tests.yml)

A prototype that checks screenshots of music ticket listings and chats for signs of a scam.
It is designed to sit inside a banking app, so people can check before they pay a stranger for tickets.

> **Status:** Step 1 is built and in the app. Step 2 (questions and scoring) is built and being
> tested; the app does not show a verdict yet.

---

## How the checker will work

| Step | What happens | Status |
|---|---|---|
| **1. Read and clean** | Read the text in the screenshot on this computer, then remove names, numbers, timestamps and app clutter | ✅ Built |
| 2. Ask questions | A small AI model on this computer answers 20 fixed yes/no questions, e.g. "Does it ask for a bank transfer?" | Built, being tested |
| 3. Score | Logistic regression turns the answers, plus the Step 1 answers, into a verdict with reasons | Built, not in the app yet |

The AI model only *reads* the text. It never makes the final decision.

---

## What Step 1 does

In the order the user sees it in the app:

1. **Asks for the artist first**, with suggestions as you type. This stops the artist's name being removed by mistake.
2. **Asks where you found the tickets** (WhatsApp, Instagram, TikTok, X, Facebook, a forum, a website or other). Choosing **Other** lets you type the answer. Choosing **A website** asks for the link and checks whether the site looks fake or dodgy (see below).
3. **Shows a tip:** "Try to capture ONLY the listing or chat", then takes the screenshot and lets you **crop** it.
4. **Reads the text on this computer** with Qwen2.5-VL, a vision AI model run by the free Ollama app. Nothing is sent online. The model is only asked to copy the text out; it never judges it. Big screenshots are shrunk first, and the same screenshot is never read twice.
5. **Removes personal details straight away**, before anything is shown or saved:
   - the top bar (where the other person's name and number sit) and the typing bar, trimmed off automatically before the model sees them (unless you crop the screenshot yourself)
   - timestamps ("14:32", "2h", "Yesterday") and app words ("Reply", "Like", "Seen", "Typing…", "Online")
   - emails, @handles, phone numbers, sort codes, account numbers and card numbers
   - WhatsApp display names after a "~" at the start of a line (WhatsApp's mark for senders not in your contacts), even ordinary words like "~ Me"
   - X display names on a post's header line ("Megan @megs_tix · 2h")
   - people's names, found by spaCy and by the Qwen AI model working together (a name either one finds is removed), except the artist you typed (small spelling differences are allowed, so "Taylor Swfit" still counts as Taylor Swift). The AI catches names spaCy misses, like "hi jess", and usernames shown without an @, as on Instagram and TikTok. It can only point at names: anything it returns that isn't in the text is ignored. Qwen also spots group chat, channel and page titles (e.g. a WhatsApp group's name), which become [title].
6. **Never removes warning signs**: payment and platform words (PayPal, Revolut, Monzo, Ticketmaster, Twickets, AXS…) and big venue names are always kept, because Step 2 needs them.
7. **Shows the cleaned text** that will be checked.
8. **Checks the event** in the background: reads the venue and date from the listing and looks them up on Ticketmaster and Skiddle, then shows a one-line confirmation. A mismatch is always a warning; "couldn't check" never counts against the seller.
9. **Asks how you came across the seller**, with quick-pick buttons or your own words, and turns the answer into a category.
10. **Asks for the seller's follower count and account age**, with an N/A option. N/A means "unknown", never "suspicious".

### Website check (the link is never opened)

| Check | What it looks for |
|---|---|
| Known sites | Is it a recognised ticket, resale or social site? |
| Copycat address | Does it imitate a real site, e.g. "ticketrnaster-uk.com"? |
| Shortened or insecure link | Does it hide the real address (bit.ly) or lack https? |
| Risky address ending | Endings often used by scam sites, e.g. .shop or .xyz (a weak sign on its own) |
| Website age | When the address was registered (public RDAP registry) |
| Security certificate age | When the site's first padlock certificate was issued (public crt.sh logs) |
| Google's scam list | Is it on Google Safe Browsing's list of scam and dangerous sites? (optional key, see below) |

Only the website's address (e.g. `ticket-deals.shop`) is sent to these services, never the full link, because the rest of a link can contain an ID tied to the person checking. If a lookup fails, it is skipped and never counts against the website.

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

Install **Ollama**, the free app that runs the reading model on your computer: download it from [ollama.com](https://ollama.com), open it, and it will sit in your menu bar.

Then download the models (once): the reading model (about 3 GB) and the Step 2 model (about 4 GB):

```bash
ollama pull qwen2.5vl:3b
```

```bash
ollama pull qwen3.5:4b
```

Ollama needs to be open whenever you use the app.

### Optional: keys in `.env`

Copy `.env.example` to a new file called `.env` and add any keys you have. The app works without them; the matching check just says "not checked".

- `TICKETMASTER_API_KEY`, `SKIDDLE_API_KEY`: free keys for the event check ([developer.ticketmaster.com](https://developer.ticketmaster.com), [skiddle.com/api/join.php](https://www.skiddle.com/api/join.php))
- `GOOGLE_SAFE_BROWSING_KEY`: Google's scam list, see below

#### Google's scam list

The website check can also ask Google Safe Browsing whether a site is a known scam. It needs a free key:

1. Go to [console.cloud.google.com](https://console.cloud.google.com), create a project and turn on the **Safe Browsing API**.
2. Under **APIs & Services → Credentials**, create an **API key**.
3. Paste it into `.env` after `GOOGLE_SAFE_BROWSING_KEY=`.

The `.env` file is never uploaded to GitHub. Google's free key is for non-commercial use; a bank would use Google's paid version (Web Risk).

## Run the app

```bash
streamlit run app.py
```

It opens in your browser. To try it without a real screenshot, upload `examples/fake_whatsapp_chat.png` and type **Dave** as the artist. Everything in that image is made up.

To also see what the model read before cleaning, and exactly what Step 1 hands to Step 2 (for building and testing only; users never see this), start it in developer mode:

```bash
streamlit run app.py -- --debug
```

## Step 2: compare the AI models

Run in this order (Ollama open). Each script explains itself with `--help`.

```bash
python scripts/run_ai_answers.py --model qwen      # then --model qwen25
python scripts/train_scoring.py --answers data/step2/answers_qwen.csv   # sensitivity table
python scripts/compare_models.py                   # charts and winner in outputs/
```

The rules for picking the winner were written before testing: [`docs/step2_judging_rules.md`](docs/step2_judging_rules.md).

## Run the tests

The quick tests take a few seconds:

```bash
pytest
```

The slow test uses the real reading model on the example screenshot (Ollama must be open):

```bash
pytest -m slow
```

Every push to GitHub also runs the code-style checks (ruff) and the quick tests automatically, using GitHub Actions (`.github/workflows/tests.yml`). The badge at the top of this page shows whether the latest run passed.

---

## Folder map

```
app.py                         The Streamlit app (only screens and buttons, no checking logic)
scam_checker/
  step1.py                     Runs Step 1 from start to finish
  local_ai.py                  Talks to the Qwen model through Ollama (used for reading and for names)
  screenshot/
    image_prep.py              Open, crop, trim the app bars, shrink and fingerprint the image
    ocr.py                     Read text with Qwen2.5-VL through Ollama; remember results so nothing is read twice
  privacy/
    cleaner.py                 Runs every cleaning stage and counts what was removed
    clutter.py                 Timestamps and app words
    patterns.py                Emails, @handles, phone, bank and card numbers
    names.py                   Removes names (spaCy plus the AI), keeping the artist
    ai_names.py                Asks the Qwen model which words are people's names
    protected_words.py         Words that are never removed (payment, platform, venue)
  context/
    artists.py                 Artist suggestions and forgiving name matching
    where_found.py             The "Where did you find the tickets?" options
    link_check.py              Checks whether a website looks fake, without opening it
    website_records.py         Public-record lookups: registration date, certificates, Google's scam list
    known_sites.py             Known ticket, resale and social sites, and risky address endings
    seller.py                  How you met the seller, followers and account age
    event_details.py           Reads the venue and date from the listing
    event_check.py             Checks them on Ticketmaster and Skiddle
  scoring/                     Step 2
    questions.py               The 20 yes/no questions, each with a source
    ask_ai.py                  Asks the AI model the questions
    step1_signals.py           Points for the Step 1 answers (fixed, from evidence)
    scorer.py                  Logistic regression, warning level by cost, reasons
    compare.py                 Picks the winning model using the judging rules
data/artist_suggestions.txt    Artists suggested while typing (add more any time)
data/step2/                    200 tagged examples: practice set, locked test set, AI answers
examples/                      A made-up screenshot for demos and tests
scripts/                       Example screenshot, evidence, and the Step 2 scripts
docs/                          Removal example, Step 2 questions, Step 1 points, judging rules
tests/                         Automatic tests
```

## Privacy by design

- **Text is read on this computer.** No screenshot or listing text is sent online. Only the artist's name (and the month) goes to Ticketmaster and Skiddle for the event check.
- **Removal happens straight after reading,** inside one function, so the uncleaned text is never shown or saved.
- **The app only counts what it removed** ("1 × phone number"). It never keeps the removed details.
- **Remembered reading results belong to one visitor only.** If the app is put online, one person's screenshot is never kept where another visitor could reach it.
- **Links are never opened.** Only the website's address is checked against public records, and only the address is sent, never the full link.

See [`docs/redaction_example.md`](docs/redaction_example.md) for a real before-and-after run. To recreate it (Ollama must be open):

```bash
python scripts/make_redaction_example.py
```

## Known limits

- Some names can be missed, so cropping to just the messages gives the best result.
- The reading model can occasionally misread a word or symbol.
