from app.evaluation.metrics import compute_metrics


def test_compute_metrics():
    records = [
        {
            "category": "制度",
            "answerable": True,
            "expected_documents": ["a.md"],
            "retrieved_documents": ["a.md", "b.md"],
            "cited_documents": ["a.md"],
            "grounded": True,
            "term_coverage": 1.0,
            "latency_ms": 10,
        },
        {
            "category": "知识库外",
            "answerable": False,
            "expected_documents": [],
            "retrieved_documents": ["b.md"],
            "cited_documents": [],
            "grounded": False,
            "term_coverage": 1.0,
            "latency_ms": 20,
        },
    ]
    metrics = compute_metrics(records)
    assert metrics["retrieval_hit_at_5"] == 1.0
    assert metrics["retrieval_recall_at_5"] == 1.0
    assert metrics["retrieval_mrr_at_5"] == 1.0
    assert metrics["citation_precision"] == 1.0
    assert metrics["refusal_accuracy"] == 1.0
    assert metrics["average_latency_ms"] == 15.0
