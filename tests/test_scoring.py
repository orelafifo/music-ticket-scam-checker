"""Tests for the Step 2 scoring step, using made-up answers (no AI needed)."""

from __future__ import annotations

import numpy as np
import pytest

from scam_checker.scoring.questions import QUESTION_IDS, QUESTIONS, Direction
from scam_checker.scoring.scorer import (
    ScoringModel,
    answers_to_numbers,
    choose_warning_level,
    expected_cost_per_check,
    train_scoring,
)


def made_up_answers(count: int = 120, seed: int = 1):
    """Scams usually ask for a bank transfer and payment first; genuine posts usually give a price."""
    rng = np.random.default_rng(seed)
    rows, labels, groups = [], [], []
    for i in range(count):
        scam = i % 2
        chance = {
            "bank_transfer": 0.8 if scam else 0.1,
            "pay_first": 0.7 if scam else 0.2,
            "sob_story": 0.4 if scam else 0.2,
            "move_to_private_chat": 0.6 if scam else 0.3,
            "price_given": 0.3 if scam else 0.8,
            "official_transfer": 0.05 if scam else 0.5,
        }
        rows.append({q: ("yes" if rng.random() < chance.get(q, 0.3) else "no") for q in QUESTION_IDS})
        labels.append(scam)
        groups.append(f"source{i % 30}")
    return rows, labels, groups


def test_only_yes_counts():
    assert answers_to_numbers({"a": "Yes", "b": "no", "c": "unclear"}, ["a", "b", "c", "d"]) == [1, 0, 0, 0]


def test_every_question_has_a_reason_and_direction():
    for question in QUESTIONS:
        assert question.reason and question.text.endswith("?")
        assert isinstance(question.direction, Direction)
    assert len(set(QUESTION_IDS)) == len(QUESTION_IDS)


def test_weights_learn_the_right_direction():
    model, report = train_scoring(*made_up_answers(), cost_false_alarm=20)
    assert model.weights["bank_transfer"] > 0
    assert model.weights["official_transfer"] < 0
    assert report.weights_strongest_first[0][1] >= report.weights_strongest_first[-1][1]
    assert report.scams_total == 60 and report.genuine_total == 60


def test_verdict_shows_strongest_reason_first_and_good_signs():
    model = ScoringModel(
        question_ids=["bank_transfer", "pay_first", "official_transfer"],
        weights={"bank_transfer": 2.0, "pay_first": 1.0, "official_transfer": -1.5},
        intercept=-1.0,
        warning_level=0.5,
    )
    verdict = model.verdict({"bank_transfer": "yes", "pay_first": "yes", "official_transfer": "yes"})
    assert verdict.reasons[0].startswith("The seller wants a bank transfer")
    assert len(verdict.reasons) == 2 and len(verdict.good_signs) == 1
    assert verdict.warning  # -1 + 2 + 1 - 1.5 = 0.5 -> probability 0.62
    assert "Why:" in verdict.summary()


def test_no_yes_answers_gives_no_reasons():
    model = ScoringModel(["bank_transfer"], {"bank_transfer": 2.0}, intercept=-2.0, warning_level=0.5)
    verdict = model.verdict({"bank_transfer": "unclear"})
    assert not verdict.warning and verdict.reasons == []


def test_expensive_misses_lower_the_warning_level():
    rows, labels, groups = made_up_answers()
    cheap_misses, _ = train_scoring(rows, labels, groups, cost_false_alarm=200, cost_missed_scam=10)
    costly_misses, _ = train_scoring(rows, labels, groups, cost_false_alarm=5, cost_missed_scam=1000)
    assert costly_misses.warning_level <= cheap_misses.warning_level


def test_cost_formula():
    # 5% scams; miss half of them (£432 each); 10% false alarms on the rest (£20 each)
    assert expected_cost_per_check(0.5, 0.1, 432, 20, 0.05) == pytest.approx(0.05 * 0.5 * 432 + 0.95 * 0.1 * 20)


def test_choose_level_perfect_split():
    probabilities = np.array([0.1, 0.2, 0.8, 0.9])
    level, cost = choose_warning_level(probabilities, np.array([0, 0, 1, 1]), 432, 20)
    assert 0.2 < level <= 0.8 and cost == 0


def test_save_and_load(tmp_path):
    model, _ = train_scoring(*made_up_answers(), cost_false_alarm=20)
    path = tmp_path / "scoring.json"
    model.save(path)
    assert ScoringModel.load(path) == model


def test_sensitivity_analysis_tries_each_cost():
    from scam_checker.scoring.scorer import sensitivity_analysis

    results = sensitivity_analysis(*made_up_answers(), false_alarm_costs=(10, 20, 50))
    assert [cost for cost, _ in results] == [10, 20, 50]
    levels = [report.warning_level for _, report in results]
    assert levels == sorted(levels)  # dearer false alarms -> the checker warns less readily


def test_a_red_flag_the_data_gets_wrong_is_set_to_zero():
    rows, labels, groups = made_up_answers()
    for row, label in zip(rows, labels, strict=True):  # make "sad story" appear mostly in genuine posts
        row["sob_story"] = "yes" if label == 0 else "no"
    model, report = train_scoring(rows, labels, groups, cost_false_alarm=20)
    assert model.weights["sob_story"] == 0
    assert "sob_story" in report.wrong_direction
    verdict = model.verdict(dict.fromkeys(model.question_ids, "no") | {"sob_story": "yes"})
    assert verdict.good_signs == [] and verdict.reasons == []


def test_every_weight_follows_its_direction():
    from scam_checker.scoring.questions import find_question

    model, _ = train_scoring(*made_up_answers(), cost_false_alarm=20)
    for question_id, weight in model.weights.items():
        sign = 1 if find_question(question_id).direction is Direction.RED_FLAG else -1
        assert weight * sign >= 0
