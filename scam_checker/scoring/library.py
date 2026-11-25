"""RAG: look up similar listings in a checked library before the AI answers (Step 2).

The library (data/step2/rag_library.csv) holds short listings with their correct
yes / unclear answers, checked by hand. It never says "scam" or "genuine".
Before the AI answers, word matching (TF-IDF) finds the most similar listings and
puts them in the prompt with their correct answers.

Fairness rule: when testing on a practice example, the library never returns that
example or any other example from the same source.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

LIBRARY_FILE = Path("data/step2/rag_library.csv")


@dataclass(frozen=True)
class LibraryExample:
    id: str
    source: str
    text: str
    yes: tuple[str, ...]
    unclear: tuple[str, ...]


def _split(cell: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in cell.split(";") if part.strip())


class Library:
    def __init__(self, examples: list[LibraryExample]):
        self.examples = examples
        self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")
        self._matrix = self._vectorizer.fit_transform([example.text for example in examples])

    @classmethod
    def load(cls, path: Path = LIBRARY_FILE) -> Library:
        with path.open(encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))
        return cls(
            [LibraryExample(r["id"], r["source"], r["text"], _split(r["yes"]), _split(r["unclear"])) for r in rows]
        )

    def similar(
        self, listing: str, count: int = 3, skip_id: str | None = None, skip_source: str | None = None
    ) -> list[LibraryExample]:
        """The most similar library listings (by shared words), leaving out the tested example and its source."""
        scores = linear_kernel(self._vectorizer.transform([listing]), self._matrix)[0]
        ranked = sorted(range(len(self.examples)), key=lambda i: scores[i], reverse=True)
        found = []
        for i in ranked:
            example = self.examples[i]
            if scores[i] <= 0 or example.id == skip_id or (skip_source and example.source == skip_source):
                continue
            found.append(example)
            if len(found) == count:
                break
        return found
