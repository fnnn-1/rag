import asyncio
import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.db.init_db import init_db
from app.main import app


pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    if os.getenv("RUN_DB_TESTS") != "1":
        pytest.skip("Set RUN_DB_TESTS=1 to run PostgreSQL integration tests")
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as test_client:
        yield test_client


async def setup_kb(client: AsyncClient) -> tuple[str, str]:
    email = f"chat-{uuid.uuid4().hex}@example.com"
    password = "StrongPass123!"
    register = await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert register.status_code == 201, register.text
    login = await client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    kb = await client.post("/api/v1/knowledge-bases", headers=headers, json={"name": "RAG 测试库"})
    assert kb.status_code == 201, kb.text
    upload = await client.post(
        f"/api/v1/knowledge-bases/{kb.json()['id']}/documents",
        headers=headers,
        files={
            "file": (
                "expense-policy.txt",
                "Expense reimbursement policy: transportation and hotel costs require valid receipts.".encode(),
                "text/plain",
            )
        },
    )
    assert upload.status_code == 202, upload.text
    document_id = upload.json()["document"]["id"]
    for _ in range(40):
        document = await client.get(f"/api/v1/documents/{document_id}", headers=headers)
        if document.json()["status"] == "completed":
            return token, kb.json()["id"]
        await asyncio.sleep(0.25)
    raise AssertionError("document did not complete")


@pytest.mark.asyncio
async def test_rag_answer_has_citations_and_conversation(client: AsyncClient) -> None:
    token, knowledge_base_id = await setup_kb(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        "/api/v1/chat/query",
        headers=headers,
        json={"knowledge_base_id": knowledge_base_id, "question": "What costs require valid receipts?"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["grounded"] is True
    assert body["citations"]
    assert body["citations"][0]["document_name"] == "expense-policy.txt"
    assert "[S1]" in body["answer"]
    assert body["llm_provider"] in {"extractive-fallback", "openai-compatible", "extractive-fallback-after-error"}
    assert body["retrieval_latency_ms"] >= 0
    assert body["generation_latency_ms"] >= 0

    follow_up = await client.post(
        "/api/v1/chat/query",
        headers=headers,
        json={
            "knowledge_base_id": knowledge_base_id,
            "question": "Which policy is this?",
            "conversation_id": body["conversation_id"],
        },
    )
    assert follow_up.status_code == 200, follow_up.text
    assert follow_up.json()["conversation_id"] == body["conversation_id"]


@pytest.mark.asyncio
async def test_rag_refuses_without_evidence(client: AsyncClient) -> None:
    token, knowledge_base_id = await setup_kb(client)
    response = await client.post(
        "/api/v1/chat/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"knowledge_base_id": knowledge_base_id, "question": "What is the company stock price?"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["grounded"] is False
    assert body["citations"] == []
    assert body["answer"] == "知识库中未找到足够依据，无法准确回答该问题。"
    assert body["llm_provider"] == "evidence-gate"
