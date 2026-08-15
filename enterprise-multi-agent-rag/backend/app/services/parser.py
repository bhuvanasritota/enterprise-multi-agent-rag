from dataclasses import dataclass
from pathlib import Path
import fitz
import pandas as pd
from docx import Document as DocxDocument

@dataclass
class ParsedSection:
    text: str
    page_number: int | None
    metadata: dict

@dataclass
class ParseResult:
    sections: list[ParsedSection]
    page_count: int | None
    metadata: dict

class DocumentParser:
    def parse(self, path: str, file_type: str) -> ParseResult:
        method = getattr(self, f"_parse_{file_type}", None)
        if not method:
            raise ValueError(f"Unsupported parser type: {file_type}")
        return method(Path(path))

    def _parse_pdf(self, path: Path) -> ParseResult:
        sections = []
        with fitz.open(path) as doc:
            meta = dict(doc.metadata or {})
            for index, page in enumerate(doc):
                text = page.get_text("text").strip()
                if text:
                    sections.append(ParsedSection(text=text, page_number=index + 1, metadata={"page": index + 1}))
            return ParseResult(sections, len(doc), meta)

    def _parse_docx(self, path: Path) -> ParseResult:
        doc = DocxDocument(path)
        text = "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())
        props = doc.core_properties
        meta = {"title": props.title or "", "author": props.author or ""}
        return ParseResult([ParsedSection(text, None, meta)] if text else [], None, meta)

    def _parse_txt(self, path: Path) -> ParseResult:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="latin-1")
        return ParseResult([ParsedSection(text.strip(), None, {})] if text.strip() else [], None, {})

    def _parse_csv(self, path: Path) -> ParseResult:
        df = pd.read_csv(path)
        sections = []
        for idx, row in df.iterrows():
            text = " | ".join(f"{col}: {row[col]}" for col in df.columns)
            sections.append(ParsedSection(text=text, page_number=None, metadata={"row": int(idx) + 1}))
        return ParseResult(sections, None, {"columns": list(df.columns), "rows": len(df)})
