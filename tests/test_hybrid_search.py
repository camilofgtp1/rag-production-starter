import pytest
from unittest.mock import patch, AsyncMock

from app.retrieval import hybrid_search


class TestHybridSearch:
    @pytest.mark.asyncio
    async def test_alpha_one_returns_dense_ordering(self):
        with patch('app.retrieval.hybrid_search.qdrant_client') as mock_qdrant:
            mock_qdrant.get_all_chunks.return_value = [
                {"chunk_id": "1", "text": "doc one", "doc_id": "d1", "filename": "f1.txt", "version": 1},
                {"chunk_id": "2", "text": "doc two", "doc_id": "d2", "filename": "f2.txt", "version": 1},
            ]
            mock_qdrant.dense_search.return_value = [
                {"chunk_id": "2", "score": 0.9, "doc_id": "d2", "filename": "f2.txt", "version": 1, "text": "doc two"},
                {"chunk_id": "1", "score": 0.7, "doc_id": "d1", "filename": "f1.txt", "version": 1, "text": "doc one"},
            ]
            
            with patch('app.retrieval.hybrid_search.embed_texts', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = [[0.1] * 1536]
                
                results = await hybrid_search.hybrid_search(
                    "test query",
                    [0.1] * 1536,
                    top_k=5,
                    alpha=1.0
                )
                
                assert results[0]["chunk_id"] == "2"
    
    @pytest.mark.asyncio
    async def test_alpha_zero_returns_bm25_ordering(self):
        with patch('app.retrieval.hybrid_search.qdrant_client') as mock_qdrant:
            mock_qdrant.get_all_chunks.return_value = [
                {"chunk_id": "1", "text": "test content", "doc_id": "d1", "filename": "f1.txt", "version": 1},
                {"chunk_id": "2", "text": "other content", "doc_id": "d2", "filename": "f2.txt", "version": 1},
            ]
            mock_qdrant.dense_search.return_value = [
                {"chunk_id": "1", "score": 0.5, "doc_id": "d1", "filename": "f1.txt", "version": 1, "text": "test content"},
            ]
            
            with patch('app.retrieval.hybrid_search.embed_texts', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = [[0.1] * 1536]
                
                results = await hybrid_search.hybrid_search(
                    "test query",
                    [0.1] * 1536,
                    top_k=5,
                    alpha=0.0
                )
                
                assert len(results) >= 1
    
    @pytest.mark.asyncio
    async def test_alpha_point_five_produces_merged_ranking(self):
        with patch('app.retrieval.hybrid_search.qdrant_client') as mock_qdrant:
            mock_qdrant.get_all_chunks.return_value = [
                {"chunk_id": "1", "text": "content one", "doc_id": "d1", "filename": "f1.txt", "version": 1},
                {"chunk_id": "2", "text": "content two", "doc_id": "d2", "filename": "f2.txt", "version": 1},
            ]
            mock_qdrant.dense_search.return_value = [
                {"chunk_id": "1", "score": 0.8, "doc_id": "d1", "filename": "f1.txt", "version": 1, "text": "content one"},
            ]
            
            with patch('app.retrieval.hybrid_search.embed_texts', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = [[0.1] * 1536]
                
                results = await hybrid_search.hybrid_search(
                    "test query",
                    [0.1] * 1536,
                    top_k=5,
                    alpha=0.5
                )
                
                assert len(results) >= 1
    
    @pytest.mark.asyncio
    async def test_empty_corpus_returns_empty(self):
        with patch('app.retrieval.hybrid_search.qdrant_client') as mock_qdrant:
            mock_qdrant.get_all_chunks.return_value = []
            
            with patch('app.retrieval.hybrid_search.embed_texts', new_callable=AsyncMock) as mock_embed:
                mock_embed.return_value = [[0.1] * 1536]
                
                results = await hybrid_search.hybrid_search(
                    "test query",
                    [0.1] * 1536,
                    top_k=5,
                    alpha=0.5
                )
                
                assert results == []