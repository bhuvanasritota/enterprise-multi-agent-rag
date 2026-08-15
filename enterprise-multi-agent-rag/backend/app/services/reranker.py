from functools import lru_cache
from sentence_transformers import CrossEncoder
from app.core.config import settings
from app.services.search import SearchHit

class RerankerService:
    def __init__(self): self._model = None
    @property
    def model(self):
        if self._model is None: self._model = CrossEncoder(settings.reranker_model)
        return self._model
    def rerank(self, query: str, hits: list[SearchHit], top_k: int | None = None) -> list[SearchHit]:
        if not hits: return []
        try:
            scores = self.model.predict([(query, h.content) for h in hits]).tolist()
            ranked = sorted(zip(hits, scores), key=lambda x: x[1], reverse=True)
            return [SearchHit(**{**h.__dict__, "score": float(s)}) for h, s in ranked[:top_k or settings.top_k]]
        except Exception:
            return hits[:top_k or settings.top_k]

@lru_cache
def get_reranker(): return RerankerService()
