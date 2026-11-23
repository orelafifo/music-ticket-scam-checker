"""Step 2 scoring: turn the AI's yes/no answers into a verdict with reasons.

How it works:
- Each question answered "yes" counts as 1; "no" and "unclear" count as 0.
- Logistic regression gives each question a weight. The weights are learned
  from the practice examples, so they show which warning signs matter most.
  A bigger weight means the sign is stronger evidence of a scam; a negative
  weight means it is evidence of a genuine sale.
- The weights turn the answers into a scam probability (0 to 1).
- A warning is shown when the probability is at or above the warning level.
  The warning level is chosen by cost: a missed scam (money lost) against a
  false alarm (a genuine seller doubted, the customer's trust in the check).
- Step 1 answers (how you met the seller, where you found the tickets, the
  seller's account, the website check) add fixed points on top. See
  step1_signals.py and docs/step2_step1_weights.md.
- The user sees the reasons: the warning signs found (from the AI answers and
  from Step 1), strongest first, and any good signs.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold

from .questions import QUESTIONS, Direction, Question, find_question
from .step1_signals import Step1Signals

# Costs used to choose the warning level.
COST_MISSED_SCAM_GBP = 215  # average loss per concert ticket scam (Lloyds, see report log)
COST_FALSE_ALARM_GBP: float | None = None  # NOT DECIDED YET: Orela chooses this before training
REAL_WORLD_SCAM_RATE = 0.05  # assumed share of checked listings that are scams (5%)

LEVELS_TO_TRY = np.round(np.arange(0.05, 0.96, 0.01), 2)


def answers_to_numbers(answers: dict[str, str], question_ids: list[str]) -> list[float]:
    """'yes' -> 1, anything else ('no', 'unclear', missing) -> 0."""
    return [1.0 if str(answers.get(question_id, "")).strip().lower() == "yes" else 0.0 for question_id in question_ids]


@dataclass
class Verdict:
    warning: bool
    scam_probability: float
    reasons: list[str] = field(default_factory=list)  # red flags found, strongest first
    good_signs: list[str] = field(default_factory=list)
    tips: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """Plain-English text for the app."""
        headline = "Warning: this looks like a scam." if self.warning else "No strong scam signs found."
        lines = [headline]
        if self.reasons:
            lines.append("Why:")
            lines += [f"- {reason}" for reason in self.reasons]
        if self.good_signs:
            lines.append("Good signs:")
            lines += [f"- {sign}" for sign in self.good_signs]
        if self.tips:
            lines.append("Tip:")
            lines += [f"- {tip}" for tip in self.tips]
        return "\n".join(lines)


@dataclass
class ScoringModel:
    """The trained scoring step. Saved as readable JSON so the weights can be checked."""

    question_ids: list[str]
    weights: dict[str, float]
    intercept: float
    warning_level: float
    trained_on: str = ""
    costs: dict[str, float] = field(default_factory=dict)

    def scam_probability(self, answers: dict[str, str], step1: Step1Signals | None = None) -> float:
        """AI answers (learned weights) plus Step 1 answers (fixed points), turned into 0 to 1."""
        values = answers_to_numbers(answers, self.question_ids)
        total = self.intercept + sum(self.weights[q] * v for q, v in zip(self.question_ids, values, strict=True))
        if step1 is not None:
            total += step1.total_points
        return float(1 / (1 + np.exp(-total)))

    def verdict(self, answers: dict[str, str], step1: Step1Signals | None = None) -> Verdict:
        step1 = step1 or Step1Signals()
        probability = self.scam_probability(answers, step1)
        values = answers_to_numbers(answers, self.question_ids)
        # (points, reason) for every sign found, from the AI answers and from Step 1
        found = [
            (self.weights[q], find_question(q).reason) for q, v in zip(self.question_ids, values, strict=True) if v
        ]
        found += [(signal.points, signal.reason) for signal in step1.found]
        red = [reason for points, reason in sorted(found, key=lambda item: -item[0]) if points > 0]
        good = [reason for points, reason in sorted(found, key=lambda item: item[0]) if points < 0]
        return Verdict(
            warning=step1.always_warn or probability >= self.warning_level,
            scam_probability=round(probability, 3),
            reasons=red,
            good_signs=good,
            tips=list(step1.tips),
        )

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> ScoringModel:
        return cls(**json.loads(Path(path).read_text(encoding="utf-8")))


@dataclass
class TrainingReport:
    warning_level: float
    scams_caught: int  # measured with cross-validation (on examples the scoring had not learned from)
    scams_total: int
    false_alarms: int
    genuine_total: int
    expected_cost_per_check_gbp: float
    weights_strongest_first: list[tuple[str, float]]
    wrong_direction: list[str]  # questions whose learned weight disagrees with their direction


def expected_cost_per_check(
    miss_rate: float, false_alarm_rate: float, cost_missed_scam: float, cost_false_alarm: float, scam_rate: float
) -> float:
    """Average cost of one check in the real world, where only `scam_rate` of listings are scams."""
    return scam_rate * miss_rate * cost_missed_scam + (1 - scam_rate) * false_alarm_rate * cost_false_alarm


def choose_warning_level(
    probabilities: np.ndarray,
    labels: np.ndarray,
    cost_missed_scam: float,
    cost_false_alarm: float,
    scam_rate: float = REAL_WORLD_SCAM_RATE,
) -> tuple[float, float]:
    """Try warning levels from 0.05 to 0.95 and keep the cheapest. Returns (level, cost per check).

    On a tie the lower level wins, because missing a scam is the worse mistake.
    """
    scams, genuine = labels == 1, labels == 0
    best_level, best_cost = 0.5, float("inf")
    for level in LEVELS_TO_TRY:
        flagged = probabilities >= level
        miss_rate = float(np.mean(~flagged[scams])) if scams.any() else 0.0
        false_alarm_rate = float(np.mean(flagged[genuine])) if genuine.any() else 0.0
        cost = expected_cost_per_check(miss_rate, false_alarm_rate, cost_missed_scam, cost_false_alarm, scam_rate)
        if cost < best_cost - 1e-12:
            best_level, best_cost = float(level), cost
    return best_level, best_cost


def cross_validated_probabilities(x: np.ndarray, y: np.ndarray, groups: list[str], folds: int = 5) -> np.ndarray:
    """Scam probability for every example, each from a model that never saw that example.

    Examples from the same source are kept in the same fold, so the scoring is
    always tested on sources it has not learned from.
    """
    probabilities = np.zeros(len(y))
    splitter = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=2026)
    for train_rows, test_rows in splitter.split(x, y, groups):
        model = LogisticRegression(C=1.0, max_iter=1000).fit(x[train_rows], y[train_rows])
        probabilities[test_rows] = model.predict_proba(x[test_rows])[:, 1]
    return probabilities


def train_scoring(
    answer_rows: list[dict[str, str]],
    labels: list[int],
    groups: list[str],
    cost_false_alarm: float,
    cost_missed_scam: float = COST_MISSED_SCAM_GBP,
    scam_rate: float = REAL_WORLD_SCAM_RATE,
    questions: tuple[Question, ...] = QUESTIONS,
    trained_on: str = "",
) -> tuple[ScoringModel, TrainingReport]:
    question_ids = [question.id for question in questions]
    x = np.array([answers_to_numbers(row, question_ids) for row in answer_rows])
    y = np.array(labels)

    # 1. Choose the warning level from cross-validated probabilities (fair: unseen examples).
    probabilities = cross_validated_probabilities(x, y, groups)
    level, cost = choose_warning_level(probabilities, y, cost_missed_scam, cost_false_alarm, scam_rate)
    flagged = probabilities >= level

    # 2. Learn the final weights from all practice examples.
    final = LogisticRegression(C=1.0, max_iter=1000).fit(x, y)
    weights = {q: round(float(w), 3) for q, w in zip(question_ids, final.coef_[0], strict=True)}

    wrong_direction = [
        q.id
        for q in questions
        if (q.direction is Direction.RED_FLAG and weights[q.id] < 0)
        or (q.direction is Direction.GOOD_SIGN and weights[q.id] > 0)
    ]
    model = ScoringModel(
        question_ids=question_ids,
        weights=weights,
        intercept=round(float(final.intercept_[0]), 3),
        warning_level=level,
        trained_on=trained_on,
        costs={"missed_scam_gbp": cost_missed_scam, "false_alarm_gbp": cost_false_alarm, "scam_rate": scam_rate},
    )
    report = TrainingReport(
        warning_level=level,
        scams_caught=int(flagged[y == 1].sum()),
        scams_total=int((y == 1).sum()),
        false_alarms=int(flagged[y == 0].sum()),
        genuine_total=int((y == 0).sum()),
        expected_cost_per_check_gbp=round(cost, 2),
        weights_strongest_first=sorted(weights.items(), key=lambda item: -item[1]),
        wrong_direction=wrong_direction,
    )
    return model, report


FALSE_ALARM_COSTS_TO_TRY_GBP = (10, 20, 50)


def sensitivity_analysis(
    answer_rows: list[dict[str, str]],
    labels: list[int],
    groups: list[str],
    false_alarm_costs: tuple[float, ...] = FALSE_ALARM_COSTS_TO_TRY_GBP,
) -> list[tuple[float, TrainingReport]]:
    """Train the scoring once per false alarm cost, to show how the choice changes the results.

    The cost of a false alarm has no published figure, so instead of guessing one
    value, several are tried and the results compared. One is then picked, with a reason.
    """
    return [(cost, train_scoring(answer_rows, labels, groups, cost_false_alarm=cost)[1]) for cost in false_alarm_costs]
