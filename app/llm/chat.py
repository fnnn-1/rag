from openai import AsyncOpenAI

from app.core.config import settings
from app.llm.prompts import build_rag_messages
from app.retrieval.hybrid_search import SearchResult


class LLMProvider:
    name = "base"

    async def generate(self, question: str, results: list[SearchResult]) -> str:
        raise NotImplementedError


class FallbackLLMProvider(LLMProvider):
    name = "extractive-fallback"

    async def generate(self, question: str, results: list[SearchResult]) -> str:
        if not results:
            return "知识库中未找到足够依据，无法准确回答该问题。"
        excerpts = []
        for index, result in enumerate(results, start=1):
            excerpts.append(f"[S{index}] {result.content}")
        return "根据知识库资料，相关内容如下：\n\n" + "\n\n".join(excerpts)


class OpenAICompatibleLLMProvider(LLMProvider):
    name = "openai-compatible"

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url or None,
            timeout=settings.llm_timeout_seconds,
        )

    async def generate(self, question: str, results: list[SearchResult]) -> str:
        response = await self.client.chat.completions.create(
            model=settings.llm_model,
            messages=build_rag_messages(question, results),
            temperature=0.1,
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("模型返回了空回答")
        return content.strip()


def get_llm_provider() -> LLMProvider:
    if settings.llm_api_key and settings.llm_model:
        return OpenAICompatibleLLMProvider()
    return FallbackLLMProvider()
