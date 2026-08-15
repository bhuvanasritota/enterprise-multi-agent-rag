from app.services.parser import DocumentParser

def test_txt_parser(tmp_path):
    p = tmp_path / "a.txt"; p.write_text("Policy text", encoding="utf-8")
    result = DocumentParser().parse(str(p), "txt")
    assert result.sections[0].text == "Policy text"
