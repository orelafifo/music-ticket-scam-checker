"""Compare the 3 AI models and pick the winner, using the judging rules written before testing.

See docs/step2_judging_rules.md. Only the models that run on this computer can win;
Gemini is a benchmark. The rules, in order:
  1. valid answers at least 95% of the time, or the model is out;
  2. more scams caught wins;
  3. within 2 scams of each other -> fewer false alarms wins;
  4. still within 2 -> faster slow-case (p95) time wins;
  5. still tied -> less energy per check wins.
"""

from __future__ import annotations

from dataclasses import dataclass

MIN_VALID_PERCENT = 95.0
TOO_CLOSE = 2  # examples


@dataclass
class ModelResult:
    name: str
    runs_locally: bool
    scams_caught: int
    scams_total: int
    false_alarms: int
    genuine_total: int
    valid_percent: float
    seconds_p50: float
    seconds_p95: float
    energy_wh_per_check: float | None = None


def pick_winner(results: list[ModelResult]) -> tuple[ModelResult | None, list[str]]:
    """Returns the winner (or None) and the reasons, in plain words, for the report."""
    reasons = []
    candidates = []
    for result in results:
        if not result.runs_locally:
            reasons.append(f"{result.name} is a benchmark only (runs in the cloud), so it can't win.")
        elif result.valid_percent < MIN_VALID_PERCENT:
            reasons.append(f"{result.name} is out: valid answers {result.valid_percent}% (needs {MIN_VALID_PERCENT}%).")
        else:
            candidates.append(result)
    if not candidates:
        return None, reasons + ["No model passed rule 1."]
    if len(candidates) == 1:
        return candidates[0], reasons + [f"{candidates[0].name} is the only model left."]

    a, b = sorted(candidates, key=lambda r: -r.scams_caught)[:2]
    rules = [
        ("scams caught", a.scams_caught, b.scams_caught, True, TOO_CLOSE),
        ("false alarms", a.false_alarms, b.false_alarms, False, TOO_CLOSE),
        ("slow-case seconds (p95)", a.seconds_p95, b.seconds_p95, False, 0),
        ("energy per check", a.energy_wh_per_check or 0, b.energy_wh_per_check or 0, False, 0),
    ]
    for label, value_a, value_b, higher_is_better, margin in rules:
        if abs(value_a - value_b) > margin:
            better_a = value_a > value_b if higher_is_better else value_a < value_b
            winner, loser = (a, b) if better_a else (b, a)
            return winner, reasons + [
                f"{winner.name} wins on {label} ({_show(winner, label)} vs {_show(loser, label)})."
            ]
        reasons.append(f"Too close to call on {label}, so the next rule decides.")
    return a, reasons + [f"Still tied after every rule; {a.name} kept (more scams caught)."]


def _show(result: ModelResult, label: str) -> str:
    return {
        "scams caught": f"{result.scams_caught}/{result.scams_total}",
        "false alarms": f"{result.false_alarms}/{result.genuine_total}",
        "slow-case seconds (p95)": f"{result.seconds_p95}s",
        "energy per check": f"{result.energy_wh_per_check} Wh",
    }[label]
