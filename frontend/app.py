import json
import os
from pathlib import Path

import requests
import streamlit as st

st.set_page_config(page_title="企业智能知识库", page_icon="📚", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.6rem; max-width: 1280px;}
    [data-testid="stSidebar"] {background: #f6f8fc;}
    .hero {padding: 1.3rem 1.5rem; border-radius: 18px; color: white;
           background: linear-gradient(120deg, #173b72, #315fa8 58%, #4d7bc3); margin-bottom: 1rem;}
    .hero h1 {margin: 0; font-size: 2rem;}
    .hero p {margin: .45rem 0 0; opacity: .88;}
    .source-card {border-left: 4px solid #315fa8; background: #f7f9fd; padding: .85rem 1rem;
                  border-radius: 8px; margin: .5rem 0;}
    .muted {color: #667085; font-size: .9rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

DEFAULT_API_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
current_api_url = st.session_state.get("api_base_url", DEFAULT_API_URL)
if current_api_url in {"http://localhost:8000", "http://127.0.0.1:8000"} and DEFAULT_API_URL != "http://localhost:8000":
    current_api_url = DEFAULT_API_URL
API_BASE_URL = current_api_url.rstrip("/")
st.session_state["api_base_url"] = API_BASE_URL
REPORT_PATH = Path("/workspace/data/evaluation/latest_report.json")


def api_request(method: str, path: str, **kwargs):
    headers = kwargs.pop("headers", {})
    token = st.session_state.get("access_token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        return requests.request(method, f"{API_BASE_URL}{path}", headers=headers, timeout=90, **kwargs)
    except requests.RequestException as exc:
        st.error(f"无法连接 API：{exc}")
        return None


def show_error(response, fallback: str) -> None:
    if response is None:
        return
    try:
        detail = response.json().get("detail", fallback)
    except ValueError:
        detail = fallback
    st.error(detail)


def auth_panel() -> None:
    st.markdown('<div class="hero"><h1>📚 企业智能知识库</h1><p>文档解析 · 混合检索 · RAG 问答 · 引用溯源</p></div>', unsafe_allow_html=True)
    left, center, right = st.columns([1, 1.25, 1])
    with center:
        mode = st.segmented_control("账号操作", ["登录", "注册"], default="登录")
        with st.form("auth_form"):
            email = st.text_input("邮箱", placeholder="name@example.com")
            password = st.text_input("密码", type="password", placeholder="至少 8 位")
            display_name = st.text_input("显示名称") if mode == "注册" else None
            submitted = st.form_submit_button(mode, type="primary", use_container_width=True)
        if not submitted:
            return
        if mode == "注册":
            response = api_request("POST", "/api/v1/auth/register", json={"email": email, "password": password, "display_name": display_name})
            if response is not None and response.ok:
                st.success("注册成功，请切换到登录。")
            else:
                show_error(response, "注册失败")
        else:
            response = api_request("POST", "/api/v1/auth/login", data={"username": email, "password": password})
            if response is not None and response.ok:
                body = response.json()
                st.session_state["access_token"] = body["access_token"]
                st.session_state["current_user"] = body["user"]
                st.rerun()
            else:
                show_error(response, "登录失败")


def fetch_knowledge_bases() -> list[dict]:
    response = api_request("GET", "/api/v1/knowledge-bases")
    return response.json() if response is not None and response.ok else []


def fetch_documents(knowledge_base_id: str) -> list[dict]:
    response = api_request("GET", f"/api/v1/knowledge-bases/{knowledge_base_id}/documents")
    return response.json() if response is not None and response.ok else []


def create_knowledge_base_panel() -> None:
    with st.sidebar.expander("＋ 新建知识库"):
        with st.form("create_kb"):
            name = st.text_input("名称", placeholder="员工制度知识库")
            description = st.text_area("描述", placeholder="知识库用途说明")
            submitted = st.form_submit_button("创建", type="primary", use_container_width=True)
        if submitted:
            response = api_request("POST", "/api/v1/knowledge-bases", json={"name": name, "description": description or None})
            if response is not None and response.ok:
                st.success("创建成功")
                st.rerun()
            else:
                show_error(response, "创建失败")


def render_chat(knowledge_base: dict) -> None:
    knowledge_base_id = knowledge_base["id"]
    state_key = f"chat_history_{knowledge_base_id}"
    conversation_key = f"conversation_{knowledge_base_id}"
    history = st.session_state.setdefault(state_key, [])

    toolbar_left, toolbar_right = st.columns([5, 1])
    toolbar_left.markdown("### 与知识库对话")
    if toolbar_right.button("清空对话", key=f"clear-chat-{knowledge_base_id}", use_container_width=True):
        st.session_state[state_key] = []
        st.session_state.pop(conversation_key, None)
        st.rerun()

    if not history:
        st.info("回答将严格基于已完成处理的文档；没有足够证据时系统会拒答。")
    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("citations"):
                with st.expander(f"引用来源（{len(message['citations'])}）"):
                    for citation in message["citations"]:
                        location = f" · 第 {citation['page_number']} 页" if citation.get("page_number") else ""
                        st.markdown(
                            f'<div class="source-card"><strong>[S{citation["citation_index"]}] '
                            f'{citation["document_name"]}</strong>{location}<br><span class="muted">'
                            f'{citation["content"]}</span></div>',
                            unsafe_allow_html=True,
                        )
            if message.get("meta"):
                st.caption(message["meta"])

    question = st.chat_input("向当前知识库提问……", key=f"chat-input-{knowledge_base_id}")
    if not question:
        return
    history.append({"role": "user", "content": question})
    with st.spinner("正在检索资料并生成回答……"):
        response = api_request(
            "POST",
            "/api/v1/chat/query",
            json={
                "knowledge_base_id": knowledge_base_id,
                "question": question,
                "conversation_id": st.session_state.get(conversation_key),
                "top_k": 3,
            },
        )
    if response is None or not response.ok:
        history.append({"role": "assistant", "content": "问答请求失败，请检查服务日志。"})
        show_error(response, "问答失败")
        st.rerun()
    result = response.json()
    st.session_state[conversation_key] = result["conversation_id"]
    status = "已基于证据" if result["grounded"] else "证据不足，已拒答"
    history.append({
        "role": "assistant",
        "content": result["answer"],
        "citations": result["citations"],
        "meta": (
            f"{status} · {result['llm_provider']} · 检索 {result['retrieval_latency_ms']} ms · "
            f"生成 {result['generation_latency_ms']} ms · Trace {result['trace_id'][:10]}"
        ),
    })
    st.rerun()


def render_documents(knowledge_base: dict, documents: list[dict]) -> None:
    knowledge_base_id = knowledge_base["id"]
    st.markdown("### 文档管理")
    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "上传资料",
            type=["pdf", "docx", "md", "markdown", "txt"],
            help="支持 PDF、DOCX、Markdown、TXT，单文件最大 20 MB。",
            key=f"upload-{knowledge_base_id}",
        )
        col1, col2 = st.columns([1, 4])
        if col1.button("开始处理", type="primary", key=f"submit-{knowledge_base_id}", disabled=uploaded_file is None):
            response = api_request(
                "POST",
                f"/api/v1/knowledge-bases/{knowledge_base_id}/documents",
                files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
            )
            if response is not None and response.status_code == 202:
                st.success("文档已进入异步处理队列。")
                st.rerun()
            else:
                show_error(response, "文档上传失败")
        if col2.button("刷新状态", key=f"refresh-{knowledge_base_id}"):
            st.rerun()

    if not documents:
        st.info("当前知识库还没有文档。")
        return
    status_map = {"queued": "排队中", "processing": "处理中", "completed": "已完成", "failed": "失败"}
    for document in documents:
        with st.container(border=True):
            cols = st.columns([5, 1.3, 1.2, 1])
            cols[0].markdown(f"**{document['original_filename']}**")
            cols[0].caption(f"{document['file_type'].upper()} · {document['file_size'] / 1024:.1f} KB")
            cols[1].write(status_map.get(document["status"], document["status"]))
            cols[2].write(f"{document['chunk_count']} 个分块")
            if cols[3].button("删除", key=f"delete-doc-{document['id']}", use_container_width=True):
                response = api_request("DELETE", f"/api/v1/documents/{document['id']}")
                if response is not None and response.status_code == 204:
                    st.rerun()
                show_error(response, "删除失败")
            if document.get("error_message"):
                st.error(document["error_message"])


def render_evaluation() -> None:
    st.markdown("### RAG 量化评测")
    if not REPORT_PATH.exists():
        st.info("尚未生成评测报告。请在项目目录执行：docker exec kb-api python scripts/evaluate_rag.py")
        return
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    metrics = report["metrics"]
    row1 = st.columns(4)
    row1[0].metric("Hit@5", f"{metrics['retrieval_hit_at_5'] * 100:.1f}%")
    row1[1].metric("Recall@5", f"{metrics['retrieval_recall_at_5'] * 100:.1f}%")
    row1[2].metric("MRR@5", f"{metrics['retrieval_mrr_at_5']:.3f}")
    row1[3].metric("平均耗时", f"{metrics['average_latency_ms']:.0f} ms")
    row2 = st.columns(4)
    row2[0].metric("引用准确率", f"{metrics['citation_precision'] * 100:.1f}%")
    row2[1].metric("引用覆盖率", f"{metrics['citation_coverage'] * 100:.1f}%")
    row2[2].metric("拒答通过率", f"{metrics['refusal_accuracy'] * 100:.1f}%")
    row2[3].metric("答案词覆盖", f"{metrics['expected_term_coverage'] * 100:.1f}%")
    st.caption(f"生成时间：{report['generated_at']} · 评测问题：{metrics['question_count']} 条")

    category_rows = []
    for name, values in metrics["category_metrics"].items():
        score = values.get("hit_at_5", values.get("refusal_accuracy", 0))
        category_rows.append({"分类": name, "问题数": values["question_count"], "得分": f"{score * 100:.1f}%"})
    st.dataframe(category_rows, use_container_width=True, hide_index=True)
    with st.expander("查看失败样例"):
        failures = [
            record for record in report["records"]
            if (record["answerable"] and not set(record["expected_documents"]) & set(record["retrieved_documents"][:5]))
            or (not record["answerable"] and record["grounded"])
        ]
        if not failures:
            st.success("本次评测没有失败样例。")
        else:
            st.dataframe(failures, use_container_width=True, hide_index=True)


def application() -> None:
    user = st.session_state.get("current_user", {})
    st.sidebar.markdown("## 📚 企业知识库")
    st.sidebar.caption(user.get("display_name") or user.get("email", ""))
    create_knowledge_base_panel()
    st.sidebar.divider()
    if st.sidebar.button("退出登录", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    knowledge_bases = fetch_knowledge_bases()
    st.markdown('<div class="hero"><h1>企业知识中心</h1><p>集中管理企业资料，并通过可追溯的 RAG 问答快速获得答案。</p></div>', unsafe_allow_html=True)
    if not knowledge_bases:
        st.info("请从左侧创建第一个知识库。")
        return

    selected_name = st.selectbox("当前知识库", [item["name"] for item in knowledge_bases])
    knowledge_base = next(item for item in knowledge_bases if item["name"] == selected_name)
    documents = fetch_documents(knowledge_base["id"])
    completed = sum(document["status"] == "completed" for document in documents)
    metrics = st.columns(4)
    metrics[0].metric("知识库", len(knowledge_bases))
    metrics[1].metric("当前文档", len(documents))
    metrics[2].metric("已完成", completed)
    metrics[3].metric("可检索分块", sum(document["chunk_count"] for document in documents))

    chat_tab, docs_tab, settings_tab, evaluation_tab = st.tabs(["💬 智能问答", "📄 文档管理", "⚙️ 知识库设置", "📊 评测报告"])
    with chat_tab:
        render_chat(knowledge_base)
    with docs_tab:
        render_documents(knowledge_base, documents)
    with settings_tab:
        st.markdown(f"### {knowledge_base['name']}")
        st.write(knowledge_base.get("description") or "暂无描述")
        st.caption(f"知识库 ID：{knowledge_base['id']}")
        if st.button("删除当前知识库", type="secondary"):
            response = api_request("DELETE", f"/api/v1/knowledge-bases/{knowledge_base['id']}")
            if response is not None and response.status_code == 204:
                st.rerun()
            show_error(response, "删除失败")
    with evaluation_tab:
        render_evaluation()


if st.session_state.get("access_token"):
    application()
else:
    auth_panel()
