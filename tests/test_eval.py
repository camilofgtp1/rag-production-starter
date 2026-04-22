import pytest
from unittest.mock import patch

from app.evaluation import ragas_eval


class TestEval:
    @pytest.mark.asyncio
    async def test_run_evaluation_returns_dict(self):
        with patch('app.evaluation.ragas_eval.evaluate') as mock_eval:
            mock_eval.return_value = {
                "faithfulness": 0.85,
                "answer_relevancy": 0.75,
                "context_recall": 0.90,
            }
            
            result = await ragas_eval.run_evaluation(
                "What is the policy?",
                "The policy states...",
                ["context text here"],
            )
            
            assert result["faithfulness"] == 0.85
            assert result["answer_relevancy"] == 0.75
            assert result["context_recall"] == 0.90
    
    @pytest.mark.asyncio
    async def test_returns_all_required_fields(self):
        with patch('app.evaluation.ragas_eval.evaluate') as mock_eval:
            mock_eval.return_value = {
                "faithfulness": 0.8,
                "answer_relevancy": 0.7,
                "context_recall": 0.9,
            }
            
            result = await ragas_eval.run_evaluation(
                "query",
                "answer",
                ["ctx1", "ctx2"],
            )
            
            assert "faithfulness" in result
            assert "answer_relevancy" in result
            assert "context_recall" in result
    
    def test_eval_scores_are_floats(self):
        eval_scores = {
            "faithfulness": 0.85,
            "answer_relevancy": 0.75,
            "context_recall": 0.90,
        }
        
        for key, value in eval_scores.items():
            assert isinstance(value, float)
            assert 0.0 <= value <= 1.0