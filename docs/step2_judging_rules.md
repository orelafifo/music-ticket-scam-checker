# Step 2: rules for judging the AI models

Written 23 Nov 2026, **before any testing**. Updated 24 Nov 2026 to the two models actually compared (see the dated notes at the bottom for why). These rules must not be changed after the first test run. If something has to change, add a dated note at the bottom saying what changed and why.

## The 2 models
| Model | Where it runs | Role |
|---|---|---|
| Qwen3.5 4B (newer) | Locally, on the MacBook Air (Ollama) | Can be chosen |
| Qwen2.5-VL 3B (older; already used in Step 1) | Locally, on the MacBook Air (Ollama) | Can be chosen |

## Test data
- `data/step2/practice_set.csv` (160 examples: 80 scams, 80 genuine).
- The locked test set is **not** used here.
- Both models get the same 143 music examples (74 scams, 69 genuine). Non-music examples (football, rugby, cricket, comedy, theatre) are left out, and the 3 examples from private WhatsApp group chats are kept aside for improving the winning model.

## Keeping it fair
- Every model gets the same prompt, the same yes/no questions and the same examples.
- Temperature 0 (or the lowest setting) so answers repeat.
- Both models run on the same MacBook Air, plugged in, with other apps closed.
- The models are compared **after** the scoring step is built, in this order:
  1. Write the yes/no questions.
  2. Run both models on the practice examples once and save their answers (speed and energy are measured here).
  3. Train the scoring step separately on each model's answers.
  4. Compare the models on scams caught and false alarms. These are measured with cross-validation: the scoring learns from 4/5 of the examples and is tested on the other 1/5, five times, so every example is judged by a scoring step that never saw it.

## What is measured
| # | Measure | What it means | How it is reported |
|---|---|---|---|
| 1 | **Scams caught** | Out of 77 scams, how many were flagged | Number and % |
| 2 | **False alarms** | Out of 80 genuine posts, how many were wrongly flagged | Number and % |
| 3 | **Valid answers** | How often the model replied in the right format (all questions answered yes/no) | % of examples |
| 4 | **Speed per check** | Seconds for one example | Typical time (p50: half of checks are faster than this) and slow-case time (p95: 95% of checks are faster than this). Not an average, because a few very slow checks would hide the usual time |
| 5 | **Privacy** | Does the text leave the device? | Both run locally: the text never leaves the device |
| 6 | **Cost** | Money per 1,000 checks | Both local: £0 in fees (electricity only, see energy) |
| 7 | **Energy** | Electricity per check | Measured with the free `codecarbon` library: kWh and grams of CO2 per check |

## How the winner is picked (decided now)
1. A model must give **valid answers at least 95% of the time**. Otherwise it is out.
2. The model that **catches more scams** wins.
3. If they are within 2 scams of each other (too close to call with 77 scams), the one with **fewer false alarms** wins.
4. If still within 2, the one with the **faster slow-case time (p95)** wins.
5. If still tied, the one that **uses less energy** wins.

## Small-sample warning
With 77 scams, one example is about 1.3 percentage points. Differences of 1–2 examples are within chance. Report numbers as "x out of 77", not only as %.

## Changes after this date
- 23 Nov 2026 (before any testing): dropped the temporary "2 or more yes = scam" rule. Models are now compared after each has its own trained scoring step.
- 23 Nov 2026 (before any testing): all 3 models are compared on the same examples (157 at the time; reduced to 143 music examples on 24 Nov, see below) (the 3 private WhatsApp examples are left out for every model, not only for Gemini).
- 24 Nov 2026 (after the Qwen run, before any scam-caught or false-alarm results were looked at): Gemma 4 E4B dropped. It needed 8.8 GiB of memory and the test MacBook Air had 4.8 GiB free (Ollama: "model requires 8.8 GiB but only 4.8 GiB are available"). The comparison is now Qwen3.5 4B (local, can win) against Gemini Flash (cloud, benchmark only). Qwen still has to pass rule 1 (at least 95% valid answers).
- 24 Nov 2026 (before any scam-caught or false-alarm results were looked at): Gemini stopped after 9 of 157 examples (Google's free-plan daily limit, error 429), so it can't be compared fairly. Qwen2.5-VL 3B (the model Step 1 already uses, 3.2 GB, fits in memory) is added as the second local model. The comparison is now Qwen3.5 4B against Qwen2.5-VL 3B, on the same 157 examples, with the same rules. Gemini's 9 answers are kept and reported as a partial test only.
- 24 Nov 2026 (after the first comparison, before the final test): the scoring now follows each question's direction from the sources (red flags can only add risk, good signs can only lower it; a question the data pushes the wrong way is set to 0). Reason: with 157 examples, "sad story", "meet outside the venue", "deposit" and "protected payment" were learned the wrong way round. Both models were re-scored with the same rule.
- 24 Nov 2026 (before running prompt version 2): target for context engineering, set in advance. Version 2 is kept only if, on the same 157 practice examples at £20, false alarms fall below 15% (12 of 80) without scams caught dropping below 60 of 77. Version 1 (as run on the MacBook Air): 67/77 caught, 26/80 false alarms.
- 24 Nov 2026 (before running prompt version 2): music events only. 14 practice examples that are not music (football, rugby, cricket, comedy, theatre) are left out of every score and comparison. Both models are compared on the same 143 music examples (74 scams, 69 genuine). The version 1 results and the target are re-calculated on these 143 before version 2 is run.
- 24 Nov 2026 (before running prompt version 2): target re-stated for the 143 music examples, same percentages as before. Version 2 is kept only if false alarms fall below 15% (10 of 69 or fewer) without scams caught dropping below 78% (58 of 74), at £20. Version 1 is re-measured on the MacBook Air on these 143 examples before version 2 is run.
- 25 Nov 2026 (after context engineering, before RAG was run): RAG added. A library of 36 practice listings (18 scams, 18 genuine) with hand-checked yes/unclear answers and no scam/genuine label (`data/step2/rag_library.csv`). Word matching (TF-IDF) puts the 3 most similar in the prompt. Fairness rule: the tested example and anything from the same source are never shown. At the same time, "sad story" now covers any personal story, and bank transfer offered only as an option next to an official transfer or protected payment is no. RAG is kept only if it beats context engineering (66/74 caught, 20/69 false alarms at £20).
- 26 Nov 2026 (after testing the app on one screenshot, before re-running): RAG copied answers from the similar listings (all 3 had a price, so the AI said a price was given when there wasn't one). Fixes: the prompt now says the similar listings only show how to apply the questions; 7 listings with no price added to the library (43 in total); "specific details" now means a seat, row, section, standing or festival ticket type, not just a date and venue. The 143 practice examples are re-run with RAG and the scoring is re-trained, so the reported results match what the app does. The earlier RAG results are in the git history.
- 26 Nov 2026 (re-run stopped after 4 of 15 replies were not valid, all missing "specific details"): "specific details" (clear_details) removed, as it had become the exact opposite of "no clear details" and the AI skipped it. 21 questions from now on. Earlier results (before, context engineering) were made with it and are not changed.
