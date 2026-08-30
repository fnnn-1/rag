from collections import defaultdict
from statistics import mean


def _round(value: float) -> float:
    return round(value, 4)


def compute_metrics(records: list[dict]) -> dict:
    answerable = [record for record in records if record["answerable"]]
    unanswerable = [record for record in records if not record["answerable"]]

    hit_values = []
    recall_values = []
    reciprocal_ranks = []
    citation_precisions = []
    citation_coverages = []
    term_coverages = []
    grounded_values = []

    for record in answerable:
        expected = set(record["expected_documents"])
        retrieved = record["retrieved_documents"][:5]
        retrieved_set = set(retrieved)
        relevant_retrieved = expected & retrieved_set
        hit_values.append(1.0 if relevant_retrieved else 0.0)
        recall_values.append(len(relevant_retrieved) / len(expected) if expected else 0.0)
        reciprocal_rank = 0.0
        for rank, document in enumerate(retrieved, start=1):
            if document in expected:
                reciprocal_rank = 1.0 / rank
                break
        reciprocal_ranks.append(reciprocal_rank)

        cited = record["cited_documents"]
        relevant_citations = sum(1 for document in cited if document in expected)
        citation_precisions.append(relevant_citations / len(cited) if cited else 0.0)
        citation_coverages.append(1.0 if relevant_citations else 0.0)
        term_coverages.append(record.get("term_coverage", 0.0))
        grounded_values.append(1.0 if record["grounded"] else 0.0)

    refusal_values = [1.0 if not record["grounded"] else 0.0 for record in unanswerable]
    latency_values = [record["latency_ms"] for record in records]

    by_category: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_category[record["category"]].append(record)

    category_metrics = {}
    for category, category_records in sorted(by_category.items()):
        category_answerable = [record for record in category_records if record["answerable"]]
        if category_answerable:
            hits = []
            for record in category_answerable:
                hits.append(bool(set(record["expected_documents"]) & set(record["retrieved_documents"][:5])))
            category_metrics[category] = {
                "question_count": len(category_records),
                "hit_at_5": _round(mean(hits)),
            }
        else:
            category_metrics[category] = {
                "question_count": len(category_records),
                "refusal_accuracy": _round(mean(not record["grounded"] for record in category_records)),
            }

    return {
        "question_count": len(records),
        "answerable_count": len(answerable),
        "unanswerable_count": len(unanswerable),
        "retrieval_hit_at_5": _round(mean(hit_values)) if hit_values else 0.0,
        "retrieval_recall_at_5": _round(mean(recall_values)) if recall_values else 0.0,
        "retrieval_mrr_at_5": _round(mean(reciprocal_ranks)) if reciprocal_ranks else 0.0,
        "citation_precision": _round(mean(citation_precisions)) if citation_precisions else 0.0,
        "citation_coverage": _round(mean(citation_coverages)) if citation_coverages else 0.0,
        "expected_term_coverage": _round(mean(term_coverages)) if term_coverages else 0.0,
        "answerable_grounded_rate": _round(mean(grounded_values)) if grounded_values else 0.0,
        "refusal_accuracy": _round(mean(refusal_values)) if refusal_values else 0.0,
        "average_latency_ms": round(mean(latency_values), 2) if latency_values else 0.0,
        "category_metrics": category_metrics,
    }
