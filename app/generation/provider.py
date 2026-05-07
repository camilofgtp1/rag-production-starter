import asyncio
import logging
from typing import List, Protocol, Tuple

from openai import AsyncOpenAI, RateLimitError

from app.config import settings

logger = logging.getLogger(__name__)


class ModelProvider(Protocol):
    """
    Protocol (not ABC) defining the interface for LLM providers.

    Why Protocol over ABC:
    - Structural subtyping: any object with these methods satisfies the protocol
      without needing to inherit from a base class. This lets us wrap third-party
      SDKs (OpenAI, Anthropic, etc.) without forcing them into our class hierarchy.
    - Zero runtime overhead: Protocols are purely a type-checking construct.
    - Easier testing: mock objects only need to match the shape, not inherit.

    To add a second provider (e.g. AnthropicProvider):
      1. Create a class that implements `complete()` and `embed()`
      2. Add it to the `get_provider()` factory below
      3. Set `MODEL_PROVIDER=anthropic` in .env
    """

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1000,
    ) -> Tuple[str, dict]: ...

    async def embed(self, texts: List[str]) -> List[List[float]]: ...


class OpenAIProvider:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1000,
    ) -> Tuple[str, dict]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
        )
        answer = response.choices[0].message.content
        usage = (
            response.usage.model_dump()
            if response.usage
            else {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
        )
        return answer, usage

    async def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        all_embeddings: List[List[float]] = []
        batch_size = 100

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embeddings = await self._embed_with_retry(batch)
            all_embeddings.extend(embeddings)

        return all_embeddings

    async def _embed_with_retry(self, texts: List[str]) -> List[List[float]]:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self.client.embeddings.create(
                    model=self.embedding_model, input=texts
                )
                return [item.embedding for item in response.data]
            except RateLimitError as e:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    logger.warning(
                        f"Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("Max retries exceeded for embedding request")
                    raise e
            except Exception as e:
                logger.error(f"Embedding error: {e}")
                raise e

        return []


def get_provider() -> ModelProvider:
    """Factory: returns the provider implementation matching MODEL_PROVIDER config."""
    provider_name = settings.MODEL_PROVIDER
    if provider_name == "openai":
        return OpenAIProvider()
    raise ValueError(f"Unknown provider: {provider_name}")
