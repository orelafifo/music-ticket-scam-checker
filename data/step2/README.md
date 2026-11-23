# Step 2 data: 200 examples and the locked test set

Made 23 Nov 2026 from the old v2 project data (`~/Documents/ticket_scam_checker/data`, 324 examples, no duplicates).

## Files
| File | Rows | What |
|---|---|---|
| `all_200_examples.csv` | 200 | Everything, with a `set` column (practice or test) |
| `practice_set.csv` | 160 | Use this to compare the 3 LLMs and to build the scoring |
| `locked_test_set.csv` | 40 | **Do not open until the final test** |

## Tags (`tag` column)
- **real word-for-word**: the seller's own words, quoted in the source
- **rebuilt from a news story**: a documented scam, wording rebuilt from the article's description
- **written for the project**: a genuine example written for the project, modelled on real posts

| | Scams | Genuine |
|---|---|---|
| Real word-for-word | 32 | 67 |
| Rebuilt from a news story | 68 | 0 |
| Written for the project | 0 | 33 |
| **Total** | **100** | **100** |

## How the 200 were chosen
- All 99 real word-for-word examples are included.
- 68 rebuilt scams and 33 written genuine posts were picked at random (seed 2026), music events only.
- 9 real examples are not music events (football or theatre). They are marked `music_event = no` and are all in the practice set.

## How the test set was chosen (20 scams + 20 genuine)
- **Only examples that v2.5 and v2.6 never learned from or were shaped by**: blind test #4, blind test #5 (with its spare genuine posts) and the v2.7 new rows. This keeps the final v3 vs v2.5 vs v2.6 test fair.
- Orela's 3 WhatsApp Olivia Rodrigo posts are **not** in the test, because they triggered v2.6 changes.
- Music events only.
- **Genuine (20):** all real word-for-word. Mix of festivals, arena and small gigs, plus some "hard" genuine posts that look a bit like scams (DM me, no price, illness, hospital, "quick sale").
- **Scams (20):** 6 real word-for-word (all that were available in the unseen data, 4 from Ireland) + 14 rebuilt, chosen to cover different scam types:

| Scam type | Example IDs (old) |
|---|---|
| Hacked friend's account (Instagram) | D16 |
| Fake ticket website | D21 |
| TikTok seller, bank account switched after a failed payment | D34 |
| Paying outside a resale platform | N11 |
| Payment to a "colleague's" account, half now | T02 |
| Screenshot as proof, small event | T05 |
| Fake page selling several artists, cash | T10 |
| Fake Ticketmaster transfer steps | N01 |
| "Send it to my cousin", "it's not a scam" | N14 |
| Split payments and extra fees | N26 |
| Western Union | N29 |
| Someone the buyer knew in person | N10 |
| "Going cheap, quick sale" on Instagram | N13 |
| Half now, half later (Gumtree) | N05 |

- An extra search on 23 Nov for 10 more real word-for-word scam messages found none usable: news articles describe the scammer's messages in their own words.

## Fingerprints (sha256)
- `locked_test_set.csv`: `9a6727a9658494cc1469bdf1163a707ff2c73026c1a5b0fb5129c07ffec9fd92`
- `practice_set.csv`: `d499ad7b3a7642ebecfd689b548f64b328ef42197edec693b30bf13685bfba4c`
- `all_200_examples.csv`: `e32c97ceaad274414fe72a70f89673b416cc9a3829cf779284e1e5253f06f1fc`

Check before the final test with: `shasum -a 256 data/step2/locked_test_set.csv`

## Known limits (for the report)
- Only 32 real word-for-word scams exist, so most scams are rebuilt.
- Every rebuilt example is a scam and every written example is genuine, so a model could learn writing style instead of warning signs. Using all real examples reduces this.
- Some texts include notes in [square brackets] about what happened later (e.g. "seller asked for more money"). A buyer would not see these in the listing.
- Small test: one example = 5 percentage points.
