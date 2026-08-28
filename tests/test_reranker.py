from app.retrieval.reranker import has_sufficient_evidence, lexical_overlap


def test_lexical_overlap_and_evidence_gate():
    assert lexical_overlap("hotel receipts", "Hotel costs require valid receipts") > 0.5
    assert lexical_overlap("stock price", "Hotel costs require valid receipts") == 0
    assert has_sufficient_evidence([]) is False
