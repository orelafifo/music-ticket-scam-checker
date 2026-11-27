"""Step 2 in the app: the cleaned listing in, a verdict with reasons out.

1. RAG: find the 3 most similar listings in the checked library.
2. The AI (Qwen3.5 4B, on this computer) answers the 21 yes/no questions about the
   cleaned listing, with the worked examples and the similar listings in the prompt.
   It never says "scam": it only reads and answers.
3. The saved scoring turns the answers into a score, adds the Step 1 points
   (how you met the seller, where you found the tickets, the account, the website
   and event checks) and gives the verdict, the reasons, good signs and tips.

Only the cleaned text is used: personal details were removed in Step 1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .advice import closing_line, next_steps
from .local_ai import LocalAIError
from .scoring.ask_ai import AIAnswers, OllamaAsker, parse_reply, prompt_for
from .scoring.library import Library
from .scoring.questions import QUESTIONS
from .scoring.scorer import ScoringModel, Verdict
from .scoring.step1_signals import step1_signals
from .step1 import Step1Result

SCORING_FILE = Path("models/scoring_qwen_rag.json")
STEP2_MODEL = "qwen3.5:4b"
ATTEMPTS = 2  # ask again once if the reply is broken
# Medium risk starts at the warning level the sensitivity analysis chose for a £10 false alarm
# (outputs/sensitivity_qwen_rag.csv): a listing the checker would warn about if false alarms cost less.
MEDIUM_RISK_FROM = 0.42


def answer_questions(cleaned_text: str, asker: OllamaAsker, library: Library) -> AIAnswers:
    similar = library.similar(cleaned_text)  # real use: nothing is left out
    prompt = prompt_for(cleaned_text, QUESTIONS, similar=similar)
    for _ in range(ATTEMPTS):
        try:
            result = parse_reply(asker.ask(prompt), QUESTIONS)
        except RuntimeError as error:
            raise LocalAIError(str(error)) from error
        if result.valid:
            return result
    raise LocalAIError("The AI's answer was incomplete. Please press Check again.")


@dataclass
class CheckResult:
    verdict: Verdict
    risk: str  # "High", "Medium" or "Low"
    score_percent: int
    forced_by: list[str] = field(default_factory=list)  # reasons that always give a warning (event check, blocklist)
    next_steps: list[str] = field(default_factory=list)
    closing: str = ""


def risk_level(verdict: Verdict, warning_level: float) -> str:
    if verdict.warning or verdict.scam_probability >= warning_level:
        return "High"
    return "Medium" if verdict.scam_probability >= MEDIUM_RISK_FROM else "Low"


def check_listing(step1: Step1Result, answers: AIAnswers, scoring: ScoringModel) -> CheckResult:
    signals = step1_signals(step1)
    verdict = scoring.verdict(answers.answers, signals)
    forced = []
    if signals.always_warn and verdict.scam_probability < scoring.warning_level:
        forced = [s.reason for s in signals.found if s.id in {"event_mismatch", "format_mismatch", "on_blocklist"}]
    risk = risk_level(verdict, scoring.warning_level)
    return CheckResult(
        verdict=verdict,
        risk=risk,
        score_percent=round(100 * verdict.scam_probability),
        forced_by=forced,
        next_steps=next_steps(answers.answers, signals, risk),
        closing=closing_line(risk),
    )
