"""Step 2 in the app, with a fake AI so Ollama doesn't need to be running."""

import json

import pytest

from scam_checker.context.seller import SellerSource
from scam_checker.local_ai import LocalAIError
from scam_checker.scoring.ask_ai import OllamaAsker
from scam_checker.scoring.library import Library, LibraryExample
from scam_checker.scoring.questions import QUESTION_IDS
from scam_checker.scoring.scorer import ScoringModel
from scam_checker.step1 import Step1Result
from scam_checker.step2 import SCORING_FILE, answer_questions, check_listing

from .fakes import fake_post

LIBRARY = Library([LibraryExample("E1", "A", "Bank transfer only, Oasis tickets", ("bank_transfer",), ())])
MODEL = ScoringModel(
    QUESTION_IDS, dict.fromkeys(QUESTION_IDS, 0.0) | {"bank_transfer": 2.0, "official_transfer": -1.5}, -1.0, 0.5
)


def reply(**yes) -> str:
    return json.dumps(dict.fromkeys(QUESTION_IDS, "no") | dict.fromkeys(yes, "yes"))


def step1(source=SellerSource.UNKNOWN) -> Step1Result:
    return Step1Result(artist="Oasis", where_found="", cleaned_text="Oasis tickets", seller_source=source)


def test_similar_listings_go_in_the_prompt():
    sent = []
    asker = OllamaAsker("qwen3.5:4b", post=fake_post(reply(bank_transfer=1), sent))
    answers = answer_questions("Oasis tickets, bank transfer please", asker, LIBRARY)
    assert answers.answers["bank_transfer"] == "yes"
    assert "Similar listings" in sent[0]["messages"][0]["content"]


def test_a_broken_reply_is_asked_again_then_stops_with_a_clear_message():
    sent = []
    with pytest.raises(LocalAIError, match="Check again"):
        answer_questions("Oasis tickets", OllamaAsker("qwen3.5:4b", post=fake_post("not json", sent)), LIBRARY)
    assert len(sent) == 2


def test_ai_answers_and_step1_points_add_up():
    answers = answer_questions("x", OllamaAsker("q", post=fake_post(reply(bank_transfer=1))), LIBRARY)
    alone = check_listing(step1(), answers, MODEL)
    stranger = check_listing(step1(SellerSource.OPEN_GROUP_CHAT), answers, MODEL)
    assert stranger.verdict.scam_probability > alone.verdict.scam_probability
    assert stranger.verdict.warning and stranger.verdict.reasons
    assert stranger.risk == "High" and 0 <= stranger.score_percent <= 100
    assert any("PayPal Goods and Services" in step for step in stranger.next_steps)
    assert any("Report Fraud" in step for step in stranger.next_steps)


def test_official_transfer_is_shown_as_a_good_sign():
    answers = answer_questions("x", OllamaAsker("q", post=fake_post(reply(official_transfer=1))), LIBRARY)
    check = check_listing(step1(), answers, MODEL)
    assert not check.verdict.warning and check.verdict.good_signs
    assert check.risk == "Low"
    assert not any("Report Fraud" in step for step in check.next_steps)


def test_event_mismatch_is_high_risk_and_says_why():
    from scam_checker.context.event_check import EventReport

    event = EventReport("Oasis", "Wembley", "2027-07-01", found=True, details_match=False, official_date="2027-07-02")
    answers = answer_questions("x", OllamaAsker("q", post=fake_post(reply(official_transfer=1))), LIBRARY)
    result = Step1Result(artist="Oasis", where_found="", cleaned_text="Oasis tickets", event=event)
    check = check_listing(result, answers, MODEL)
    assert check.risk == "High" and check.forced_by


def test_saved_scoring_matches_the_questions():
    if not SCORING_FILE.exists():
        pytest.skip("scoring not saved on this computer")
    assert ScoringModel.load(SCORING_FILE).question_ids == list(QUESTION_IDS), (
        "The saved scoring uses old questions: re-run train_scoring.py with --cost-false-alarm 20"
    )
