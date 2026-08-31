import argparse
import asyncio
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from time import perf_counter
from urllib.request import urlopen
import uuid

WORKSPACE = Path(__file__).resolve().parents[1]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from sqlalchemy import delete, func, select, update

from app.core.config import settings
from app.core.security import hash_password
from app.db.init_db import init_db
from app.db.session import SessionLocal, engine
from app.models import Document, DocumentChunk, IngestionJob, KnowledgeBase, User
from app.retrieval.hybrid_search import hybrid_search
from app.retrieval.reranker import rerank_results

DATA_URL = "https://raw.githubusercontent.com/hyintell/RetrievalQA/main/data/retrievalqa_gpt4.jsonl"
DATA_PATH = WORKSPACE / "data" / "evaluation" / "public_retrievalqa_gpt4.jsonl"
REPORT_JSON = WORKSPACE / "data" / "evaluation" / "public_retrievalqa_report.json"
REPORT_MD = WORKSPACE / "data" / "evaluation" / "public_retrievalqa_report.md"
PUBLIC_EMAIL = "public-retrievalqa-evaluation@demo.local"
PUBLIC_KB_NAME = "公开 RetrievalQA 评测知识库"


def ensure_dataset() -> list[dict]:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        with urlopen(DATA_URL, timeout=60) as response:
            DATA_PATH.write_bytes(response.read())
    return [json.loads(line) for line in DATA_PATH.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def context_parts(context: object) -> tuple[str, str]:
    if isinstance(context, dict):
        title = str(context.get("title") or "untitled")
        text = str(context.get("text") or "")
    else:
        title = str(context)
        text = str(context)
    content = f"{title}\n{text}".strip()
    return title, content


def stable_key(title: str, content: str) -> str:
    return hashlib.sha256(f"{title}\n{content}".encode("utf-8")).hexdigest()


def choose_rows(rows: list[dict], limit: int | None) -> list[dict]:
    if not limit or limit >= len(rows):
        return rows
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("data_source", "unknown"))].append(row)
    sources = sorted(grouped)
    selected: list[dict] = []
    for index in range(limit):
        source_rows = grouped[sources[index % len(sources)]]
        selected.append(source_rows[index // len(sources)])
    return selected


async def prepare(rows: list[dict]) -> KnowledgeBase:
    await init_db()
    upload_dir = settings.ensure_upload_dir()
    async with SessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == PUBLIC_EMAIL))
        if user is None:
            user = User(
                email=PUBLIC_EMAIL,
                password_hash=hash_password("EvaluationOnly123!"),
                display_name="公开 RetrievalQA 评测",
            )
            db.add(user)
            await db.flush()

        old_kb = await db.scalar(
            select(KnowledgeBase).where(
                KnowledgeBase.owner_id == user.id,
                KnowledgeBase.name == PUBLIC_KB_NAME,
            )
        )
        if old_kb is not None:
            await db.delete(old_kb)
            await db.commit()

        kb = KnowledgeBase(
            owner_id=user.id,
            name=PUBLIC_KB_NAME,
            description="来自公开 RetrievalQA 数据集的评测语料，仅用于检索基准测试。",
        )
        db.add(kb)
        await db.commit()
        await db.refresh(kb)

        unique_contexts: dict[str, tuple[str, str]] = {}
        for row in rows:
            for context in row.get("context", []):
                title, content = context_parts(context)
                key = stable_key(title, content)
                unique_contexts.setdefault(key, (title, content))

        provider = __import__("app.llm.embeddings", fromlist=["get_embedding_provider"]).get_embedding_provider()
        items = list(unique_contexts.items())
        try:
            for start in range(0, len(items), settings.embedding_batch_size):
                batch = items[start:start + settings.embedding_batch_size]
                embeddings = await provider.embed_documents([content for _, (_, content) in batch])
                for offset, ((key, (title, content)), embedding) in enumerate(zip(batch, embeddings, strict=True)):
                    index = start + offset
                    filename = f"public-{index:05d}-{title[:160]}"
                    document = Document(
                        knowledge_base_id=kb.id,
                        original_filename=filename,
                        storage_filename=f"{key}.txt",
                        storage_path=str(upload_dir / f"public-{key}.txt"),
                        file_type="txt",
                        content_type="text/plain",
                        file_size=len(content.encode("utf-8")),
                        status="completed",
                        extracted_text=content,
                        chunk_count=1,
                        processed_at=datetime.now(timezone.utc),
                    )
                    db.add(document)
                    await db.flush()
                    db.add(DocumentChunk(
                        document_id=document.id,
                        chunk_index=0,
                        content=content,
                        token_count=len(content),
                        embedding=embedding,
                    ))
                await db.flush()
                await db.execute(
                    update(DocumentChunk)
                    .where(DocumentChunk.document_id.in_(select(Document.id).where(Document.knowledge_base_id == kb.id)))
                    .where(DocumentChunk.search_vector.is_(None))
                    .values(search_vector=func.to_tsvector("simple", DocumentChunk.content))
                )
                await db.commit()
        finally:
            await provider.close()
        await db.refresh(kb)
        return kb


async def evaluate(rows: list[dict], kb: KnowledgeBase) -> dict:
    records = []
    async with SessionLocal() as db:
        for row in rows:
            started = perf_counter()
            results, provider_name = await hybrid_search(db, kb.id, row["question"], top_k=5)
            reranked = rerank_results(row["question"], results, top_k=5)
            retrieved_titles = [item.document_name for item in results]
            reranked_titles = [item.result.document_name for item in reranked]
            gold_titles = [context_parts(context)[0] for context in row.get("context", [])]
            gold_prefixes = [title[:160] for title in gold_titles]
            matches = [
                title for title in retrieved_titles
                if any(title.split("-", 2)[-1] == prefix for prefix in gold_prefixes)
            ]
            reciprocal_rank = 0.0
            for rank, title in enumerate(retrieved_titles, start=1):
                if title.split("-", 2)[-1] in gold_prefixes:
                    reciprocal_rank = 1.0 / rank
                    break
            hit = 1.0 if matches else 0.0
            recall = len(set(matches)) / len(set(gold_prefixes)) if gold_prefixes else 0.0
            precision = len(set(matches)) / len(set(retrieved_titles)) if retrieved_titles else 0.0
            records.append({
                "question_id": row.get("question_id"),
                "data_source": row.get("data_source", "unknown"),
                "question": row["question"],
                "ground_truth": row.get("ground_truth", []),
                "gold_context_count": len(gold_prefixes),
                "retrieved_documents": retrieved_titles,
                "reranked_documents": reranked_titles,
                "matched_gold_documents": matches,
                "hit_at_5": hit,
                "recall_at_5": recall,
                "precision_at_5": precision,
                "reciprocal_rank_at_5": reciprocal_rank,
                "latency_ms": round((perf_counter() - started) * 1000, 2),
                "embedding_provider": provider_name,
            })

    def avg(key: str) -> float:
        values = [record[key] for record in records]
        return round(sum(values) / len(values), 4) if values else 0.0

    by_source: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        by_source[record["data_source"]].append(record)
    source_metrics = {}
    for source, source_records in sorted(by_source.items()):
        source_metrics[source] = {
            "question_count": len(source_records),
            "hit_at_5": round(sum(x["hit_at_5"] for x in source_records) / len(source_records), 4),
            "recall_at_5": round(sum(x["recall_at_5"] for x in source_records) / len(source_records), 4),
            "mrr_at_5": round(sum(x["reciprocal_rank_at_5"] for x in source_records) / len(source_records), 4),
        }

    report = {
        "report_name": "公开 RetrievalQA 检索评测报告",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "dataset": {
            "name": "RetrievalQA",
            "file": DATA_PATH.name,
            "source_url": DATA_URL,
            "repository": "hyintell/RetrievalQA",
            "selected_question_count": len(rows),
            "available_question_count": 250,
        },
        "knowledge_base": {"id": str(kb.id), "name": kb.name},
        "metrics": {
            "question_count": len(records),
            "retrieval_hit_at_5": avg("hit_at_5"),
            "retrieval_recall_at_5": avg("recall_at_5"),
            "retrieval_precision_at_5": avg("precision_at_5"),
            "retrieval_mrr_at_5": avg("reciprocal_rank_at_5"),
            "average_latency_ms": round(sum(x["latency_ms"] for x in records) / len(records), 2) if records else 0.0,
            "source_metrics": source_metrics,
        },
        "records": records,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(report)
    return report


def pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def write_markdown(report: dict) -> None:
    m = report["metrics"]
    lines = [
        "# 公开 RetrievalQA 检索评测报告", "",
        f"- 生成时间：{report['generated_at']}",
        f"- 数据集：{report['dataset']['name']} / {report['dataset']['file']}",
        f"- 公开数据集来源：{report['dataset']['repository']}",
        f"- 本次评测问题数：{m['question_count']}",
        "",
        "## 检索指标", "",
        "| 指标 | 结果 |", "|---|---:|",
        f"| Retrieval Hit@5 | {pct(m['retrieval_hit_at_5'])} |",
        f"| Retrieval Recall@5 | {pct(m['retrieval_recall_at_5'])} |",
        f"| Retrieval Precision@5 | {pct(m['retrieval_precision_at_5'])} |",
        f"| MRR@5 | {m['retrieval_mrr_at_5']:.4f} |",
        f"| 平均检索耗时 | {m['average_latency_ms']:.2f} ms |",
        "",
        "## 数据源分类结果", "",
        "| 数据源 | 问题数 | Hit@5 | Recall@5 | MRR@5 |", "|---|---:|---:|---:|---:|",
    ]
    for source, values in m["source_metrics"].items():
        lines.append(
            f"| {source} | {values['question_count']} | {pct(values['hit_at_5'])} | "
            f"{pct(values['recall_at_5'])} | {values['mrr_at_5']:.4f} |"
        )
    lines += [
        "", "## 说明", "",
        "- 本次评测使用公开 RetrievalQA 仓库提供的 `retrievalqa_gpt4.jsonl` 选定样本文件。",
        "- 数据文件包含来自 RealTimeQA、FreshQA、ToolQA、PopQA 和 TriviaQA 的问题与上下文。",
        "- 本报告评估当前项目的检索器是否找回数据集提供的上下文标题，不评估聊天模型最终答案 EM/F1。",
        "- 评测语料由数据集中的上下文构建，因此指标用于比较检索管线，不等价于真实企业知识库效果。",
        "",
    ]
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


async def main(limit: int | None) -> None:
    rows = choose_rows(ensure_dataset(), limit)
    try:
        kb = await prepare(rows)
        report = await evaluate(rows, kb)
        print(json.dumps(report["metrics"], ensure_ascii=False, indent=2))
        print(f"JSON report: {REPORT_JSON}")
        print(f"Markdown report: {REPORT_MD}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="使用公开 RetrievalQA 数据集评测当前检索管线。")
    parser.add_argument("--limit", type=int, default=None, help="只抽取指定数量问题，按数据源轮转；默认使用文件中的 250 条。")
    args = parser.parse_args()
    asyncio.run(main(args.limit))
