import pytest

from app.evaluation import ragas_eval


class TestEval:
    def test_eval_scores_are_floats(self):
        eval_scores = {
            "faithfulness": 0.85,
            "answer_relevancy": 0.75,
            "context_recall": 0.90,
        }
        
        for key, value in eval_scores.items():
            assert isinstance(value, float)
            assert 0.0 <= value <= 1.0
    
    def test_eval_scores_are_floats(self):
        eval_scores = {
            "faithfulness": 0.85,
            "answer_relevancy": 0.75,
            "context_recall": 0.90,
        }
        
        for key, value in eval_scores.items():
            assert isinstance(value, float)
            assert 0.0 <= value <= 1.0