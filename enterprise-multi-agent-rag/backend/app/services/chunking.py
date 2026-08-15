from dataclasses import dataclass
from app.core.config import settings
from app.services.parser import ParsedSection

@dataclass
class Chunk:
    content: str
    page_number: int | None
    metadata: dict

def clean_text(text: str) -> str:
    return " ".join(text.replace("\x00", " ").split())

def chunk_sections(sections: list[ParsedSection], chunk_size: int | None = None, overlap: int | None = None) -> list[Chunk]:
    size = chunk_size or settings.chunk_size
    ov = settings.chunk_overlap if overlap is None else overlap
    if size <= 0 or ov < 0 or ov >= size:
        raise ValueError("Invalid chunk_size/chunk_overlap configuration")
    chunks: list[Chunk] = []
    for section in sections:
        text = clean_text(section.text)
        start = 0
        while start < len(text):
            end = min(len(text), start + size)
            piece = text[start:end]
            if end < len(text):
                boundary = piece.rfind(" ")
                if boundary > size * 0.6:
                    end = start + boundary
                    piece = text[start:end]
            piece = piece.strip()
            if piece:
                chunks.append(Chunk(piece, section.page_number, dict(section.metadata)))
            if end >= len(text):
                break
            start = max(end - ov, start + 1)
    return chunks
