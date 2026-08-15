from app.services.chunking import chunk_sections
from app.services.parser import ParsedSection

def test_chunking_preserves_page():
    chunks = chunk_sections([ParsedSection("word " * 300, 7, {"x": 1})], chunk_size=200, overlap=20)
    assert len(chunks) > 1
    assert all(c.page_number == 7 for c in chunks)
    assert all(c.metadata["x"] == 1 for c in chunks)

def test_invalid_overlap():
    import pytest
    with pytest.raises(ValueError): chunk_sections([ParsedSection("abc", 1, {})], chunk_size=10, overlap=10)
