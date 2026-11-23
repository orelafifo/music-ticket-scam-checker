# Step 2: rules for judging the 3 AI models

Written 23 Nov 2026, **before any testing**. These rules must not be changed after the first test run. If something has to change, add a dated note at the bottom saying what changed and why.

## The 3 models
| Model | Where it runs | Role |
|---|---|---|
| Qwen3.5 4B | Locally, on the MacBook Air (Ollama) | Can be chosen |
| Gemma 4 E4B | Locally, on the MacBook Air (Ollama) | Can be chosen |
| Gemini Flash (current version on the test day) | Google's cloud | Benchmark only: shows the best result a big cloud model gives. Not chosen, because the product must keep screenshots private (the bank hosts the model itself) |

## Test data
- `data/step2/practice_set.csv` (160 examples: 80 scams, 80 genuine).
- The locked test set is **not** used here.
- All 3 models get the same 157 examples (77 scams, 80 genuine). The 3 examples from private WhatsApp group chats are left out for every model, so Gemini never sees them and the comparison is equal. They are used later, when improving the winning model.

## Keeping it fair
- Every model gets the same prompt, the same yes/no questions and the same examples.
- Temperature 0 (or the lowest setting) so answers repeat.
- Both local models run on the same MacBook Air, plugged in, with other apps closed.
- The models are compared **after** the scoring step is built, in this order:
  1. Write the yes/no questions.
  2. Run all 3 models on the practice examples once and save their answers (speed and energy are measured here).
  3. Train the scoring step separately on each model's answers.
  4. Compare the models on scams caught and false alarms. These are measured with cross-validation: the scoring learns from 4/5 of the examples and is tested on the other 1/5, five times, so every example is judged by a scoring step that never saw it.

## What is measured
| # | Measure | What it means | How it is reported |
|---|---|---|---|
| 1 | **Scams caught** | Out of 77 scams, how many were flagged | Number and % |
| 2 | **False alarms** | Out of 80 genuine posts, how many were wrongly flagged | Number and % |
| 3 | **Valid answers** | How often the model replied in the right format (all questions answered yes/no) | % of examples |
| 4 | **Speed per check** | Seconds for one example | Typical time (p50: half of checks are faster than this) and slow-case time (p95: 95% of checks are faster than this). Not an average, because a few very slow checks would hide the usual time |
| 5 | **Privacy** | Does the text leave the device? | Local = stays on the device; Cloud = sent to Google |
| 6 | **Cost** | Money per 1,000 checks | Local: £0 in fees. Gemini: price list on the test day |
| 7 | **Energy** | Electricity per check | Measured with the free `codecarbon` library: kWh and grams of CO2 per check. For Gemini only an estimate is possible, because the work happens in Google's data centre. Say so in the report |

## How the winner is picked (decided now)
Only the two local models can win.

1. A model must give **valid answers at least 95% of the time**. Otherwise it is out.
2. The model that **catches more scams** wins.
3. If they are within 2 scams of each other (too close to call with 77 scams), the one with **fewer false alarms** wins.
4. If still within 2, the one with the **faster slow-case time (p95)** wins.
5. If still tied, the one that **uses less energy** wins.

Gemini's results are reported next to them, to show how much is gained or lost by staying local.

## Small-sample warning
With 77 scams, one example is about 1.3 percentage points. Differences of 1–2 examples are within chance. Report numbers as "x out of 77", not only as %.

## Changes after this date
- 23 Nov 2026 (before any testing): dropped the temporary "2 or more yes = scam" rule. Models are now compared after each has its own trained scoring step.
- 23 Nov 2026 (before any testing): all 3 models are compared on the same 157 examples (the 3 private WhatsApp examples are left out for every model, not only for Gemini).
