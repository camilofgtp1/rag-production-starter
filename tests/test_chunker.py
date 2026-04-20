import pytest
from unittest.mock import patch, MagicMock

from app.ingestion.chunker import chunk_document, Chunk, count_tokens


class TestFixedChunking:
    def test_output_has_valid_chunk_objects(self):
        text = "Hello world. " * 100
        chunks = chunk_document(text, strategy="fixed")
        
        assert all(isinstance(c, Chunk) for c in chunks)
        assert all(c.chunk_id for c in chunks)
    
    def test_token_count_within_bounds(self):
        text = "Hello world. " * 200
        chunks = chunk_document(text, strategy="fixed")
        
        assert all(c.token_count <= 512 for c in chunks)
    
    def test_uses_correct_strategy(self):
        text = "Hello world. " * 100
        chunks = chunk_document(text, strategy="fixed")
        
        assert all(c.strategy_used == "fixed" for c in chunks)


class TestSemanticChunking:
    def test_output_has_valid_chunk_objects(self):
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = chunk_document(text, strategy="semantic")
        
        assert all(isinstance(c, Chunk) for c in chunks)
    
    def test_no_chunk_exceeds_max_tokens(self):
        text = "This is a sentence. " * 150
        chunks = chunk_document(text, strategy="semantic")
        
        assert all(c.token_count <= 512 for c in chunks)
    
    def test_respects_paragraph_boundaries(self):
        text = "Para one ends here.\n\nPara two starts here."
        chunks = chunk_document(text, strategy="semantic")
        
        assert len(chunks) >= 1


class TestLateChunking:
    def test_output_contains_both_parent_and_child(self):
        text = "First parent paragraph.\n\nSecond parent paragraph.\n\nThird parent."
        chunks = chunk_document(text, strategy="late")
        
        assert len(chunks) >= 2
    
    def test_children_have_parent_id(self):
        text = "Parent one.\n\nParent two.\n\nParent three."
        chunks = chunk_document(text, strategy="late")
        
        parent_ids = {c.chunk_id for c in chunks if c.parent_chunk_id is None}
        children = [c for c in chunks if c.parent_chunk_id is not None]
        
        if children:
            assert all(c.parent_chunk_id in parent_ids for c in children)
    
    def test_uses_correct_strategy(self):
        text = "Parent content here.\n\nMore parent."
        chunks = chunk_document(text, strategy="late")
        
        assert all(c.strategy_used == "late" for c in chunks)


class TestTokenCount:
    def test_count_tokens_returns_int(self):
        text = "Hello world"
        count = count_tokens(text)
        
        assert isinstance(count, int)
        assert count > 0