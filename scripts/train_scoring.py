"""Train the Step 2 scoring step on one AI model's answers to the practice examples.

Usage (after the AI has answered the questions for every practice example):

1. Sensitivity analysis first: tries a false alarm cost of £10, £20 and £50 and
   prints how many scams are caught and how many false alarms there are for each,
   and saves the table and a chart as outputs/sensitivity_<model>.csv and .png:
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


DISPLAY_NAMES = {"qwen": "Qwen3.5 4B", "qwen25": "Qwen2.5-VL 3B"}
OUT = Path("outputs")


def print_sensitivity_analysis(rows, labels, groups, model_key: str) -> None:
    results = sensitivity_analysis(rows, labels, groups)
    print("Sensitivity analysis: how the false alarm cost changes the results (cross-validated)")
    print("False alarm cost | Warning level | Scams caught | False alarms | Cost per check")
    for cost, report in results:
        print(
            f"£{cost:<15g} | {report.warning_level:<13} | {report.scams_caught}/{report.scams_total:<10} "
            f"| {report.false_alarms}/{report.genuine_total:<10} | £{report.expected_cost_per_check_gbp}"
        )
    OUT.mkdir(exist_ok=True)
    print(f"Saved {save_sensitivity_table(results, model_key)}")
    print(f"Saved {save_sensitivity_chart(results, model_key)}")
    print("Pick one, write down why, then run again with --cost-false-alarm <your choice> to save the scoring.")


def save_sensitivity_table(results, model_key: str) -> Path:
    path = OUT / f"sensitivity_{model_key}.csv"
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["false_alarm_cost_gbp", "warning_level", "scams_caught", "scams_total", "false_alarms", "genuine_total",
             "cost_per_check_gbp"]
        )  # fmt: skip
        for cost, r in results:
            writer.writerow(
                [cost, r.warning_level, r.scams_caught, r.scams_total, r.false_alarms, r.genuine_total,
                 r.expected_cost_per_check_gbp]
            )  # fmt: skip
    return path


def save_sensitivity_chart(results, model_key: str) -> Path:
    """Scams caught and false alarms side by side at each false alarm cost (both as % of their group)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    caught_colour, alarm_colour = "#2a78d6", "#eb6834"  # validated categorical slots 1-2
    ink, muted, grid, surface = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"
    fig, ax = plt.subplots(figsize=(7, 3.6), facecolor=surface)
    width = 0.36
    for i, (_cost, r) in enumerate(results):
        caught = 100 * r.scams_caught / r.scams_total
        alarms = 100 * r.false_alarms / r.genuine_total
        for offset, value, colour, label in (
            (-width / 2, caught, caught_colour, f"{r.scams_caught}/{r.scams_total}"),
            (width / 2, alarms, alarm_colour, f"{r.false_alarms}/{r.genuine_total}"),
        ):
            ax.bar(i + offset, value, width - 0.04, color=colour, edgecolor=surface, linewidth=2)
            ax.text(i + offset, value + 2, label, ha="center", fontsize=8.5, color=ink)
    ax.set_xticks(range(len(results)), [f"£{cost:g}" for cost, _ in results])
    ax.set_ylim(0, 112)
    ax.set_ylabel("% of scams / % of genuine posts", fontsize=9, color=muted)
    ax.set_xlabel("Cost given to one false alarm (a missed scam costs £432)", fontsize=9, color=muted)
    ax.set_title(f"Sensitivity analysis: {DISPLAY_NAMES.get(model_key, model_key)}", loc="left", fontsize=11, color=ink)
    ax.set_facecolor(surface)
    ax.grid(axis="y", color=grid, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(grid)
    ax.tick_params(colors=muted, labelsize=9, length=0)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in (caught_colour, alarm_colour)]
    ax.legend(handles, ["Scams caught", "False alarms"], frameon=False, fontsize=8.5, loc="upper right", ncol=2)
    fig.text(0.01, 0.01, "Cross-validated on the same 157 practice examples.", fontsize=8, color=muted)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    path = OUT / f"sensitivity_{model_key}.png"
    fig.savefig(path, dpi=200, facecolor=surface)
    plt.close(fig)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--answers", type=Path, required=True)
    parser.add_argument("--cost-false-alarm", type=float, default=COST_FALSE_ALARM_GBP)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    rows, labels, groups = load_training_rows(args.answers)
    if args.cost_false_alarm is None:
        print_sensitivity_analysis(rows, labels, groups, args.answers.stem.removeprefix("answers_"))
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
