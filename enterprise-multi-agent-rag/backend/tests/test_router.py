from app.agents.graph import router_agent

def test_comparison_route():
    assert router_agent({"question": "Compare policy A versus B"})["route"] == "DOCUMENT_COMPARISON"

def test_document_route():
    assert router_agent({"question": "What is annual leave?"})["route"] == "DOCUMENT_RAG"
