from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import current_user
from app.core.database import get_db
from app.models.entities import Document, User
from app.schemas.documents import DocumentResponse, DocumentSearchHit
from app.services.search import HybridSearchService
from app.services.storage import validate_and_save
from app.workers.tasks import process_document

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentResponse, status_code=202)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(current_user)):
    try: path, file_type, size, original = await validate_and_save(file, user.id)
    except ValueError as exc: raise HTTPException(400, str(exc))
    doc = Document(owner_id=user.id, filename=Path(path).name, original_filename=original, file_type=file_type, file_size=size, storage_path=path)
    db.add(doc); db.commit(); db.refresh(doc)
    try: process_document.delay(doc.id)
    except Exception as exc:
        doc.processing_error = f"Could not queue processing job: {exc}"[:2000]
        db.commit()
        raise HTTPException(503, "Document saved but background processing could not be queued")
    return doc

@router.get("", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.scalars(select(Document).where(Document.owner_id == user.id).order_by(Document.created_at.desc())).all()


@router.get("/search", response_model=list[DocumentSearchHit])
def search_documents(q: str, document_id: str | None = None, db: Session = Depends(get_db), user: User = Depends(current_user)):
    ids = [document_id] if document_id else None
    hits = HybridSearchService().hybrid(db, user.id, q, ids)
    return [DocumentSearchHit(chunk_id=h.chunk_id, document_id=h.document_id, filename=h.filename, content=h.content, page_number=h.page_number, score=h.score) for h in hits[:10]]

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    doc = db.scalar(select(Document).where(Document.id == document_id, Document.owner_id == user.id))
    if not doc: raise HTTPException(404, "Document not found")
    return doc

@router.get("/{document_id}/status", response_model=DocumentResponse)
def status(document_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return get_document(document_id, db, user)

@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    doc = db.scalar(select(Document).where(Document.id == document_id, Document.owner_id == user.id))
    if not doc: raise HTTPException(404, "Document not found")
    try: Path(doc.storage_path).unlink(missing_ok=True)
    except OSError: pass
    HybridSearchService().delete_document(user.id, doc.id)
    db.delete(doc); db.commit()
