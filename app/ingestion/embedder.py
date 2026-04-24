import asyncio
import logging

from openai import AsyncOpenAI, RateLimitError

from app.config import settings

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
MODEL = "text-embedding-3-small"
BATCH_SIZE = 100
MAX_RETRIES = 3


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    all_embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        embeddings = await _embed_with_retry(batch)
        all_embeddings.extend(embeddings)

    return all_embeddings


async def _embed_with_retry(texts: list[str]) -> list[list[float]]:
    for attempt in range(MAX_RETRIES):
        try:
            response = await client.embeddings.create(model=MODEL, input=texts)
            return [item.embedding for item in response.data]
        except RateLimitError as e:
            if attempt < MAX_RETRIES - 1:
                wait_time = 2**attempt
                logger.warning(
                    f"Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1}/{MAX_RETRIES})"
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error("Max retries exceeded for embedding request")
                raise e
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise e

    return []
