import logging
from typing import Dict, List

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
MODEL = "gpt-4o-mini"
MAX_TOKENS = 1000

SYSTEM_PROMPT = """You are a precise assistant. Answer the user's question using ONLY the provided context. If the context does not contain enough information to answer, respond with: 'I don't have enough information in the provided documents to answer this.' Always reference the source filename when you use information from it."""


async def generate_answer(query: str, context_chunks: List[Dict]) -> str:
    context_parts = []
    for chunk in context_chunks:
        context_parts.append(
            f"[Source: {chunk.get('filename', 'unknown')}]\n{chunk.get('text', '')}"
        )

    context_block = "\n\n---\n\n".join(context_parts)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Context:\n{context_block}\n\n---\n\nQuestion: {query}",
        },
    ]

    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM generation error: {e}")
        raise
