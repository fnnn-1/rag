import argparse
import asyncio
from datetime import datetime
import json
from pathlib import Path
import shutil
import sys
from time import perf_counter
import uuid

WORKSPACE = Path(__file__).resolve().parents[1]
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.init_db import init_db
from app.db.session import SessionLocal, engine
from app.evaluation.metrics import compute_metrics
from app.models import Document, IngestionJob, KnowledgeBase, User
from app.retrieval.hybrid_search import hybrid_search
from app.retrieval.reranker import has_sufficient_evidence, rerank_results, select_evidence
from app.tasks.document_tasks import _process_document
SEED_DIR = WORKSPACE / "data" / "seed" / "company_policies"
DATASET_PATH = WORKSPACE / "data" / "evaluation" / "eval_dataset.json"
REPORT_JSON = WORKSPACE / "data" / "evaluation" / "latest_report.json"
REPORT_MD = WORKSPACE / "data" / "evaluation" / "latest_report.md"
EVALUATION_EMAIL = "rag-evaluation@demo.local"
EVALUATION_KB_NAME = "企业制度演示知识库"


async def prepare_demo_knowledge_base() -> tuple[User, KnowledgeBase]:
    await init_db()
    upload_dir = settings.ensure_upload_dir()
    async with SessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == EVALUATION_EMAIL))
        if user is None:
            user = User(
                email=EVALUATION_EMAIL,
                password_hash=hash_password("EvaluationOnly123!"),
                display_name="RAG 自动评测",
            )
            db.add(user)
            await db.flush()

        existing = await db.scalar(
            select(KnowledgeBase).where(
                KnowledgeBase.owner_id == user.id,
                KnowledgeBase.name == EVALUATION_KB_NAME,
            )
        )
        if existing is not None:
            storage_paths = list(
                (await db.scalars(select(Document.storage_path).where(Document.knowledge_base_id == existing.id))).all()
            )
            await db.delete(existing)
            await db.commit()
            for raw_path in storage_paths:
                path = Path(raw_path)
                try:
                    path.relative_to(upload_dir)
                except ValueError:
                    continue
                path.unlink(missing_ok=True)
            user = await db.scalar(select(User).where(User.email == EVALUATION_EMAIL))

        knowledge_base = KnowledgeBase(
            owner_id=user.id,
            name=EVALUATION_KB_NAME,
            description="由第六天评测脚本自动创建的虚构企业制度知识库。",
        )
        db.add(knowledge_base)
        await db.commit()
        await db.refresh(knowledge_base)

        for source in sorted(SEED_DIR.glob("*.md")):
            storage_filename = f"eval-{uuid.uuid4()}{source.suffix}"
            storage_path = upload_dir / storage_filename
            shutil.copyfile(source, storage_path)
            document = Document(
                knowledge_base_id=knowledge_base.id,
                original_filename=source.name,
                storage_filename=storage_filename,
                storage_path=str(storage_path),
                file_type="md",
                content_type="text/markdown",
                file_size=storage_path.stat().st_size,
                status="queued",
            )
            db.add(document)
            await db.flush()
            job = IngestionJob(document_id=document.id, status="queued")
            db.add(job)
            await db.commit()
            await _process_document(str(document.id), str(job.id))

        return user, knowledge_base


async def find_demo_knowledge_base() -> tuple[User, KnowledgeBase]:
    await init_db()
    async with SessionLocal() as db:
        row = (
            await db.execute(
                select(User, KnowledgeBase)
                .join(KnowledgeBase, KnowledgeBase.owner_id == User.id)
                .where(User.email == EVALUATION_EMAIL, KnowledgeBase.name == EVALUATION_KB_NAME)
            )
        ).first()
        if row is None:
            raise RuntimeError("未找到演示知识库，请先使用默认模式运行评测脚本。")
        return row[0], row[1]


def term_coverage(expected_terms: list[str], contents: list[str]) -> float:
    if not expected_terms:
        return 1.0
    combined = "\n".join(contents).replace(" ", "")
    return sum(term.replace(" ", "") in combined for term in expected_terms) / len(expected_terms)


async def evaluate(knowledge_base: KnowledgeBase) -> dict:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    records = []
    async with SessionLocal() as db:
        for item in dataset["items"]:
            started = perf_counter()
            results, provider_name = await hybrid_search(db, knowledge_base.id, item["question"], top_k=5)
            reranked = rerank_results(item["question"], results, top_k=5)
            evidence = select_evidence(reranked)
            grounded = has_sufficient_evidence(evidence)
            citations = evidence[:3] if grounded else []
            latency_ms = round((perf_counter() - started) * 1000, 2)
            records.append({
                "id": item["id"],
                "category": item["category"],
                "question": item["question"],
                "answerable": item["answerable"],
                "expected_documents": item["expected_documents"],
                "expected_terms": item["expected_terms"],
                "retrieved_documents": [result.document_name for result in results],
                "cited_documents": [citation.result.document_name for citation in citations],
                "grounded": grounded,
                "term_coverage": term_coverage(
                    item["expected_terms"], [citation.result.content for citation in citations]
                ) if item["answerable"] else 1.0,
                "latency_ms": latency_ms,
                "embedding_provider": provider_name,
            })

    metrics = compute_metrics(records)
    report = {
        "report_name": "企业级智能知识库 RAG 评测报告",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "dataset": {
            "name": dataset["name"],
            "version": dataset["version"],
            "question_count": len(dataset["items"]),
        },
        "knowledge_base": {
            "id": str(knowledge_base.id),
            "name": knowledge_base.name,
            "document_count": len(list(SEED_DIR.glob("*.md"))),
        },
        "metrics": metrics,
        "records": records,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown_report(report)
    return report


def pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def write_markdown_report(report: dict) -> None:
    metrics = report["metrics"]
    lines = [
        "# 企业级智能知识库 RAG 评测报告",
        "",
        f"- 生成时间：{report['generated_at']}",
        f"- 评测集：{report['dataset']['name']} v{report['dataset']['version']}",
        f"- 问题数量：{metrics['question_count']}（可回答 {metrics['answerable_count']}，知识库外 {metrics['unanswerable_count']}）",
        f"- 演示文档：{report['knowledge_base']['document_count']} 份",
        "",
        "## 核心指标",
        "",
        "| 指标 | 结果 |",
        "|---|---:|",
        f"| Retrieval Hit@5 | {pct(metrics['retrieval_hit_at_5'])} |",
        f"| Retrieval Recall@5 | {pct(metrics['retrieval_recall_at_5'])} |",
        f"| MRR@5 | {metrics['retrieval_mrr_at_5']:.4f} |",
        f"| 引用准确率 | {pct(metrics['citation_precision'])} |",
        f"| 引用覆盖率 | {pct(metrics['citation_coverage'])} |",
        f"| 关键答案词覆盖率 | {pct(metrics['expected_term_coverage'])} |",
        f"| 可回答问题证据通过率 | {pct(metrics['answerable_grounded_rate'])} |",
        f"| 知识库外问题拒答通过率 | {pct(metrics['refusal_accuracy'])} |",
        f"| 平均检索与重排序耗时 | {metrics['average_latency_ms']:.2f} ms |",
        "",
        "## 分类结果",
        "",
        "| 分类 | 问题数 | 指标 |",
        "|---|---:|---:|",
    ]
    for category, values in metrics["category_metrics"].items():
        metric = values.get("hit_at_5", values.get("refusal_accuracy", 0.0))
        lines.append(f"| {category} | {values['question_count']} | {pct(metric)} |")
    lines += [
        "",
        "## 说明",
        "",
        "- 检索指标使用混合检索和重排序后的 Top 5 结果计算。",
        "- 引用准确率根据证据门控后选中的来源文档与标准相关文档计算。",
        "- 拒答通过率衡量知识库外问题是否被证据门控正确拒绝。",
        "- 本报告不调用聊天大模型生成答案，因此可重复运行且不产生额外对话模型费用。",
        "",
    ]
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


async def main(skip_prepare: bool) -> None:
    try:
        if skip_prepare:
            _, knowledge_base = await find_demo_knowledge_base()
        else:
            _, knowledge_base = await prepare_demo_knowledge_base()
        report = await evaluate(knowledge_base)
        print(json.dumps(report["metrics"], ensure_ascii=False, indent=2))
        print(f"JSON report: {REPORT_JSON}")
        print(f"Markdown report: {REPORT_MD}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="准备演示知识库并运行 RAG 检索评测。")
    parser.add_argument("--skip-prepare", action="store_true", help="复用现有演示知识库，仅重新运行评测。")
    args = parser.parse_args()
    asyncio.run(main(args.skip_prepare))
