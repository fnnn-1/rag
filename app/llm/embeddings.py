from hashlib import sha256
import math
import re

from openai import AsyncOpenAI

from app.core.config import settings


class EmbeddingProvider:
    name = "base"

    async def close(self) -> None:
        return None

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    async def embed_query(self, text: str) -> list[float]:
        result = await self.embed_documents([text])
        return result[0]


class HashEmbeddingProvider(EmbeddingProvider):
    name = "hash-fallback"

    def __init__(self, dimensions: int):
        self.dimensions = dimensions

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        normalized = text.lower().strip()
        tokens = re.findall(r"[\w]+|[^\s]", normalized, flags=re.UNICODE)
        features = tokens + [normalized[index:index + 2] for index in range(max(0, len(normalized) - 1))]
        for feature in features:
            digest = sha256(feature.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]


class OpenAIEmbeddingProvider(EmbeddingProvider):
    name = "openai-compatible"

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.embedding_api_key,
            base_url=settings.embedding_base_url or settings.llm_base_url or None,
            timeout=settings.embedding_timeout_seconds,
        )

    async def close(self) -> None:
        await self.client.close()

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), settings.embedding_batch_size):
            batch = texts[start:start + settings.embedding_batch_size]
            response = await self.client.embeddings.create(model=settings.embedding_model, input=batch)
            ordered = sorted(response.data, key=lambda item: item.index)
            vectors.extend([item.embedding for item in ordered])
        return vectors


def get_embedding_provider() -> EmbeddingProvider:
    if settings.embedding_api_key and settings.embedding_model:
        return OpenAIEmbeddingProvider()
    return HashEmbeddingProvider(settings.embedding_dimensions)
