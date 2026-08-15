from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.api.deps import current_user
from app.core.database import get_db
from app.models.entities import Conversation, EvaluationResult, Message, RagQuery, User
from app.rag.pipeline import run_rag
from app.schemas.chat import ChatRequest, ChatResponse, ConversationDetail, ConversationResponse

router = APIRouter(tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    convo = None
    if body.conversation_id:
        convo = db.scalar(select(Conversation).where(Conversation.id == body.conversation_id, Conversation.user_id == user.id))
        if not convo: raise HTTPException(404, "Conversation not found")
    if not convo:
        convo = Conversation(user_id=user.id, title=body.question[:80])
        db.add(convo); db.flush()
    db.add(Message(conversation_id=convo.id, role="user", content=body.question, sources=[]))
    result = await run_rag(db, user.id, body.question, body.document_ids)
    db.add(Message(conversation_id=convo.id, role="assistant", content=result["answer"], sources=result["sources"]))
    rq = RagQuery(user_id=user.id, conversation_id=convo.id, query=body.question, total_time=result["total_time"])
    db.add(rq); db.flush()
    db.add(EvaluationResult(query_id=rq.id, metric_name="has_sources", metric_value=1.0 if result["sources"] else 0.0))
    db.add(EvaluationResult(query_id=rq.id, metric_name="answer_nonempty", metric_value=1.0 if result["answer"].strip() else 0.0))
    db.commit()
    return ChatResponse(conversation_id=convo.id, answer=result["answer"], sources=result["sources"], route=result["route"])

@router.get("/conversations", response_model=list[ConversationResponse])
def conversations(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.scalars(select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.updated_at.desc())).all()

@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def conversation(conversation_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = db.scalar(select(Conversation).options(selectinload(Conversation.messages)).where(Conversation.id == conversation_id, Conversation.user_id == user.id))
    if not item: raise HTTPException(404, "Conversation not found")
    return item

@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id))
    if not item: raise HTTPException(404, "Conversation not found")
    db.delete(item); db.commit()
