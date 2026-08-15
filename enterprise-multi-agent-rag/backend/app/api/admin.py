from fastapi import APIRouter, Depends
from pathlib import Path
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.api.deps import admin_user
from app.core.database import get_db
from app.models.entities import Document, DocumentChunk, EvaluationResult, ProcessingStatus, RagQuery, User
from app.services.search import HybridSearchService

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/stats")
def stats(db: Session = Depends(get_db), _=Depends(admin_user)):
    scalar = lambda stmt: db.scalar(stmt) or 0
    return {
        "total_users": scalar(select(func.count(User.id))),
        "total_documents": scalar(select(func.count(Document.id))),
        "total_chunks": scalar(select(func.count(DocumentChunk.id))),
        "total_questions": scalar(select(func.count(RagQuery.id))),
        "failed_processing_jobs": scalar(select(func.count(Document.id)).where(Document.processing_status == ProcessingStatus.FAILED)),
        "average_total_time": float(scalar(select(func.avg(RagQuery.total_time)))),
        "average_evaluation_score": float(scalar(select(func.avg(EvaluationResult.metric_value)))),
    }

@router.get("/users")
def users(db: Session = Depends(get_db), _=Depends(admin_user)):
    return [{"id": u.id, "email": u.email, "role": u.role.value, "created_at": u.created_at} for u in db.scalars(select(User).order_by(User.created_at.desc())).all()]

@router.get("/documents")
def documents(db: Session = Depends(get_db), _=Depends(admin_user)):
    return [{"id": d.id, "owner_id": d.owner_id, "filename": d.original_filename, "status": d.processing_status.value, "chunks": d.chunk_count, "error": d.processing_error} for d in db.scalars(select(Document).order_by(Document.created_at.desc())).all()]

@router.delete("/documents/{document_id}", status_code=204)
def admin_delete_document(document_id: str, db: Session = Depends(get_db), _=Depends(admin_user)):
    doc = db.get(Document, document_id)
    if not doc:
        from fastapi import HTTPException
        raise HTTPException(404, "Document not found")
    try: Path(doc.storage_path).unlink(missing_ok=True)
    except OSError: pass
    HybridSearchService().delete_document(doc.owner_id, doc.id)
    db.delete(doc); db.commit()
