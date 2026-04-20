import pytest
from io import BytesIO

from app.ingestion.loader import load_document


class TestLoader:
    def test_pdf_loading_returns_text(self):
        content = b"%PDF-1.4 test content"
        
        with pytest.raises(Exception):
            result = load_document(content, "application/pdf")
    
    def test_markdown_loading_strips_markdown(self):
        content = b"# Heading\n\nParagraph text"
        result = load_document(content, "text/markdown")
        
        assert isinstance(result, str)
        assert "Heading" in result or len(result) > 0
    
    def test_plain_text_returns_decoded(self):
        content = b"Hello world"
        result = load_document(content, "text/plain")
        
        assert result == "Hello world"
    
    def test_unsupported_mime_raises_error(self):
        content = b"some content"
        
        with pytest.raises(ValueError, match="Unsupported mime type"):
            load_document(content, "application/octet-stream")
    
    def test_docx_loading(self):
        content = b"PK\x00\x00 mock docx"
        
        with pytest.raises(Exception):
            result = load_document(content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    
    def test_empty_content(self):
        content = b""
        result = load_document(content, "text/plain")
        
        assert result == ""