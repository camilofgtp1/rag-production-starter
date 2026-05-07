import logging
from typing import Dict, List, Tuple

from app.config import settings
from app.generation.provider import get_provider

logger = logging.getLogger(__name__)

MODEL = settings.OPENAI_MODEL
MAX_TOKENS = 1000

SYSTEM_PROMPT = """You are a precise assistant. Answer the user's question using ONLY the provided context. If the context does not contain enough information to answer, respond with: 'I don't have enough information in the provided documents to answer this.' Always reference the source filename when you use information from it."""

_provider = None


def _get_provider():
    global _provider
    if _provider is None:
        _provider = get_provider()
    return _provider


async def generate_answer(query: str, context_chunks: List[Dict]) -> Tuple[str, Dict]:
    context_parts = []
    for chunk in context_chunks:
        context_parts.append(
            f"[Source: {chunk.get('filename', 'unknown')}]\n{chunk.get('text', '')}"
        )

    context_block = "\n\n---\n\n".join(context_parts)

    user_prompt = f"Context:\n{context_block}\n\n---\n\nQuestion: {query}"

    try:
        provider = _get_provider()
        answer, usage = await provider.complete(SYSTEM_PROMPT, user_prompt, MAX_TOKENS)
        return answer, usage
    except Exception as e:
        logger.error(f"LLM generation error: {e}")
        raise
