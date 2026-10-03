"""Keyword retrieval (BM25), with no model and no extra dependency.

It is the right first step: explainable, instant, and good enough on a curated corpus. When
paraphrased questions start to miss, add embeddings from a local model (for example
`nomic-embed-text` through Ollama) and fuse the two rankings; policy-evidence-mcp shows how.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from .documents import Passage

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "do",
    "does",
    "for",
    "from",
    "has",
    "have",
    "how",
    "i",
    "if",
    "in",
    "is",
    "it",
    "its",
    "may",
    "my",
    "of",
    "on",
    "or",
    "our",
    "should",
    "that",
    "the",
    "their",
    "there",
    "this",
    "to",
    "was",
    "we",
    "what",
    "when",
    "where",
    "which",
    "who",
    "will",
    "with",
    "you",
    "your",
}


def tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w[:-1] if len(w) > 4 and w.endswith("s") else w for w in words if w not in STOPWORDS]


class Index:
    def __init__(self, passages: list[Passage], k1: float = 1.5, b: float = 0.75):
        self.passages = passages
        self.k1, self.b = k1, b
        self.docs = [Counter(tokens(f"{p.title} {p.heading} {p.text}")) for p in passages]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg = sum(self.lengths) / len(self.lengths) if self.lengths else 0.0
        df = Counter(term for d in self.docs for term in d)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def search(self, query: str, k: int = 4, min_score: float = 0.0) -> list[tuple[Passage, float]]:
        terms = tokens(query)
        scored = []
        for i, doc in enumerate(self.docs):
            score = 0.0
            for t in terms:
                if t in doc:
                    tf = doc[t]
                    norm = 1 - self.b + self.b * self.lengths[i] / (self.avg or 1)
                    score += self.idf[t] * tf * (self.k1 + 1) / (tf + self.k1 * norm)
            if score > min_score:
                scored.append((self.passages[i], round(score, 3)))
        scored.sort(key=lambda x: (-x[1], x[0].id))
        return scored[:k]
