from dataclasses import dataclass
from elasticsearch import Elasticsearch
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.entities import Document, DocumentChunk
from app.services.embeddings import get_embedding_service

@dataclass
class SearchHit:
    chunk_id: str
    document_id: str
    filename: str
    content: str
    page_number: int | None
    score: float
    metadata: dict

class HybridSearchService:
    index_name = "enterprise_rag_chunks"

    def __init__(self):
        self.es = Elasticsearch(settings.elasticsearch_url, request_timeout=10)

    def ensure_index(self):
        if not self.es.indices.exists(index=self.index_name):
            self.es.indices.create(index=self.index_name, mappings={"properties": {
                "chunk_id": {"type": "keyword"}, "document_id": {"type": "keyword"},
                "owner_id": {"type": "keyword"}, "filename": {"type": "keyword"},
                "content": {"type": "text"}, "page_number": {"type": "integer"},
            }})

    def semantic(self, db: Session, owner_id: str, query: str, document_ids: list[str] | None, limit: int) -> list[SearchHit]:
        vector = get_embedding_service().embed_text(query)
        stmt = select(DocumentChunk, Document.original_filename).join(Document, Document.id == DocumentChunk.document_id).where(DocumentChunk.owner_id == owner_id)
        if document_ids:
            stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))
        stmt = stmt.order_by(DocumentChunk.embedding.cosine_distance(vector)).limit(limit)
        rows = db.execute(stmt).all()
        return [SearchHit(c.id, c.document_id, name, c.content, c.page_number, max(0.0, 1.0 - i/limit), dict(c.chunk_metadata or {})) for i, (c, name) in enumerate(rows)]

    def keyword(self, owner_id: str, query: str, document_ids: list[str] | None, limit: int) -> list[SearchHit]:
        filters = [{"term": {"owner_id": owner_id}}]
        if document_ids:
            filters.append({"terms": {"document_id": document_ids}})
        body = {"size": limit, "query": {"bool": {"should": [{"match": {"content": {"query": query, "operator": "or"}}}, {"match_phrase": {"content": {"query": query, "boost": 2.0}}}], "minimum_should_match": 1, "filter": filters}}}
        result = self.es.search(index=self.index_name, body=body)
        hits = []
        for h in result["hits"]["hits"]:
            s = h["_source"]
            hits.append(SearchHit(s["chunk_id"], s["document_id"], s["filename"], s["content"], s.get("page_number"), float(h.get("_score") or 0), s.get("metadata", {})))
        return hits

    def hybrid(self, db: Session, owner_id: str, query: str, document_ids: list[str] | None = None) -> list[SearchHit]:
        limit = settings.retrieval_candidates
        vector_hits, keyword_hits = [], []
        try: vector_hits = self.semantic(db, owner_id, query, document_ids, limit)
        except Exception: pass
        try: keyword_hits = self.keyword(owner_id, query, document_ids, limit)
        except Exception: pass
        scores: dict[str, float] = {}
        by_id: dict[str, SearchHit] = {}
        k = 60
        for rank, hit in enumerate(vector_hits, 1):
            scores[hit.chunk_id] = scores.get(hit.chunk_id, 0) + 1/(k+rank)
            by_id[hit.chunk_id] = hit
        for rank, hit in enumerate(keyword_hits, 1):
            scores[hit.chunk_id] = scores.get(hit.chunk_id, 0) + 1/(k+rank)
            by_id[hit.chunk_id] = hit
        ordered = sorted(scores, key=scores.get, reverse=True)
        return [SearchHit(**{**by_id[cid].__dict__, "score": scores[cid]}) for cid in ordered[:limit]]

    def index_chunks(self, chunks: list[dict]):
        self.ensure_index()
        ops = []
        for item in chunks:
            ops.extend([{"index": {"_index": self.index_name, "_id": item["chunk_id"]}}, item])
        if ops:
            self.es.bulk(operations=ops, refresh=True)

    def delete_document(self, owner_id: str, document_id: str):
        try:
            self.es.delete_by_query(index=self.index_name, query={"bool": {"filter": [{"term": {"owner_id": owner_id}}, {"term": {"document_id": document_id}}]}}, refresh=True)
        except Exception:
            pass
