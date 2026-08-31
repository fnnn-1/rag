import json
import os
from pathlib import Path

import requests
import streamlit as st

st.set_page_config(
    page_title="企业智能知识库",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

DEFAULT_API_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_BASE_URL = st.session_state.get("api_base_url", DEFAULT_API_URL).rstrip("/")
if API_BASE_URL in {"http://localhost:8000", "http://127.0.0.1:8000"} and DEFAULT_API_URL != "http://localhost:8000":
    API_BASE_URL = DEFAULT_API_URL.rstrip("/")
st.session_state["api_base_url"] = API_BASE_URL

LOCAL_REPORT_PATH = Path("/workspace/data/evaluation/latest_report.json")
PUBLIC_REPORT_PATH = Path("/workspace/data/evaluation/public_retrievalqa_report.json")

st.markdown(
    """
    <style>
    :root {
        --ink: #172033;
        --muted: #667085;
        --line: #e7ebf2;
        --surface: #ffffff;
        --canvas: #f5f7fb;
        --brand: #3b5ccc;
        --brand-dark: #21377f;
        --success: #137a55;
        --warning: #a15c00;
    }
    .stApp { background: var(--canvas); color: var(--ink); }
    [data-testid="stSidebar"] { background: #101a36; border-right: 0; }
    [data-testid="stSidebar"] * { color: #e8edff; }
    [data-testid="stSidebar"] .stCaption { color: #9caad1; }
    [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.13); }
    .block-container { max-width: 1380px; padding: 1.5rem 2.2rem 3rem; }
    .brand-mark { display:flex; align-items:center; gap:.65rem; margin:.2rem 0 1.5rem; }
    .brand-icon { width:36px; height:36px; display:grid; place-items:center; border-radius:11px; background:linear-gradient(135deg,#6e83ff,#3b5ccc); font-size:20px; box-shadow:0 8px 18px rgba(0,0,0,.2); }
    .brand-name { font-size:1.08rem; font-weight:750; letter-spacing:.01em; }
    .sidebar-label { color:#93a5d8 !important; font-size:.72rem; font-weight:700; letter-spacing:.09em; text-transform:uppercase; margin:1.1rem 0 .45rem; }
    .hero { position:relative; overflow:hidden; border-radius:24px; padding:1.65rem 1.85rem; color:#fff; background: radial-gradient(circle at 90% 15%, rgba(126,153,255,.45), transparent 28%), linear-gradient(115deg,#1c2d67 0%,#344fa2 63%,#5674d3 100%); box-shadow:0 14px 35px rgba(37,57,124,.16); margin-bottom:1rem; }
    .hero:after { content:""; position:absolute; width:220px; height:220px; right:-70px; bottom:-120px; border:1px solid rgba(255,255,255,.18); border-radius:50%; box-shadow:0 0 0 20px rgba(255,255,255,.04),0 0 0 42px rgba(255,255,255,.03); }
    .hero h1 { margin:0; font-size:2rem; font-weight:780; letter-spacing:-.03em; }
    .hero p { margin:.5rem 0 0; color:#dce5ff; font-size:.96rem; }
    .hero-meta { margin-top:1.1rem; display:flex; flex-wrap:wrap; gap:.55rem; }
    .hero-chip { padding:.35rem .7rem; border-radius:999px; border:1px solid rgba(255,255,255,.2); background:rgba(255,255,255,.1); color:#eef2ff; font-size:.78rem; }
    .section-title { color:var(--ink); font-size:1.08rem; font-weight:760; margin:.4rem 0 .8rem; }
    .section-subtitle { color:var(--muted); font-size:.86rem; margin:-.45rem 0 1rem; }
    .metric-card { background:var(--surface); border:1px solid var(--line); border-radius:16px; padding:1rem 1.1rem; min-height:100px; box-shadow:0 5px 15px rgba(16,24,40,.035); }
    .metric-label { color:var(--muted); font-size:.78rem; }
    .metric-value { color:var(--ink); font-size:1.55rem; font-weight:780; margin-top:.35rem; letter-spacing:-.02em; }
    .metric-hint { color:#98a2b3; font-size:.72rem; margin-top:.25rem; }
    .surface { background:var(--surface); border:1px solid var(--line); border-radius:18px; padding:1.1rem 1.2rem; box-shadow:0 5px 15px rgba(16,24,40,.035); }
    .empty-state { text-align:center; padding:3.2rem 1rem; background:var(--surface); border:1px dashed #cdd5e4; border-radius:18px; }
    .empty-icon { font-size:2.2rem; margin-bottom:.35rem; }
    .empty-title { color:var(--ink); font-weight:750; font-size:1.05rem; }
    .empty-copy { color:var(--muted); font-size:.86rem; margin-top:.35rem; }
    .source-card { border:1px solid #dbe3f2; border-left:4px solid var(--brand); background:#f8faff; padding:.8rem .95rem; border-radius:10px; margin:.55rem 0; }
    .source-title { color:#243b85; font-weight:720; font-size:.84rem; }
    .source-copy { color:#5f6f87; font-size:.8rem; line-height:1.55; margin-top:.35rem; }
    .status-pill { display:inline-block; padding:.25rem .55rem; border-radius:999px; font-size:.74rem; font-weight:700; }
    .status-success { background:#e7f7ef; color:var(--success); }
    .status-processing { background:#fff5df; color:var(--warning); }
    .status-failed { background:#ffebeb; color:#b42318; }
    .status-neutral { background:#eef1f6; color:#667085; }
    div[data-testid="stMetric"] { background:var(--surface); border:1px solid var(--line); border-radius:16px; padding:.75rem .9rem; box-shadow:0 5px 15px rgba(16,24,40,.035); }
    div[data-testid="stMetricLabel"] { color:var(--muted); }
    div[data-testid="stMetricValue"] { color:var(--ink); }
    button[kind="primary"] { border-radius:10px; }
    .stTabs [data-baseweb="tab-list"] { gap:.35rem; border-bottom:1px solid var(--line); }
    .stTabs [data-baseweb="tab"] { height:2.7rem; padding:0 1rem; color:var(--muted); }
    .stTabs [aria-selected="true"] { color:var(--brand); font-weight:700; }
    [data-testid="stChatMessage"] { border:1px solid var(--line); border-radius:16px; margin:.65rem 0; padding:.85rem 1rem; background:var(--surface); }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] { line-height:1.7; }
    .quick-prompt { background:#f4f6ff; border:1px solid #dce3ff; border-radius:12px; padding:.75rem .9rem; color:#3b4d84; font-size:.82rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


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


def status_badge(status: str) -> str:
    mapping = {
        "queued": ("排队中", "status-processing"),
        "processing": ("处理中", "status-processing"),
        "completed": ("已完成", "status-success"),
        "failed": ("失败", "status-failed"),
    }
    label, class_name = mapping.get(status, (status, "status-neutral"))
    return f'<span class="status-pill {class_name}">{label}</span>'


def auth_panel() -> None:
    left, center, right = st.columns([1.15, 1.35, 1.15], gap="large")
    with left:
        st.markdown("### 更快找到答案")
        st.caption("把企业资料变成可搜索、可追溯的知识资产。")
        for icon, title, copy in [
            ("⚡", "异步入库", "上传文档后自动解析、切分和向量化。"),
            ("🔎", "混合检索", "语义检索与关键词检索协同工作。"),
            ("🛡️", "证据优先", "回答附带来源，没有依据时明确拒答。"),
        ]:
            st.markdown(f'<div class="surface"><b>{icon} {title}</b><div class="muted">{copy}</div></div>', unsafe_allow_html=True)
    with center:
        st.markdown('<div class="brand-mark"><div class="brand-icon">📚</div><div class="brand-name">企业智能知识库</div></div>', unsafe_allow_html=True)
        st.markdown("## 欢迎回来")
        st.caption("登录后管理你的知识库，并开始一场有来源的问答。")
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
    with right:
        st.markdown("### 项目能力")
        st.markdown('<div class="surface"><div class="metric-label">支持格式</div><div class="metric-value">4 种</div><div class="metric-hint">PDF · DOCX · MD · TXT</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="surface"><div class="metric-label">检索链路</div><div class="metric-value">RRF</div><div class="metric-hint">向量 + 全文 + 重排序</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="surface"><div class="metric-label">安全策略</div><div class="metric-value">证据门控</div><div class="metric-hint">无依据自动拒答</div></div>', unsafe_allow_html=True)


def fetch_knowledge_bases() -> list[dict]:
    response = api_request("GET", "/api/v1/knowledge-bases")
    return response.json() if response is not None and response.ok else []


def fetch_documents(knowledge_base_id: str) -> list[dict]:
    response = api_request("GET", f"/api/v1/knowledge-bases/{knowledge_base_id}/documents")
    return response.json() if response is not None and response.ok else []


def sidebar_panel(knowledge_bases: list[dict]) -> tuple[dict | None, str]:
    st.markdown('<div class="brand-mark"><div class="brand-icon">📚</div><div class="brand-name">企业知识库</div></div>', unsafe_allow_html=True)
    user = st.session_state.get("current_user", {})
    st.caption(user.get("email", ""))
    st.markdown('<div class="sidebar-label">当前知识库</div>', unsafe_allow_html=True)
    if not knowledge_bases:
        selected = None
    else:
        names = [item["name"] for item in knowledge_bases]
        selected_name = st.selectbox("选择知识库", names, label_visibility="collapsed")
        selected = next(item for item in knowledge_bases if item["name"] == selected_name)
    st.markdown('<div class="sidebar-label">工作区</div>', unsafe_allow_html=True)
    section = st.radio("工作区", ["智能问答", "文档管理", "知识库设置", "评测报告"], label_visibility="collapsed")
    st.divider()
    with st.expander("＋ 新建知识库"):
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
    if st.button("退出登录", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    return selected, section


def render_chat(knowledge_base: dict) -> None:
    knowledge_base_id = knowledge_base["id"]
    state_key = f"chat_history_{knowledge_base_id}"
    conversation_key = f"conversation_{knowledge_base_id}"
    history = st.session_state.setdefault(state_key, [])
    st.markdown('<div class="section-title">智能问答</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">回答严格基于当前知识库，并为关键结论提供来源。</div>', unsafe_allow_html=True)
    if not history:
        st.markdown('<div class="empty-state"><div class="empty-icon">✦</div><div class="empty-title">从一个问题开始</div><div class="empty-copy">试试下面的问题，或直接在底部输入你的问题。</div></div>', unsafe_allow_html=True)
        st.write("")
        prompt_cols = st.columns(3)
        prompts = ["上海出差住宿标准是多少？", "报销需要提交哪些材料？", "漏打卡应该如何处理？"]
        for col, prompt in zip(prompt_cols, prompts):
            if col.button(prompt, key=f"quick-{knowledge_base_id}-{prompt}", use_container_width=True):
                st.session_state[f"pending_question_{knowledge_base_id}"] = prompt
                st.rerun()
    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("citations"):
                with st.expander(f"引用来源（{len(message['citations'])}）"):
                    for citation in message["citations"]:
                        location = f" · 第 {citation['page_number']} 页" if citation.get("page_number") else ""
                        st.markdown(
                            f'<div class="source-card"><div class="source-title">[S{citation["citation_index"]}] {citation["document_name"]}{location}</div><div class="source-copy">{citation["content"]}</div></div>',
                            unsafe_allow_html=True,
                        )
            if message.get("meta"):
                st.caption(message["meta"])
    pending_key = f"pending_question_{knowledge_base_id}"
    question = st.session_state.pop(pending_key, None) or st.chat_input("向当前知识库提问……", key=f"chat-input-{knowledge_base_id}")
    if not question:
        return
    history.append({"role": "user", "content": question})
    with st.spinner("正在检索资料并生成回答……"):
        response = api_request("POST", "/api/v1/chat/query", json={"knowledge_base_id": knowledge_base_id, "question": question, "conversation_id": st.session_state.get(conversation_key), "top_k": 3})
    if response is None or not response.ok:
        history.append({"role": "assistant", "content": "问答请求失败，请检查服务状态。"})
        show_error(response, "问答失败")
        st.rerun()
    result = response.json()
    st.session_state[conversation_key] = result["conversation_id"]
    status = "已基于证据" if result["grounded"] else "证据不足，已拒答"
    history.append({
        "role": "assistant",
        "content": result["answer"],
        "citations": result["citations"],
        "meta": f"{status} · {result['llm_provider']} · 检索 {result['retrieval_latency_ms']} ms · 生成 {result['generation_latency_ms']} ms · Trace {result['trace_id'][:10]}",
    })
    st.rerun()


def render_documents(knowledge_base: dict, documents: list[dict]) -> None:
    knowledge_base_id = knowledge_base["id"]
    st.markdown('<div class="section-title">文档管理</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">上传资料后，系统会在后台自动解析、分块并生成向量索引。</div>', unsafe_allow_html=True)
    with st.container(border=True):
        uploaded_file = st.file_uploader("拖拽或选择文档", type=["pdf", "docx", "md", "markdown", "txt"], help="支持 PDF、DOCX、Markdown、TXT，单文件最大 20 MB。", key=f"upload-{knowledge_base_id}")
        col1, col2 = st.columns([1, 1])
        if col1.button("开始处理", type="primary", key=f"submit-{knowledge_base_id}", disabled=uploaded_file is None, use_container_width=True):
            response = api_request("POST", f"/api/v1/knowledge-bases/{knowledge_base_id}/documents", files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)})
            if response is not None and response.status_code == 202:
                st.success("文档已进入异步处理队列。")
                st.rerun()
            else:
                show_error(response, "文档上传失败")
        if col2.button("刷新状态", key=f"refresh-{knowledge_base_id}", use_container_width=True):
            st.rerun()
    if not documents:
        st.markdown('<div class="empty-state"><div class="empty-icon">📄</div><div class="empty-title">还没有文档</div><div class="empty-copy">上传第一份企业资料，开始构建你的知识库。</div></div>', unsafe_allow_html=True)
        return
    for document in documents:
        with st.container(border=True):
            cols = st.columns([4.5, 1.2, 1.2, .9])
            cols[0].markdown(f"**{document['original_filename']}**")
            cols[0].caption(f"{document['file_type'].upper()} · {document['file_size'] / 1024:.1f} KB")
            cols[1].markdown(status_badge(document["status"]), unsafe_allow_html=True)
            cols[2].write(f"{document['chunk_count']} 个分块")
            if cols[3].button("删除", key=f"delete-doc-{document['id']}", use_container_width=True):
                response = api_request("DELETE", f"/api/v1/documents/{document['id']}")
                if response is not None and response.status_code == 204:
                    st.rerun()
                show_error(response, "删除失败")
            if document.get("error_message"):
                st.error(document["error_message"])


def render_settings(knowledge_base: dict) -> None:
    st.markdown('<div class="section-title">知识库设置</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">查看当前知识库信息和危险操作。</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="surface"><div class="metric-label">名称</div><div class="metric-value">{knowledge_base["name"]}</div><div class="metric-hint">{knowledge_base.get("description") or "暂无描述"}</div></div>', unsafe_allow_html=True)
    st.code(knowledge_base["id"], language="text")
    st.warning("删除知识库会同时删除其中的文档、向量、会话和引用记录。")
    if st.button("删除当前知识库", type="secondary"):
        response = api_request("DELETE", f"/api/v1/knowledge-bases/{knowledge_base['id']}")
        if response is not None and response.status_code == 204:
            st.rerun()
        show_error(response, "删除失败")


def render_evaluation() -> None:
    st.markdown('<div class="section-title">评测报告</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">用可重复的指标观察检索、引用与拒答能力。</div>', unsafe_allow_html=True)
    if LOCAL_REPORT_PATH.exists():
        report = json.loads(LOCAL_REPORT_PATH.read_text(encoding="utf-8"))
        metrics = report["metrics"]
        st.caption(f"自建企业制度集 · {metrics['question_count']} 条问题 · 生成于 {report['generated_at']}")
        row = st.columns(4)
        row[0].metric("Hit@5", f"{metrics['retrieval_hit_at_5'] * 100:.1f}%")
        row[1].metric("Recall@5", f"{metrics['retrieval_recall_at_5'] * 100:.1f}%")
        row[2].metric("引用准确率", f"{metrics['citation_precision'] * 100:.1f}%")
        row[3].metric("拒答通过率", f"{metrics['refusal_accuracy'] * 100:.1f}%")
    else:
        st.info("尚未生成自建评测报告。")
    if PUBLIC_REPORT_PATH.exists():
        report = json.loads(PUBLIC_REPORT_PATH.read_text(encoding="utf-8"))
        metrics = report["metrics"]
        st.divider()
        st.markdown("#### 公开 RetrievalQA 基准")
        st.caption(f"公开检索基准 · {metrics['question_count']} 条问题 · 来源仓库：{report['dataset']['repository']}")
        row = st.columns(5)
        row[0].metric("Hit@5", f"{metrics['retrieval_hit_at_5'] * 100:.1f}%")
        row[1].metric("Recall@5", f"{metrics['retrieval_recall_at_5'] * 100:.1f}%")
        row[2].metric("Precision@5", f"{metrics['retrieval_precision_at_5'] * 100:.1f}%")
        row[3].metric("MRR@5", f"{metrics['retrieval_mrr_at_5']:.3f}")
        row[4].metric("平均耗时", f"{metrics['average_latency_ms']:.0f} ms")
        st.caption("公开基准用于检索管线对比，不等价于真实企业业务准确率。")


if st.session_state.get("access_token"):
    knowledge_bases = fetch_knowledge_bases()
    selected_kb, section = sidebar_panel(knowledge_bases)
    if selected_kb is None:
        st.markdown('<div class="hero"><h1>企业知识中心</h1><p>创建一个知识库，开始管理资料并进行有来源的问答。</p><div class="hero-meta"><span class="hero-chip">多格式文档</span><span class="hero-chip">混合检索</span><span class="hero-chip">证据门控</span></div></div>', unsafe_allow_html=True)
        st.info("请从左侧创建第一个知识库。")
    else:
        documents = fetch_documents(selected_kb["id"])
        completed = sum(document["status"] == "completed" for document in documents)
        chunks = sum(document["chunk_count"] for document in documents)
        st.markdown(f'<div class="hero"><h1>{selected_kb["name"]}</h1><p>{selected_kb.get("description") or "集中管理企业资料，并通过可追溯的 RAG 问答快速获得答案。"}</p><div class="hero-meta"><span class="hero-chip">🔐 私有知识库</span><span class="hero-chip">⚡ 异步处理</span><span class="hero-chip">🧭 来源可追溯</span></div></div>', unsafe_allow_html=True)
        stats = st.columns(4)
        stats[0].metric("知识库", len(knowledge_bases))
        stats[1].metric("当前文档", len(documents))
        stats[2].metric("已完成", completed)
        stats[3].metric("可检索分块", chunks)
        if section == "智能问答":
            render_chat(selected_kb)
        elif section == "文档管理":
            render_documents(selected_kb, documents)
        elif section == "知识库设置":
            render_settings(selected_kb)
        else:
            render_evaluation()
else:
    st.markdown('<div class="hero"><h1>企业级智能知识库问答系统</h1><p>让企业资料可搜索、可引用、可验证。</p><div class="hero-meta"><span class="hero-chip">Python 后端</span><span class="hero-chip">RAG 应用</span><span class="hero-chip">企业知识管理</span></div></div>', unsafe_allow_html=True)
    auth_panel()
