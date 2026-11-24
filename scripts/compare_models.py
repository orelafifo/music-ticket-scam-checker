"""Step 2, part 5: compare the 2 AI models and save the charts for the report.

Run after each model has answered the questions (run_ai_answers.py) and its
scoring has been trained and saved (train_scoring.py --cost-false-alarm ...):
    python scripts/compare_models.py

Scams caught and false alarms are cross-validated: every example is judged by a
scoring step that never saw it (see docs/step2_judging_rules.md).

Saves in outputs/:
  step2_scams_caught.png          scams caught, per model
  step2_false_alarms.png          false alarms, per model
  step2_speed.png                 typical and slow-case seconds per check
  step2_energy.png                energy per check
  step2_model_comparison.png      all four charts in one image
  step2_warning_signs_<model>.png which warning signs matter most, for the winner
  step2_model_comparison.csv      the same numbers as a table
  step2_winner.txt                which model won and why, rule by rule
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from scam_checker.scoring.compare import ModelResult, pick_winner  # noqa: E402
from scam_checker.scoring.questions import find_question, questions_answered  # noqa: E402
from scam_checker.scoring.scorer import ScoringModel, train_scoring  # noqa: E402
from scripts.train_scoring import load_training_rows  # noqa: E402

MODELS = {"qwen": "Qwen3.5 4B", "qwen25": "Qwen2.5-VL 3B"}
# Colours: validated categorical slots 1-2 (blue, orange), text in ink colours.
COLOURS = {"qwen": "#2a78d6", "qwen25": "#eb6834"}
SCAM_SIGN, GOOD_SIGN = "#e34948", "#2a78d6"  # diverging pair for the weights chart
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"
OUT = Path("outputs")


def load_result(key: str) -> tuple[ModelResult, ScoringModel] | None:
    answers = Path(f"data/step2/answers_{key}.csv")
    summary_file, scoring_file = Path(f"data/step2/run_{key}.json"), Path(f"models/scoring_{key}.json")
    missing = [str(p) for p in (answers, summary_file, scoring_file) if not p.exists()]
    if missing:
        print(f"Skipping {MODELS[key]}: missing {', '.join(missing)}")
        return None
    summary, saved = json.loads(summary_file.read_text()), ScoringModel.load(scoring_file)
    rows, labels, groups = load_training_rows(answers)
    _, report = train_scoring(
        rows, labels, groups, cost_false_alarm=saved.costs["false_alarm_gbp"], questions=questions_answered(rows[0])
    )
    energy = summary.get("energy_kwh_per_check")
    return (
        ModelResult(
            name=MODELS[key],
            scams_caught=report.scams_caught,
            scams_total=report.scams_total,
            false_alarms=report.false_alarms,
            genuine_total=report.genuine_total,
            valid_percent=summary["valid_percent"],
            seconds_p50=summary["seconds_typical_p50"],
            seconds_p95=summary["seconds_slow_case_p95"],
            energy_wh_per_check=round(energy * 1000, 3) if energy is not None else None,
        ),
        saved,
    )


def style(ax, title: str, xlabel: str) -> None:
    ax.set_title(title, loc="left", fontsize=11, color=INK, pad=10)
    ax.set_xlabel(xlabel, fontsize=9, color=MUTED)
    ax.set_facecolor(SURFACE)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    for label in ax.get_yticklabels():
        label.set_color(INK)


def bars(ax, keys, values, labels, title, xlabel, xmax=None) -> None:
    y = range(len(keys))
    ax.barh(y, values, color=[COLOURS[k] for k in keys], height=0.55, edgecolor=SURFACE, linewidth=2)
    ax.set_yticks(list(y), [MODELS[k] for k in keys])
    ax.invert_yaxis()
    top = xmax or max(values) * 1.25 or 1
    ax.set_xlim(0, top)
    for i, (value, text) in enumerate(zip(values, labels, strict=True)):
        ax.text(value + top * 0.02, i, text, va="center", fontsize=9, color=INK)
    style(ax, title, xlabel)


def save(fig, name: str, note: str = "") -> Path:
    if note:
        fig.text(0.02, 0.02, note, fontsize=8, color=MUTED)
    path = OUT / name
    fig.savefig(path, dpi=200, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    return path


def new_chart():
    fig, ax = plt.subplots(figsize=(7, 3.2), facecolor=SURFACE)
    fig.subplots_adjust(left=0.2, right=0.95, top=0.82, bottom=0.25)
    return fig, ax


def comparison_charts(results: dict[str, ModelResult]) -> list[Path]:
    """Four separate PNGs, one per measure, all on the same 143 music examples."""
    keys, rows = list(results), list(results.values())
    cv_note = "Same 143 music practice examples for every model. Cross-validated."
    paths = []

    fig, ax = new_chart()
    bars(
        ax,
        keys,
        [100 * r.scams_caught / r.scams_total for r in rows],
        [f"{r.scams_caught}/{r.scams_total}" for r in rows],
        "Scams caught (higher is better)",
        "% of scams",
        xmax=110,
    )
    paths.append(save(fig, "step2_scams_caught.png", cv_note))

    fig, ax = new_chart()
    alarms = [100 * r.false_alarms / r.genuine_total for r in rows]
    bars(
        ax,
        keys,
        alarms,
        [f"{r.false_alarms}/{r.genuine_total}" for r in rows],
        "False alarms (lower is better)",
        "% of genuine posts",
        xmax=max(max(alarms) * 1.4, 10),
    )
    paths.append(save(fig, "step2_false_alarms.png", cv_note))

    fig, ax = new_chart()  # typical time as a dot, a line out to the slow-case time
    for i, (key, r) in enumerate(results.items()):
        ax.plot([r.seconds_p50, r.seconds_p95], [i, i], color=COLOURS[key], linewidth=2)
        ax.plot(r.seconds_p50, i, "o", color=COLOURS[key], markersize=8, markeredgecolor=SURFACE, markeredgewidth=2)
        label = f"{r.seconds_p50}s typical · {r.seconds_p95}s slow"
        ax.text(r.seconds_p95, i - 0.3, label, fontsize=8.5, color=INK, ha="right")
    ax.set_yticks(range(len(keys)), [MODELS[k] for k in keys])
    ax.set_ylim(len(keys) - 0.4, -0.75)
    ax.set_xlim(0, max(r.seconds_p95 for r in rows) * 1.15)
    style(ax, "Speed per check (dot = typical, line to slow case)", "seconds")
    paths.append(save(fig, "step2_speed.png", "Typical = p50 (half of checks are faster); slow case = p95."))

    with_energy = [k for k in keys if results[k].energy_wh_per_check is not None]
    if with_energy:
        fig, ax = new_chart()
        values = [results[k].energy_wh_per_check for k in with_energy]
        texts = [f"{v} Wh" for v in values]
        bars(ax, with_energy, values, texts, "Energy per check (lower is better)", "watt-hours")
        note = "Measured with codecarbon on the same MacBook Air."
        paths.append(save(fig, "step2_energy.png", note))
    return paths


def combined_chart(results: dict[str, ModelResult]) -> Path:
    """All four comparisons in one image: scams caught, false alarms, speed, energy."""
    keys, rows = list(results), list(results.values())
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.4), facecolor=SURFACE)
    fig.subplots_adjust(hspace=0.7, wspace=0.42, top=0.86, bottom=0.12, left=0.12, right=0.97)
    bars(
        axes[0][0],
        keys,
        [100 * r.scams_caught / r.scams_total for r in rows],
        [f"{r.scams_caught}/{r.scams_total}" for r in rows],
        "Scams caught (higher is better)",
        "% of scams",
        xmax=110,
    )
    alarms = [100 * r.false_alarms / r.genuine_total for r in rows]
    bars(
        axes[0][1],
        keys,
        alarms,
        [f"{r.false_alarms}/{r.genuine_total}" for r in rows],
        "False alarms (lower is better)",
        "% of genuine posts",
        xmax=max(max(alarms) * 1.4, 10),
    )
    ax = axes[1][0]
    for i, (key, r) in enumerate(results.items()):
        ax.plot([r.seconds_p50, r.seconds_p95], [i, i], color=COLOURS[key], linewidth=2)
        ax.plot(r.seconds_p50, i, "o", color=COLOURS[key], markersize=8, markeredgecolor=SURFACE, markeredgewidth=2)
        ax.text(r.seconds_p95, i - 0.3, f"{r.seconds_p50}s · {r.seconds_p95}s", fontsize=8.5, color=INK, ha="right")
    ax.set_yticks(range(len(keys)), [MODELS[k] for k in keys])
    ax.set_ylim(len(keys) - 0.4, -0.75)
    ax.set_xlim(0, max(r.seconds_p95 for r in rows) * 1.15)
    style(ax, "Speed per check (dot = typical, line to slow case)", "seconds")
    with_energy = [k for k in keys if results[k].energy_wh_per_check is not None]
    if with_energy:
        values = [results[k].energy_wh_per_check for k in with_energy]
        bars(
            axes[1][1],
            with_energy,
            values,
            [f"{v} Wh" for v in values],
            "Energy per check (lower is better)",
            "watt-hours",
        )
    else:
        axes[1][1].axis("off")
    fig.suptitle(
        "Qwen3.5 4B vs Qwen2.5-VL 3B on the same 143 music practice examples", x=0.02, ha="left", fontsize=13, color=INK
    )
    return save(
        fig,
        "step2_model_comparison.png",
        "Scams caught and false alarms are cross-validated. Energy measured with codecarbon.",
    )


def weights_chart(key: str, scoring: ScoringModel) -> Path:
    items = sorted(scoring.weights.items(), key=lambda item: item[1])
    fig, ax = plt.subplots(figsize=(9, 0.32 * len(items) + 1.4), facecolor=SURFACE)
    colours = [SCAM_SIGN if w > 0 else GOOD_SIGN for _, w in items]
    ax.barh(range(len(items)), [w for _, w in items], color=colours, height=0.6, edgecolor=SURFACE, linewidth=2)
    ax.set_yticks(
        range(len(items)), [re.split(r"[,(]", find_question(q).reason)[0].strip(" .") for q, _ in items], fontsize=8
    )
    ax.axvline(0, color=MUTED, linewidth=1)
    style(ax, f"Which warning signs matter most ({MODELS[key]})", "weight (right = points to a scam, left = genuine)")
    fig.tight_layout()
    path = OUT / f"step2_warning_signs_{key}.png"
    fig.savefig(path, dpi=200, facecolor=SURFACE)
    plt.close(fig)
    return path


def main() -> None:
    OUT.mkdir(exist_ok=True)
    loaded = {key: found for key in MODELS if (found := load_result(key))}
    if not loaded:
        raise SystemExit(
            "No model has answers and a saved scoring yet. Run run_ai_answers.py and train_scoring.py first."
        )
    results = {key: result for key, (result, _) in loaded.items()}

    winner, reasons = pick_winner(list(results.values()))
    (OUT / "step2_winner.txt").write_text(
        "\n".join([f"Winner: {winner.name if winner else 'none'}", *reasons]) + "\n", encoding="utf-8"
    )
    with (OUT / "step2_model_comparison.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(vars(next(iter(results.values())))))
        writer.writeheader()
        writer.writerows(vars(r) for r in results.values())

    for path in [*comparison_charts(results), combined_chart(results)]:
        print(f"Saved {path}")
    if winner:
        key = next(k for k, r in results.items() if r is winner)
        print(f"Saved {weights_chart(key, loaded[key][1])}")
    print("\n".join([f"Winner: {winner.name if winner else 'none'}", *reasons]))


if __name__ == "__main__":
    main()
