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


async def create_user(client: AsyncClient, email: str) -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123!", "display_name": "测试用户"},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def login(client: AsyncClient, email: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "StrongPass123!"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_auth_and_knowledge_base_crud(client: AsyncClient) -> None:
    email = f"crud-{uuid.uuid4().hex}@example.com"
    user = await create_user(client, email)

    duplicate = await client.post(
        "/api/v1/auth/register",
        json={"email": email.upper(), "password": "StrongPass123!"},
    )
    assert duplicate.status_code == 409

    token = await login(client, email)
    headers = {"Authorization": f"Bearer {token}"}

    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["id"] == user["id"]

    created = await client.post(
        "/api/v1/knowledge-bases",
        headers=headers,
        json={"name": "员工制度", "description": "测试知识库"},
    )
    assert created.status_code == 201
    knowledge_base = created.json()
    knowledge_base_id = knowledge_base["id"]
    assert knowledge_base["owner_id"] == user["id"]

    listed = await client.get("/api/v1/knowledge-bases", headers=headers)
    assert listed.status_code == 200
    assert any(item["id"] == knowledge_base_id for item in listed.json())

    updated = await client.patch(
        f"/api/v1/knowledge-bases/{knowledge_base_id}",
        headers=headers,
        json={"description": "更新后的描述"},
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "更新后的描述"

    deleted = await client.delete(f"/api/v1/knowledge-bases/{knowledge_base_id}", headers=headers)
    assert deleted.status_code == 204

    missing = await client.get(f"/api/v1/knowledge-bases/{knowledge_base_id}", headers=headers)
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_knowledge_base_isolation(client: AsyncClient) -> None:
    suffix = uuid.uuid4().hex
    email_a = f"owner-a-{suffix}@example.com"
    email_b = f"owner-b-{suffix}@example.com"
    await create_user(client, email_a)
    await create_user(client, email_b)
    token_a = await login(client, email_a)
    token_b = await login(client, email_b)

    created = await client.post(
        "/api/v1/knowledge-bases",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"name": "仅属于 A 的知识库"},
    )
    assert created.status_code == 201
    knowledge_base_id = created.json()["id"]

    accessed_by_b = await client.get(
        f"/api/v1/knowledge-bases/{knowledge_base_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert accessed_by_b.status_code == 404

    listed_by_b = await client.get(
        "/api/v1/knowledge-bases",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert listed_by_b.status_code == 200
    assert all(item["id"] != knowledge_base_id for item in listed_by_b.json())

    await client.delete(
        f"/api/v1/knowledge-bases/{knowledge_base_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )


