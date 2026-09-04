from functools import lru_cache
import re

from app.core.config import settings
from app.services.search import SearchHit


class RerankerService:
    def __init__(self):
        pass

    def _score(self, query: str, content: str) -> float:
        query_words = set(re.findall(r"\b\w+\b", query.lower()))
        content_words = set(re.findall(r"\b\w+\b", content.lower()))

        if not query_words:
            return 0.0

        return len(query_words & content_words) / len(query_words)

    def rerank(
        self,
        query: str,
        hits: list[SearchHit],
        top_k: int | None = None,
    ) -> list[SearchHit]:
        if not hits:
            return []

        limit = top_k or settings.top_k

        try:
            ranked = sorted(
                hits,
                key=lambda h: self._score(query, h.content),
                reverse=True,
            )

            return ranked[:limit]

        except Exception:
            return hits[:limit]


@lru_cache
def get_reranker():
    return RerankerService()
