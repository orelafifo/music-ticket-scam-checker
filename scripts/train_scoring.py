"""Train the Step 2 scoring step on one AI model's answers to the practice examples.

Usage (after the AI has answered the questions for every practice example):

1. Sensitivity analysis first: tries a false alarm cost of £10, £20 and £50 and
   prints how many scams are caught and how many false alarms there are for each:
       python scripts/train_scoring.py --answers data/step2/answers_qwen.csv

2. Then train and save the scoring with the cost you picked:
       python scripts/train_scoring.py --answers data/step2/answers_qwen.csv --cost-false-alarm 20

The answers file needs an `id` column (E001, E002, ... from practice_set.csv)
and one column per question, each holding yes / no / unclear.

Only practice examples are allowed. The script stops if it finds an example
from the locked test set.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scam_checker.scoring.questions import QUESTION_IDS  # noqa: E402
from scam_checker.scoring.scorer import COST_FALSE_ALARM_GBP, sensitivity_analysis, train_scoring  # noqa: E402

PRACTICE_FILE = Path("data/step2/practice_set.csv")
LOCKED_TEST_FILE = Path("data/step2/locked_test_set.csv")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def load_training_rows(answers_file: Path) -> tuple[list[dict[str, str]], list[int], list[str]]:
    practice = {row["id"]: row for row in read_csv(PRACTICE_FILE)}
    if not answers_file.exists():
        raise SystemExit(
            f"No answers file yet: {answers_file}\n"
            "The AI has to answer the questions for the practice examples first (Step 2, part 3)."
        )
    answers = read_csv(answers_file)
    missing_columns = [q for q in QUESTION_IDS if q not in answers[0]]
    if missing_columns:
        raise SystemExit(f"The answers file is missing these questions: {', '.join(missing_columns)}")
    if LOCKED_TEST_FILE.exists():
        locked_ids = {row["id"] for row in read_csv(LOCKED_TEST_FILE)}
        leaked = sorted(row["id"] for row in answers if row["id"] in locked_ids)
        if leaked:
            raise SystemExit(f"Stopped: these are locked test examples and must not be used: {', '.join(leaked)}")
    unknown = sorted(row["id"] for row in answers if row["id"] not in practice)
    if unknown:
        raise SystemExit(f"Stopped: these ids are not in the practice set: {', '.join(unknown)}")
    labels = [int(practice[row["id"]]["label"]) for row in answers]
    groups = [practice[row["id"]]["source"] or row["id"] for row in answers]
    return answers, labels, groups


def print_sensitivity_analysis(rows, labels, groups) -> None:
    print("Sensitivity analysis: how the false alarm cost changes the results (cross-validated)")
    print("False alarm cost | Warning level | Scams caught | False alarms | Cost per check")
    for cost, report in sensitivity_analysis(rows, labels, groups):
        print(
            f"£{cost:<15g} | {report.warning_level:<13} | {report.scams_caught}/{report.scams_total:<10} "
            f"| {report.false_alarms}/{report.genuine_total:<10} | £{report.expected_cost_per_check_gbp}"
        )
    print("Pick one, write down why, then run again with --cost-false-alarm <your choice> to save the scoring.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--answers", type=Path, required=True)
    parser.add_argument("--cost-false-alarm", type=float, default=COST_FALSE_ALARM_GBP)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    rows, labels, groups = load_training_rows(args.answers)
    if args.cost_false_alarm is None:
        print_sensitivity_analysis(rows, labels, groups)
        return
    out = args.out or Path("models") / f"scoring_{args.answers.stem.removeprefix('answers_')}.json"
    model, report = train_scoring(rows, labels, groups, args.cost_false_alarm, trained_on=str(args.answers))
    model.save(out)

    print(f"Saved: {out}")
    print(f"Warning level: {report.warning_level}")
    print(f"Scams caught:  {report.scams_caught}/{report.scams_total} (cross-validated)")
    print(f"False alarms:  {report.false_alarms}/{report.genuine_total} (cross-validated)")
    print(f"Expected cost per check: £{report.expected_cost_per_check_gbp}")
    print("Weights (biggest = strongest scam sign):")
    for question_id, weight in report.weights_strongest_first:
        print(f"  {weight:+.2f}  {question_id}")
    if report.wrong_direction:
        print(f"Check these: the data disagrees with their expected direction: {', '.join(report.wrong_direction)}")


if __name__ == "__main__":
    main()
