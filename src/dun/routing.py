"""Offline lexical router for natural-language task requests (PL + EN).

Vendored and adapted from uritime/autonom ``src/autonom/registry.py`` (Apache-2.0):
- ``fold`` (lowercase + diacritic stripping, ``ł`` -> ``l``),
- ``tokens`` tokenization avoiding substring false-positives (``api`` in ``zapisz``),
- BM25-lite scoring with 5-char prefix rule + 4-char short Polish stem rule,
- precomputed inverted postings index per router,
- deterministic tie-breaking on ``(-round(score, 9), -priority, route_id)``.
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

__all__ = [
    "fold",
    "tokens",
    "Route",
    "LexicalRouter",
    "keyword_hits",
    "TASK_TYPE_KEYWORDS",
    "TASK_TYPE_PRIORITY",
    "LIBRARY_KEYWORDS",
    "LIBRARY_PRIORITY",
    "task_router",
    "library_router",
    "autonom_available",
]

_SPLIT = re.compile(r"[^a-z0-9]+")
PREFIX_LEN = 5
STEM_MIN = 4
STEM_MAX_SUFFIX = 4
PREFIX_WEIGHT = 0.6


def fold(text: str) -> str:
    """Lowercase and strip diacritics so Polish inflections compare cleanly."""
    text = text.replace("ł", "l").replace("Ł", "L")
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def tokens(text: str) -> list[str]:
    """Tokenize folded text into alphanumeric tokens of length >= 2."""
    return [tok for tok in _SPLIT.split(fold(text)) if len(tok) > 1]


def autonom_available() -> bool:
    """Return True when optional oqlos-autonom registry is importable."""
    try:
        import autonom.registry  # noqa: F401
    except ImportError:
        return False
    return True


@dataclass
class Route:
    """Single routing entry indexed by ``LexicalRouter``."""

    id: str
    keywords: Sequence[str]
    priority: int = 0
    successes: int = 0
    failures: int = 0
    doc: list[str] = field(default_factory=list)

    @property
    def reliability(self) -> float:
        """Laplace-smoothed historical execution reliability."""
        return (self.successes + 1) / (self.successes + self.failures + 2)


class LexicalRouter:
    """BM25-lite offline ranking over a small fixed menu of routes."""

    def __init__(
        self,
        routes: Mapping[str, Sequence[str]],
        priorities: Mapping[str, int] | None = None,
        *,
        reliability_weight: float = 0.15,
    ) -> None:
        priorities = priorities or {}
        self.reliability_weight = reliability_weight
        self.routes: dict[str, Route] = {
            rid: Route(rid, tuple(kws), priorities.get(rid, 0), doc=self._doc(kws))
            for rid, kws in routes.items()
        }
        self._build_index()

    @staticmethod
    def _doc(keywords: Iterable[str]) -> list[str]:
        return [tok for kw in keywords for tok in tokens(kw)]

    def _build_index(self) -> None:
        n = len(self.routes)
        df = Counter(tok for r in self.routes.values() for tok in set(r.doc))
        self._avg = sum(len(r.doc) for r in self.routes.values()) / max(1, n)
        self._idf = {tok: math.log(1 + (n - cnt + 0.5) / (cnt + 0.5)) for tok, cnt in df.items()}
        self._tf = {rid: Counter(r.doc) for rid, r in self.routes.items()}

        exact: dict[str, set[str]] = defaultdict(set)
        prefix: dict[str, set[str]] = defaultdict(set)
        for route in self.routes.values():
            for tok in route.doc:
                exact[tok].add(tok)
                if len(tok) >= PREFIX_LEN:
                    prefix[tok[:PREFIX_LEN]].add(tok)
                elif len(tok) >= STEM_MIN:
                    prefix[tok].add(tok)
        self._exact = dict(exact)
        self._prefix = dict(prefix)

        postings: dict[str, list[tuple[str, int]]] = defaultdict(list)
        for rid, tf in self._tf.items():
            for tok, cnt in tf.items():
                postings[tok].append((rid, cnt))
        self._postings = dict(postings)

    def _expand(self, term: str) -> tuple[list[str], float]:
        if term in self._exact:
            return [term], 1.0
        cands: set[str] = set()
        if len(term) >= PREFIX_LEN:
            cands |= {t for t in self._prefix.get(term[:PREFIX_LEN], ()) if len(t) >= PREFIX_LEN}
        stem = self._prefix.get(term[:STEM_MIN], ()) if len(term) >= STEM_MIN else ()
        cands |= {
            t
            for t in stem
            if len(t) < PREFIX_LEN and term.startswith(t) and len(term) - len(t) <= STEM_MAX_SUFFIX
        }
        return sorted(cands), PREFIX_WEIGHT

    def _term_score(self, term: str, rid: str, hits: int, weight: float) -> float:
        freq = hits if weight == 1.0 else hits * weight
        idf = self._idf.get(term, max(self._idf.values(), default=1.0))
        dl = len(self.routes[rid].doc)
        return idf * freq * 2.2 / (freq + 1.2 * (0.25 + 0.75 * dl / max(self._avg, 1)))

    def scores(self, query: str) -> dict[str, float]:
        """Return lexical + reliability score for routes with at least one token hit."""
        lexical: dict[str, float] = defaultdict(float)
        for term in set(tokens(query)):
            matched, weight = self._expand(term)
            hits: Counter[str] = Counter()
            for tok in matched:
                hits.update(dict(self._postings.get(tok, ())))
            idf_term = term if weight == 1.0 else (matched[0] if matched else term)
            for rid, cnt in hits.items():
                lexical[rid] += self._term_score(idf_term, rid, cnt, weight)
        weight = self.reliability_weight
        return {
            rid: score + weight * self.routes[rid].reliability
            for rid, score in lexical.items()
            if score > 0
        }

    def rank(self, query: str) -> list[tuple[str, float]]:
        """Rank matching routes by descending score, priority, then route ID."""
        scored = self.scores(query)
        order = sorted(
            scored,
            key=lambda rid: (-round(scored[rid], 9), -self.routes[rid].priority, rid),
        )
        return [(rid, scored[rid]) for rid in order]

    def best(self, query: str, default: str | None = None) -> str | None:
        """Return top-ranked route ID or ``default`` when nothing matched."""
        ranked = self.rank(query)
        return ranked[0][0] if ranked else default

    def record_outcome(self, route_id: str, ok: bool) -> None:
        """Record execution outcome to update route reliability."""
        route = self.routes[route_id]
        if ok:
            route.successes += 1
        else:
            route.failures += 1

    def matches(self, query: str, keywords: Iterable[str]) -> bool:
        """Return True if any keyword token-matches ``query`` (no substring traps)."""
        query_tokens = set(tokens(query))
        return any(_token_hit(query_tokens, tok) for kw in keywords for tok in tokens(kw))

    def to_operation_specs(self, namespace: str = "dun") -> list[Any]:
        """Export routes as ``autonom.registry.OperationSpec`` (optional dependency)."""
        from autonom.registry import OperationSpec

        return [
            OperationSpec(
                id=f"{namespace}.{rid}",
                description=" ".join(route.keywords),
                input_schema={"type": "object", "properties": {}},
                keywords=list(route.keywords),
                successes=route.successes,
                failures=route.failures,
            )
            for rid, route in sorted(self.routes.items())
        ]


def _token_hit(query_tokens: set[str], kw: str) -> bool:
    if kw in query_tokens:
        return True
    if len(kw) >= PREFIX_LEN:
        return any(len(q) >= PREFIX_LEN and q[:PREFIX_LEN] == kw[:PREFIX_LEN] for q in query_tokens)
    if len(kw) >= STEM_MIN:
        return any(q.startswith(kw) and len(q) - len(kw) <= STEM_MAX_SUFFIX for q in query_tokens)
    return False


def keyword_hits(text: str, table: Mapping[str, Sequence[str]]) -> list[str]:
    """Return labels from ``table`` whose keywords token-match ``text``."""
    query_tokens = set(tokens(text))
    folded = {label: [tok for kw in kws for tok in tokens(kw)] for label, kws in table.items()}
    return [label for label, kws in folded.items() if any(_token_hit(query_tokens, tok) for tok in kws)]


TASK_TYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "email_processing": (
        "email", "e-mail", "mail", "maile", "mailbox", "imap", "pop3", "smtp",
        "inbox", "gmail", "outlook", "skrzynka", "skrzynki", "wiadomość",
        "wiadomości", "poczta", "pocztowy", "załącznik", "attachment",
        "attachments", "newsletter",
    ),
    "database_processing": (
        "database", "baza", "bazie", "bazy", "sql", "postgresql", "postgres",
        "mysql", "sqlite", "rekord", "record", "records", "rows", "zapytanie",
        "query", "tabeli",
    ),
    "file_processing": (
        "plik", "pliki", "file", "files", "csv", "excel", "xlsx", "json", "xml",
        "folder", "katalog", "directory", "pdf", "dokument", "document",
        "archiwum", "zip", "txt", "rename", "konwertuj", "convert", "kompresuj",
    ),
    "web_scraping": (
        "strona", "website", "web", "page", "site", "scraping", "scrape",
        "crawl", "crawler", "internetowa", "www", "html", "linki", "links",
        "headlines",
    ),
    "api_processing": (
        "api", "endpoint", "rest", "webhook", "oauth", "graphql", "paginate",
        "response", "odpowiedź",
    ),
    "data_analysis": (
        "analiza", "przeanalizuj", "analyze", "analysis", "wykres", "chart",
        "charts", "plot", "statystyki", "statistics", "raport", "report",
        "dashboard", "średnia", "mediana", "average", "median", "trend",
        "revenue", "sprzedaż", "summary", "oblicz", "compute",
    ),
}

TASK_TYPE_PRIORITY = {
    "email_processing": 6,
    "database_processing": 5,
    "api_processing": 4,
    "web_scraping": 3,
    "data_analysis": 2,
    "file_processing": 1,
}

LIBRARY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "imaplib": (
        "email", "e-mail", "mail", "maile", "mailbox", "imap", "pop3", "inbox",
        "gmail", "skrzynka", "wiadomość", "wiadomości", "poczta", "załącznik",
        "attachment", "attachments",
    ),
    "sqlalchemy": (
        "database", "baza", "bazie", "bazy", "sql", "postgresql", "postgres",
        "mysql", "sqlite", "rekord", "records", "query", "zapytanie",
    ),
    "requests": (
        "http", "https", "api", "rest", "endpoint", "url", "strona", "website",
        "web", "page", "site", "www", "html", "scraping", "scrape", "crawl",
        "internetowa", "headlines", "linki",
    ),
    "pandas": (
        "csv", "excel", "xlsx", "pandas", "dataframe", "tabela", "arkusz",
        "spreadsheet", "kolumna", "column", "statystyki", "statistics",
        "wykres", "chart", "charts", "plot", "średnia", "mediana", "dane",
        "danych", "sprzedaż", "revenue", "dashboard", "analyze", "przeanalizuj",
    ),
    "pillow": (
        "obraz", "obrazy", "image", "images", "zdjęcie", "zdjęcia", "photo",
        "photos", "picture", "jpg", "jpeg", "png", "resize", "rozmiar",
        "thumbnail", "thumbnails", "miniatura", "grafika", "grafiki",
        "watermark", "wodny", "przytnij", "crop",
    ),
}

LIBRARY_PRIORITY = {
    "imaplib": 10,
    "sqlalchemy": 9,
    "requests": 8,
    "pandas": 7,
    "pillow": 6,
}

_TASK_ROUTER: LexicalRouter | None = None
_LIBRARY_ROUTER: LexicalRouter | None = None


def task_router() -> LexicalRouter:
    """Return cached router over task types."""
    global _TASK_ROUTER
    if _TASK_ROUTER is None:
        _TASK_ROUTER = LexicalRouter(TASK_TYPE_KEYWORDS, TASK_TYPE_PRIORITY)
    return _TASK_ROUTER


def library_router() -> LexicalRouter:
    """Return cached router over supported runtime libraries."""
    global _LIBRARY_ROUTER
    if _LIBRARY_ROUTER is None:
        _LIBRARY_ROUTER = LexicalRouter(LIBRARY_KEYWORDS, LIBRARY_PRIORITY)
    return _LIBRARY_ROUTER
