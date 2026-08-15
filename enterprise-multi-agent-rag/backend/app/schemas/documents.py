from datetime import datetime
from pydantic import BaseModel

class DocumentResponse(BaseModel):
    id: str
    original_filename: str
    file_type: str
    file_size: int
    processing_status: str
    page_count: int | None
    chunk_count: int
    processing_error: str | None
    created_at: datetime
    model_config = {"from_attributes": True}

class DocumentSearchHit(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    content: str
    page_number: int | None
    score: float

