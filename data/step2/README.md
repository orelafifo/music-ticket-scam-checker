# Step 2 data: 200 examples and the locked test set

Made 23 Nov 2026 from the old v2 project data (`~/Documents/ticket_scam_checker/data`, 324 examples, no duplicates).

## Files
| File | Rows | What |
|---|---|---|
| `all_200_examples.csv` | 200 | Everything, with a `set` column (practice or test) |
| `practice_set.csv` | 160 | Use this to compare the 2 AI models and to build the scoring (music events only: 143 examples) |
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
- 14 practice examples are not music events (football, rugby, cricket, comedy, theatre). They are marked `music_event = no` and left out of every comparison and score (5 were added to that list on 24 Nov 2026). The model comparison uses the 143 music examples (74 scams, 69 genuine), leaving out the 3 private WhatsApp examples too.

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
- `practice_set.csv`: `db3a8ed3885e72ab9f0611ffb9ed4a4491bc880f93ea2c6760ef28f4a1139fde` (updated 24 Nov 2026: 5 rows re-marked as not music)
- `all_200_examples.csv`: `17ebd189f23aca4fb5f06126fd3e2c25481339c9a09131300f157e2e74307d50` (updated 24 Nov 2026, same change)

Check before the final test with: `shasum -a 256 data/step2/locked_test_set.csv`

## Known limits (for the report)
- Only 32 real word-for-word scams exist, so most scams are rebuilt.
- Every rebuilt example is a scam and every written example is genuine, so a model could learn writing style instead of warning signs. Using all real examples reduces this.
- Some texts include notes in [square brackets] about what happened later (e.g. "seller asked for more money"). A buyer would not see these in the listing.
- Small test: one example = 5 percentage points.
