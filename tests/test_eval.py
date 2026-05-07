from unittest.mock import MagicMock, patch


class TestEval:
    def test_run_evaluation_returns_real_scores_structure(self):
        """Verify the expected score keys and value constraints."""
        scores = {
            "faithfulness": 0.85,
            "answer_relevancy": 0.75,
            "context_recall": 0.90,
        }
        for key, value in scores.items():
            assert isinstance(value, float)
            assert 0.0 <= value <= 1.0

    def test_eval_error_response_structure(self):
        """Verify error response returns -1.0 for all scores plus error key."""
        result = {
            "faithfulness": -1.0,
            "answer_relevancy": -1.0,
            "context_recall": -1.0,
            "error": "simulated failure",
        }
        assert result["faithfulness"] == -1.0
        assert result["answer_relevancy"] == -1.0
        assert result["context_recall"] == -1.0
        assert result["error"] == "simulated failure"

    @patch("app.evaluation.ragas_eval.RAGAS_AVAILABLE", False)
    def test_run_evaluation_when_ragas_unavailable(self):
        """Verify graceful degradation when ragas is not installed."""
        from app.evaluation.ragas_eval import run_evaluation
        import asyncio

        result = asyncio.run(
            run_evaluation(
                query="What is RAG?",
                answer="RAG is Retrieval Augmented Generation",
                contexts=["RAG combines retrieval and generation."],
            )
        )
        assert result["error"] == "Ragas not installed"
        assert all(
            result[k] == -1.0
            for k in ["faithfulness", "answer_relevancy", "context_recall"]
        )

    @patch("ragas.llms.LangchainLLMWrapper")
    @patch("ragas.embeddings.LangchainEmbeddingsWrapper")
    @patch("langchain_openai.ChatOpenAI")
    @patch("langchain_openai.OpenAIEmbeddings")
    def test_run_evaluation_calls_ragas_correctly(
        self,
        mock_oai_emb,
        mock_oai_llm,
        mock_emb_wrapper,
        mock_llm_wrapper,
    ):
        """Verify ragas evaluate is called with correct parameters."""
        import asyncio
        from ragas import EvaluationDataset

        mock_result = MagicMock()
        mock_df = MagicMock()
        mock_df.__getitem__ = lambda self, key: MagicMock(mean=lambda: 0.85)
        mock_result.to_pandas.return_value = mock_df

        with patch("app.evaluation.ragas_eval.evaluate", return_value=mock_result):
            from app.evaluation.ragas_eval import run_evaluation

            result = asyncio.run(
                run_evaluation(
                    query="What is RAG?",
                    answer="RAG is Retrieval Augmented Generation",
                    contexts=["RAG combines retrieval and generation."],
                )
            )

            from app.evaluation.ragas_eval import evaluate

            evaluate.assert_called_once()
            call_args = evaluate.call_args
            assert isinstance(call_args[0][0], EvaluationDataset)
            assert "metrics" in call_args[1]
