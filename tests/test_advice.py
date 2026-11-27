from scam_checker.advice import CLOSING, MAX_STEPS, PAY_SAFELY, next_steps
from scam_checker.scoring.step1_signals import Signal, Step1Signals


def yes(*questions):
    return dict.fromkeys(questions, "yes")


def test_at_most_4_steps_most_important_first():
    answers = yes("bank_transfer", "pressure_to_pay", "pdf_or_screenshot_ticket", "move_to_private_chat", "giveaway")
    signals = Step1Signals(found=[Signal("event_mismatch", 2.0, "x")])
    steps = next_steps(answers, signals, "High")
    assert len(steps) == MAX_STEPS
    assert steps[0].startswith("Check the date and venue")
    assert steps[1] == PAY_SAFELY


def test_low_risk_only_gets_the_basic_protections():
    assert next_steps(yes("sob_story", "official_transfer", "protected_payment"), Step1Signals(), "Low") == []
    assert next_steps(yes("sob_story"), Step1Signals(), "Low") == next_steps({}, Step1Signals(), "Low")


def test_every_risk_level_has_a_closing_line():
    assert "Report Fraud" in CLOSING["High"] and "looks OK" in CLOSING["Low"]
