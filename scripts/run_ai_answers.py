"""Step 2, part 3: let one AI model answer the yes/no questions for every practice example.

Usage (one model at a time; the Ollama app must be open):
    python scripts/run_ai_answers.py --model qwen
    python scripts/run_ai_answers.py --model qwen25

Try a few first:   python scripts/run_ai_answers.py --model qwen --limit 3
With RAG (similar listings from data/step2/rag_library.csv in the prompt):
    python scripts/run_ai_answers.py --model qwen --rag

Saves after every example, so you can stop with Ctrl + C and run the same
command again later: it carries on where it stopped.

Writes:
  data/step2/answers_<model>.csv   one row per example: the answers, valid or not, seconds
  data/step2/run_<model>.json      valid %, typical (p50) and slow-case (p95) seconds, energy per check

Only the practice set is used, never the locked test set. Both models answer the
same 143 music examples (74 scams + 69 genuine): non-music examples (football,
rugby, theatre...) are skipped, and the 3 private WhatsApp group-chat examples are
kept for later, when improving the winning model.
Notes in [square brackets] that a buyer would not see are removed before asking.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

from scam_checker.scoring.ask_ai import (  # noqa: E402  # noqa: E402
    MODELS,
    PROMPT_VERSION,
    V1_QUESTIONS,
    make_asker,
    parse_reply,
    prompt_for,
    remove_bracket_notes,
)
from scam_checker.scoring.library import Library  # noqa: E402
from scam_checker.scoring.questions import QUESTIONS, find_question  # noqa: E402

PRACTICE_FILE = Path("data/step2/practice_set.csv")
PRIVATE_SOURCE = "Open WhatsApp group chats"  # Orela's own examples: kept for improving the winner


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def percentile(values: list[float], share: float) -> float:
    ordered = sorted(values)
    return round(ordered[min(len(ordered) - 1, int(share * len(ordered)))], 2)


def ask_with_retries(asker, prompt: str, attempts: int = 3) -> tuple[str, float]:
    """If the model doesn't reply in time, wait and try again.

    Only the attempt that worked is timed, so a dropped connection isn't counted as the model being slow.
    """
    for attempt in range(1, attempts + 1):
        started = time.perf_counter()
        try:
            return asker.ask(prompt), time.perf_counter() - started
        except (requests.Timeout, requests.ConnectionError) as error:
            if attempt == attempts:
                raise SystemExit(
                    f"No reply after {attempts} tries ({error.__class__.__name__}). "
                    "Everything so far is saved: run the same command again later to carry on."
                ) from error
            print(f"    no reply (try {attempt} of {attempts}), waiting 30 seconds...")
            time.sleep(30)
    raise AssertionError("unreachable")


def start_energy_meter(model: str):
    try:
        from codecarbon import OfflineEmissionsTracker
    except ImportError:
        print("codecarbon isn't installed, so energy won't be measured (pip install codecarbon).")
        return None
    tracker = OfflineEmissionsTracker(country_iso_code="GBR", project_name=f"step2-{model}", log_level="error")
    tracker.start()
    return tracker


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", choices=list(MODELS), required=True)
    parser.add_argument("--limit", type=int, default=None, help="only do this many new examples (for a quick try)")
    parser.add_argument(
        "--prompt", type=int, choices=[1, 2], default=PROMPT_VERSION, help="prompt version (default: 2)"
    )
    parser.add_argument("--rag", action="store_true", help="add 3 similar listings from the checked library")
    args = parser.parse_args()
    if args.rag and args.prompt == 1:
        raise SystemExit("RAG is only used with prompt version 2.")
    library = Library.load() if args.rag else None

    examples = read_rows(PRACTICE_FILE)
    examples = [row for row in examples if PRIVATE_SOURCE not in row["source"]]  # same set for every model
    examples = [row for row in examples if row["music_event"] == "yes"]  # music events only (no football, theatre...)
    suffix = "_rag" if args.rag else "" if args.prompt == 1 else f"_v{args.prompt}"  # version 1 keeps its names
    out_file = Path(f"data/step2/answers_{args.model}{suffix}.csv")
    questions = tuple(find_question(q) for q in V1_QUESTIONS) if args.prompt == 1 else QUESTIONS
    columns = ["id", *(q.id for q in questions), "valid", "seconds"]
    done = {row["id"] for row in read_rows(out_file)} if out_file.exists() else set()
    to_do = [row for row in examples if row["id"] not in done][: args.limit]
    label = "RAG" if args.rag else f"prompt version {args.prompt}"
    print(f"{args.model} ({label}): {len(done)} done already, {len(to_do)} to do now.")
    if not to_do:
        return

    asker = make_asker(args.model)
    print("Warming up (loading the model into memory; not timed)...")
    asker.ask(
        prompt_for("Warm-up: 1 ticket for sale.", version=args.prompt)
    )  # the first call loads the model, which isn't fair to time
    new_file = not out_file.exists()
    seconds, tracker = [], start_energy_meter(args.model)
    with out_file.open("a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        if new_file:
            writer.writeheader()
        for number, row in enumerate(to_do, start=1):
            listing = remove_bracket_notes(row["text"])
            # Fairness rule: never show the tested example, or anything from the same source.
            similar = library.similar(listing, skip_id=row["id"], skip_source=row["source"]) if library else None
            prompt = prompt_for(listing, questions, version=args.prompt, similar=similar)
            reply, took = ask_with_retries(asker, prompt)
            result = parse_reply(reply, questions)
            writer.writerow({"id": row["id"], **result.answers, "valid": result.valid, "seconds": round(took, 2)})
            file.flush()
            seconds.append(took)
            print(f"  {number}/{len(to_do)} {row['id']}  {took:.1f}s  {'ok' if result.valid else 'NOT VALID'}")
    energy_kwh = tracker.stop() if tracker else None  # codecarbon returns kg CO2; energy is on the tracker

    all_rows = read_rows(out_file)
    summary = {
        "model": MODELS[args.model],
        "prompt_version": args.prompt,
        "rag": args.rag,
        "examples_answered": len(all_rows),
        "valid_percent": round(100 * sum(r["valid"] == "True" for r in all_rows) / len(all_rows), 1),
        "seconds_typical_p50": percentile([float(r["seconds"]) for r in all_rows], 0.50),
        "seconds_slow_case_p95": percentile([float(r["seconds"]) for r in all_rows], 0.95),
        "seconds_mean_this_session": round(statistics.mean(seconds), 2),
        "where_it_runs": "this computer",
    }
    if tracker:
        data = tracker.final_emissions_data
        summary["energy_kwh_per_check"] = round(data.energy_consumed / len(seconds), 6)
        summary["co2_grams_per_check"] = round(1000 * data.emissions / len(seconds), 4)
    Path(f"data/step2/run_{args.model}{suffix}.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    del energy_kwh


if __name__ == "__main__":
    main()
