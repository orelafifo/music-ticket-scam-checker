"""List the scoring's mistakes on the practice examples: false alarms and missed scams.

Usage (after train_scoring.py has saved the scoring for this answers file):
    python scripts/list_mistakes.py --answers data/step2/answers_qwen.csv

Uses the same cross-validation as train_scoring.py, so the counts match its table.
Prints the mistakes in the terminal (practice examples only; nothing is saved).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from scam_checker.scoring.ask_ai import remove_bracket_notes  # noqa: E402
from scam_checker.scoring.questions import Direction, questions_answered  # noqa: E402
from scam_checker.scoring.scorer import (  # noqa: E402
    ScoringModel,
    answers_to_numbers,
    choose_warning_level,
    cross_validated_probabilities,
)
from scripts.train_scoring import PRACTICE_FILE, load_training_rows, read_csv  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--answers", type=Path, required=True)
    args = parser.parse_args()
    key = args.answers.stem.removeprefix("answers_")
    scoring_file = Path(f"models/scoring_{key}.json")
    if not scoring_file.exists():
        raise SystemExit(
            f"Save the scoring first: python scripts/train_scoring.py --answers {args.answers} --cost-false-alarm 20"
        )

    saved = ScoringModel.load(scoring_file)
    rows, labels, groups = load_training_rows(args.answers)
    questions = questions_answered(rows[0])
    ids = [q.id for q in questions]
    x = np.array([answers_to_numbers(row, ids) for row in rows])
    y = np.array(labels)
    signs = np.array([1 if q.direction is Direction.RED_FLAG else -1 for q in questions])
    probabilities = cross_validated_probabilities(x, y, groups, signs)
    costs = saved.costs
    level, _ = choose_warning_level(
        probabilities, y, costs["missed_scam_gbp"], costs["false_alarm_gbp"], costs["scam_rate"]
    )

    practice = {row["id"]: row for row in read_csv(PRACTICE_FILE)}
    mistakes = []
    for row, label, probability in zip(rows, labels, probabilities, strict=True):
        warned = probability >= level
        if warned == bool(label):
            continue
        mistakes.append(
            {
                "mistake": "false alarm" if warned else "missed scam",
                "id": row["id"],
                "score": round(float(probability), 2),
                "yes_answers": ", ".join(q for q in ids if row[q] == "yes"),
                "tag": practice[row["id"]]["tag"],
                "text": remove_bracket_notes(practice[row["id"]]["text"]),
            }
        )
    mistakes.sort(key=lambda m: (m["mistake"], -m["score"]))

    print(f"Warning level {level} (false alarm cost £{costs['false_alarm_gbp']:g})")
    for kind in ("false alarm", "missed scam"):
        group = [m for m in mistakes if m["mistake"] == kind]
        print(f"\n{kind.upper()}S: {len(group)}")
        for m in group:
            print(f"- {m['id']} (score {m['score']}) {m['text'][:110]}")
            print(f"    yes: {m['yes_answers'] or 'nothing'}")


if __name__ == "__main__":
    main()
