from pathlib import Path

def test_owner_filters_present_in_document_and_conversation_routes():
    docs = Path("app/api/documents.py").read_text(encoding="utf-8")
    chat = Path("app/api/chat.py").read_text(encoding="utf-8")
    search = Path("app/services/search.py").read_text(encoding="utf-8")
    assert "Document.owner_id == user.id" in docs
    assert "Conversation.user_id == user.id" in chat
    assert "DocumentChunk.owner_id == owner_id" in search
    assert '"owner_id": owner_id' in search
