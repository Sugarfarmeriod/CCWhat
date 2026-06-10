"""BM25 retrieval for task segmentation."""

from __future__ import annotations

import math
import os
import re
from collections import Counter


def tokenize(text: str) -> list[str]:
    """Tokenize text for BM25.

    - English/identifiers: split on [A-Za-z0-9_]+, then further split tokens
      containing /.-_ separators.
    - File paths: keep full basename, stem (no extension), each directory segment.
    - Chinese: extract runs of CJK characters and produce 2-grams.
    - All tokens lowercased; tokens shorter than 2 characters are dropped.
    """
    tokens: list[str] = []

    # --- file path detection ---
    # A token looks like a path if it contains / or \ or ends with a known extension
    path_re = re.compile(r"(?:^|(?<=\s))(\.{0,2}[/\\][^\s]+|[^\s]+\.[a-zA-Z]{1,6}(?:/[^\s]*)?)")

    # Collect path-like substrings first to handle them specially
    path_tokens: set[str] = set()
    for m in path_re.finditer(text):
        raw = m.group(0)
        path_tokens.add(raw)
        # basename
        base = os.path.basename(raw.replace("\\", "/"))
        if base:
            tokens.append(base.lower())
        # stem (no extension)
        stem, _ = os.path.splitext(base)
        if stem and stem != base:
            tokens.append(stem.lower())
        # directory segments
        parts = raw.replace("\\", "/").split("/")
        for part in parts:
            part = part.strip()
            if len(part) >= 2:
                tokens.append(part.lower())

    # --- English/identifier tokens ---
    ident_re = re.compile(r"[A-Za-z0-9_]+")
    sep_re = re.compile(r"[/.\-_]")

    for m in ident_re.finditer(text):
        tok = m.group(0).lower()
        if len(tok) >= 2:
            tokens.append(tok)
        # further split on separator characters embedded in the token
        # (e.g. snake_case → ["snake", "case"])
        sub_parts = sep_re.split(tok)
        for part in sub_parts:
            if len(part) >= 2 and part != tok:
                tokens.append(part)

    # --- Chinese characters and 2-grams ---
    cjk_re = re.compile(r"[一-鿿㐀-䶿豈-﫿]+")
    for m in cjk_re.finditer(text):
        run = m.group(0)
        # individual characters (length 1 — skip per rule)
        # 2-grams
        for i in range(len(run) - 1):
            bigram = run[i : i + 2]
            tokens.append(bigram)
        # full run if length >= 2
        if len(run) >= 2:
            tokens.append(run)

    # deduplicate while preserving order, then filter length < 2
    seen: set[str] = set()
    result: list[str] = []
    for tok in tokens:
        tok = tok.lower()
        if len(tok) >= 2 and tok not in seen:
            seen.add(tok)
            result.append(tok)
    return result


class BM25:
    """In-memory BM25 scorer.

    Parameters
    ----------
    corpus:
        List of document strings.
    k1:
        Term frequency saturation parameter (default 1.5).
    b:
        Length normalization parameter (default 0.75).
    """

    def __init__(
        self,
        corpus: list[str],
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.k1 = k1
        self.b = b
        self.corpus = corpus
        self.n = len(corpus)

        # Tokenize all documents
        self._doc_tokens: list[list[str]] = [tokenize(doc) for doc in corpus]
        self._doc_freqs: list[Counter[str]] = [Counter(toks) for toks in self._doc_tokens]
        self._doc_lens: list[int] = [len(toks) for toks in self._doc_tokens]
        self._avgdl: float = (
            sum(self._doc_lens) / self.n if self.n > 0 else 0.0
        )

        # IDF: document frequency per term
        self._df: Counter[str] = Counter()
        for freq in self._doc_freqs:
            for term in freq:
                self._df[term] += 1

    def _idf(self, term: str) -> float:
        df = self._df.get(term, 0)
        return math.log((self.n - df + 0.5) / (df + 0.5) + 1)

    def score(self, query: str, doc_index: int) -> float:
        """Return BM25 score for *query* against document at *doc_index*."""
        if self.n == 0:
            return 0.0
        query_terms = tokenize(query)
        freq = self._doc_freqs[doc_index]
        dl = self._doc_lens[doc_index]
        score = 0.0
        for term in query_terms:
            tf = freq.get(term, 0)
            idf = self._idf(term)
            norm = tf * (self.k1 + 1) / (
                tf + self.k1 * (1 - self.b + self.b * dl / self._avgdl)
            )
            score += idf * norm
        return score

    def rank(self, query: str) -> list[tuple[int, float]]:
        """Return list of (doc_index, score) sorted by score descending."""
        scores = [(i, self.score(query, i)) for i in range(self.n)]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores
