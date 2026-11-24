"""Tests for picking the winning AI model with the judging rules."""

from __future__ import annotations

from scam_checker.scoring.compare import ModelResult, pick_winner


def result(name, caught, alarms, valid=99.0, p95=5.0, energy=0.1):
    return ModelResult(name, caught, 80, alarms, 80, valid, 2.0, p95, energy)


def test_more_scams_caught_wins():
    winner, reasons = pick_winner([result("Qwen", 70, 10), result("Qwen2.5", 60, 5)])
    assert winner.name == "Qwen" and "scams caught" in reasons[-1]


def test_within_two_scams_fewer_false_alarms_wins():
    winner, _ = pick_winner([result("Qwen", 70, 12), result("Qwen2.5", 69, 6)])
    assert winner.name == "Qwen2.5"


def test_then_speed_decides():
    winner, _ = pick_winner([result("Qwen", 70, 6, p95=9.0), result("Qwen2.5", 69, 7, p95=4.0)])
    assert winner.name == "Qwen2.5"


def test_too_few_valid_answers_is_out():
    winner, reasons = pick_winner([result("Qwen", 75, 3, valid=80.0), result("Qwen2.5", 60, 5)])
    assert winner.name == "Qwen2.5"
    assert any("Qwen is out" in reason for reason in reasons)
