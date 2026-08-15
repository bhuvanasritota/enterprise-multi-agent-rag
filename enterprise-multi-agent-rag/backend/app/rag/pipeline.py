import time
from sqlalchemy.orm import Session
from app.agents.graph import graph

async def run_rag(db: Session, owner_id: str, question: str, document_ids: list[str] | None = None) -> dict:
    started = time.perf_counter()
    result = await graph.ainvoke({"db": db, "owner_id": owner_id, "question": question, "document_ids": document_ids})
    total = time.perf_counter() - started
    hits = result.get("hits", [])
    sources = [{"document_id": h.document_id, "filename": h.filename, "page_number": h.page_number, "chunk_id": h.chunk_id, "score": h.score} for h in hits]
    return {"answer": result.get("answer", ""), "sources": sources, "route": result.get("route", "DOCUMENT_RAG"), "total_time": total}
