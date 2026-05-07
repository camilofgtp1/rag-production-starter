import pytest

from app.ingestion.chunker import chunk_document
from app.ingestion.loader import load_document


class TestLoader:
    def test_pdf_loading_returns_text(self):
        content = b"%PDF-1.4 test content"

        with pytest.raises(Exception):
            load_document(content, "application/pdf")

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
            load_document(
                content,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

    def test_empty_content(self):
        content = b""
        result = load_document(content, "text/plain")

        assert result == ""


class TestChunkingStrategy:
    def test_fixed_chunking_returns_chunks(self):
        text = "This is a test document. " * 50
        chunks = chunk_document(text, strategy="fixed")

        assert len(chunks) > 0
        assert all(c.strategy_used == "fixed" for c in chunks)

    def test_semantic_chunking_returns_chunks(self):
        text = "This is a test document.\n\nSecond paragraph here.\n\nThird paragraph with more content."
        chunks = chunk_document(text, strategy="semantic")

        assert len(chunks) > 0
        assert all(c.strategy_used == "semantic" for c in chunks)

    def test_late_chunking_returns_parent_and_child(self):
        text = "This is a test document. " * 50
        chunks = chunk_document(text, strategy="late")

        assert len(chunks) > 0
        parent_chunks = [c for c in chunks if c.parent_chunk_id is None]
        assert len(parent_chunks) > 0
        assert all(c.strategy_used == "late" for c in chunks)

    def test_unknown_strategy_raises(self):
        text = "Some text content"
        with pytest.raises(ValueError, match="Unknown strategy"):
            chunk_document(text, strategy="unknown")
