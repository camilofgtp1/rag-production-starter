import logging

from app.generation.provider import get_provider

logger = logging.getLogger(__name__)

_provider = None


def _get_provider():
    global _provider
    if _provider is None:
        _provider = get_provider()
    return _provider


async def embed_texts(texts: list[str]) -> list[list[float]]:
    provider = _get_provider()
    return await provider.embed(texts)
