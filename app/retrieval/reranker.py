from dataclasses import dataclass
import re

from app.retrieval.hybrid_search import SearchResult


@dataclass(slots=True)
class RerankedResult:
    result: SearchResult
    rerank_score: float
    lexical_overlap: float


def _features(text: str) -> set[str]:
    normalized = text.lower().strip()
    words = set(re.findall(r"[a-z0-9_]+", normalized))
    cjk = re.findall(r"[\u4e00-\u9fff]", normalized)
    words.update(cjk)
    words.update("".join(cjk[index:index + 2]) for index in range(max(0, len(cjk) - 1)))
    return words


def lexical_overlap(query: str, content: str) -> float:
    query_features = _features(query)
    if not query_features:
        return 0.0
    content_features = _features(content)
    return len(query_features & content_features) / len(query_features)


def rerank_results(query: str, results: list[SearchResult], top_k: int) -> list[RerankedResult]:
    reranked = []
    for result in results:
        overlap = lexical_overlap(query, result.content)
        vector_score = max(0.0, min(1.0, result.vector_score or 0.0))
        keyword_score = max(0.0, min(1.0, result.keyword_score or 0.0))
        score = 0.65 * overlap + 0.20 * vector_score + 0.15 * keyword_score
        reranked.append(RerankedResult(result=result, rerank_score=score, lexical_overlap=overlap))
    return sorted(reranked, key=lambda item: item.rerank_score, reverse=True)[:top_k]


def has_sufficient_evidence(results: list[RerankedResult], threshold: float = 0.12) -> bool:
    return bool(results and max(item.lexical_overlap for item in results) >= threshold)
