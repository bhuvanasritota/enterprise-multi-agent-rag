from sqlalchemy import delete
from app.core.database import SessionLocal
from app.models.entities import Document, DocumentChunk, ProcessingStatus
from app.services.chunking import chunk_sections
from app.services.embeddings import get_embedding_service
from app.services.parser import DocumentParser
from app.services.search import HybridSearchService
from app.workers.celery_app import celery

@celery.task(bind=True, autoretry_for=(ConnectionError,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def process_document(self, document_id: str):
    db = SessionLocal()
    doc = None
    try:
        doc = db.get(Document, document_id)
        if not doc: return
        doc.processing_status = ProcessingStatus.PROCESSING
        doc.processing_error = None
        db.commit()
        parsed = DocumentParser().parse(doc.storage_path, doc.file_type)
        chunks = chunk_sections(parsed.sections)
        if not chunks: raise ValueError("No searchable text was extracted from the document")
        embeddings = get_embedding_service().embed_documents([c.content for c in chunks])
        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))
        records, es_records = [], []
        for idx, (chunk, vector) in enumerate(zip(chunks, embeddings)):
            row = DocumentChunk(document_id=doc.id, owner_id=doc.owner_id, chunk_index=idx, content=chunk.content, page_number=chunk.page_number, embedding=vector, chunk_metadata=chunk.metadata)
            db.add(row); db.flush(); records.append(row)
            es_records.append({"chunk_id": row.id, "document_id": doc.id, "owner_id": doc.owner_id, "filename": doc.original_filename, "content": row.content, "page_number": row.page_number, "metadata": row.chunk_metadata})
        HybridSearchService().index_chunks(es_records)
        doc.page_count = parsed.page_count
        doc.chunk_count = len(records)
        doc.processing_status = ProcessingStatus.COMPLETED
        db.commit()
    except Exception as exc:
        db.rollback()
        if doc:
            doc = db.get(Document, document_id)
            if doc:
                doc.processing_status = ProcessingStatus.FAILED
                doc.processing_error = str(exc)[:2000]
                db.commit()
        raise
    finally:
        db.close()
