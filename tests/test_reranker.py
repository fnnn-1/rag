from app.retrieval.hybrid_search import SearchResult
from app.retrieval.reranker import RerankedResult, has_sufficient_evidence, lexical_overlap, select_evidence


def test_lexical_overlap_and_evidence_gate():
    assert lexical_overlap("hotel receipts", "Hotel costs require valid receipts") > 0.5
    assert lexical_overlap("stock price", "Hotel costs require valid receipts") == 0
    assert has_sufficient_evidence([]) is False


def test_select_evidence_filters_weak_secondary_sources():
    base = SearchResult(
        chunk_id=__import__("uuid").uuid4(), document_id=__import__("uuid").uuid4(),
        document_name="a.md", content="content", page_number=None, section=None,
        vector_score=0.8, keyword_score=0.4, hybrid_score=0.03,
    )
    strong = RerankedResult(result=base, rerank_score=0.8, lexical_overlap=0.6)
    weak = RerankedResult(result=base, rerank_score=0.3, lexical_overlap=0.2)
    assert select_evidence([strong, weak]) == [strong]
    assert has_sufficient_evidence([RerankedResult(base, 0.2, 0.12)]) is False
