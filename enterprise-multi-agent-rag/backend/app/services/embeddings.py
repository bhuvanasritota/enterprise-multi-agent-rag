from functools import lru_cache
import hashlib
import math
import re


class EmbeddingService:
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name

    def _embed(self, text: str) -> list[float]:
        # Lightweight deterministic 384-dimensional embedding.
        # This avoids loading a large ML model into Render's 512 MB RAM.
        vector = [0.0] * 384

        words = re.findall(r"\b\w+\b", text.lower())

        for word in words:
            digest = hashlib.sha256(word.encode("utf-8")).digest()

            index = int.from_bytes(digest[:4], "big") % 384
            sign = 1.0 if digest[4] % 2 == 0 else -1.0

            vector[index] += sign

        magnitude = math.sqrt(sum(x * x for x in vector))

        if magnitude > 0:
            vector = [x / magnitude for x in vector]

        return vector

    def embed_text(self, text: str) -> list[float]:
        return self._embed(text)

    def embed_documents(
        self,
        texts: list[str],
        batch_size: int = 32,
    ) -> list[list[float]]:
        return [self._embed(text) for text in texts]


@lru_cache
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
