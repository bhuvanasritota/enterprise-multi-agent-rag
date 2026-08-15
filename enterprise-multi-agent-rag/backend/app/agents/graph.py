from typing import TypedDict
from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session
from app.core.config import settings
from app.rag.prompts import ANSWER_PROMPT, COMPARISON_PROMPT, GENERAL_PROMPT, SYSTEM_GROUNDED, VERIFICATION_PROMPT
from app.services.llm import get_llm_service
from app.services.reranker import get_reranker
from app.services.search import HybridSearchService, SearchHit

class AgentState(TypedDict, total=False):
    question: str
    owner_id: str
    document_ids: list[str] | None
    db: Session
    route: str
    hits: list[SearchHit]
    context: str
    answer: str
    supported: bool
    retries: int

GENERAL_PREFIXES = ("hello", "hi ", "hey", "thanks", "thank you")

def router_agent(state: AgentState):
    q = state["question"].strip().lower()
    if any(x in q for x in ("compare", "difference between", "versus", " vs ")): route = "DOCUMENT_COMPARISON"
    elif any(x in q for x in ("how many documents", "statistics", "analytics", "usage")): route = "ANALYTICS"
    elif q.startswith(GENERAL_PREFIXES): route = "GENERAL_CHAT"
    else: route = "DOCUMENT_RAG"
    return {"route": route, "retries": 0}

def route_next(state: AgentState):
    return "general" if state["route"] in {"GENERAL_CHAT", "ANALYTICS"} else "retrieve"

def retrieval_agent(state: AgentState):
    hits = HybridSearchService().hybrid(state["db"], state["owner_id"], state["question"], state.get("document_ids"))
    hits = get_reranker().rerank(state["question"], hits, settings.top_k)
    context_lines = []
    for i, h in enumerate(hits, 1):
        page = f", page {h.page_number}" if h.page_number else ""
        context_lines.append(f"[S{i}] {h.filename}{page}, chunk {h.chunk_id}: {h.content}")
    return {"hits": hits, "context": "\n\n".join(context_lines)}

async def answer_agent(state: AgentState):
    if not state.get("hits"):
        return {"answer": "I could not find relevant evidence in your uploaded documents."}
    template = COMPARISON_PROMPT if state["route"] == "DOCUMENT_COMPARISON" else ANSWER_PROMPT
    answer = await get_llm_service().generate(template.format(question=state["question"], context=state["context"]), SYSTEM_GROUNDED)
    return {"answer": answer}

async def general_agent(state: AgentState):
    if state["route"] == "ANALYTICS":
        return {"answer": "Analytics questions are available through the dashboard and admin statistics endpoints. Ask a document question to run RAG.", "hits": []}
    answer = await get_llm_service().generate(GENERAL_PROMPT.format(question=state["question"]), "You are a concise enterprise assistant.")
    return {"answer": answer, "hits": []}

async def verification_agent(state: AgentState):
    if not state.get("hits"):
        return {"supported": True}
    verdict = await get_llm_service().generate(VERIFICATION_PROMPT.format(answer=state["answer"], context=state["context"]), "Return exactly SUPPORTED or UNSUPPORTED.")
    supported = verdict.strip().upper().startswith("SUPPORTED")
    return {"supported": supported}

def verify_next(state: AgentState):
    if state.get("supported") or state.get("retries", 0) >= 1: return END
    return "retry"

def retry_agent(state: AgentState):
    return {"retries": state.get("retries", 0) + 1}

builder = StateGraph(AgentState)
builder.add_node("router", router_agent)
builder.add_node("retrieve", retrieval_agent)
builder.add_node("answer", answer_agent)
builder.add_node("general", general_agent)
builder.add_node("verify", verification_agent)
builder.add_node("retry", retry_agent)
builder.add_edge(START, "router")
builder.add_conditional_edges("router", route_next, {"retrieve": "retrieve", "general": "general"})
builder.add_edge("retrieve", "answer")
builder.add_edge("answer", "verify")
builder.add_conditional_edges("verify", verify_next, {END: END, "retry": "retry"})
builder.add_edge("retry", "retrieve")
builder.add_edge("general", END)
graph = builder.compile()
