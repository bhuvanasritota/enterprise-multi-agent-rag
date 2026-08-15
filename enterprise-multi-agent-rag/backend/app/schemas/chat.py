from datetime import datetime
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=5000)
    conversation_id: str | None = None
    document_ids: list[str] | None = None

class SourceResponse(BaseModel):
    document_id: str
    filename: str
    page_number: int | None = None
    chunk_id: str
    score: float | None = None

class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    sources: list[SourceResponse]
    route: str

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    sources: list
    created_at: datetime
    model_config = {"from_attributes": True}

class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class ConversationDetail(ConversationResponse):
    messages: list[MessageResponse]
