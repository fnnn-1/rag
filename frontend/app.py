import os

import requests
import streamlit as st

st.set_page_config(page_title="企业智能知识库", page_icon="📚", layout="wide")
default_api_url = os.getenv("API_BASE_URL", "http://localhost:8000")
current_api_url = st.session_state.get("api_base_url", default_api_url)
if current_api_url in {"http://localhost:8000", "http://127.0.0.1:8000"} and default_api_url != "http://localhost:8000":
    current_api_url = default_api_url
API_BASE_URL = st.sidebar.text_input("API 地址", current_api_url)
st.session_state["api_base_url"] = API_BASE_URL.rstrip("/")


def api_request(method: str, path: str, **kwargs):
    headers = kwargs.pop("headers", {})
    token = st.session_state.get("access_token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        return requests.request(method, f"{API_BASE_URL.rstrip('/')}{path}", headers=headers, timeout=60, **kwargs)
    except requests.RequestException as exc:
        st.error(f"无法连接 API：{exc}")
        return None


def auth_panel() -> None:
    st.title("📚 企业级智能知识库问答系统")
    st.caption("第五天版本：RAG 问答、引用和无依据拒答")
    mode = st.radio("操作", ["登录", "注册"], horizontal=True)
    with st.form("auth_form"):
        email = st.text_input("邮箱")
        password = st.text_input("密码", type="password")
        display_name = st.text_input("显示名称") if mode == "注册" else None
        submitted = st.form_submit_button(mode, type="primary")

    if not submitted:
        return
    if mode == "注册":
        response = api_request("POST", "/api/v1/auth/register", json={"email": email, "password": password, "display_name": display_name})
        if response is not None and response.ok:
            st.success("注册成功，请登录")
        elif response is not None:
            st.error(response.json().get("detail", "注册失败"))
    else:
        response = api_request("POST", "/api/v1/auth/login", data={"username": email, "password": password})
        if response is not None and response.ok:
            body = response.json()
            st.session_state["access_token"] = body["access_token"]
            st.session_state["current_user"] = body["user"]
            st.rerun()
        elif response is not None:
            st.error(response.json().get("detail", "登录失败"))


def render_documents(knowledge_base_id: str) -> None:
    st.markdown("#### 文档管理")
    uploaded_file = st.file_uploader("上传 PDF、Word、Markdown 或 TXT 文件", type=["pdf", "docx", "md", "markdown", "txt"], key=f"upload-{knowledge_base_id}")
    if uploaded_file is not None and st.button("提交文档处理", key=f"submit-{knowledge_base_id}"):
        response = api_request("POST", f"/api/v1/knowledge-bases/{knowledge_base_id}/documents", files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)})
        if response is not None and response.status_code == 202:
            st.success("文档已提交，后台正在处理")
            st.rerun()
        elif response is not None:
            st.error(response.json().get("detail", "文档上传失败"))

    response = api_request("GET", f"/api/v1/knowledge-bases/{knowledge_base_id}/documents")
    if response is None or not response.ok:
        return
    documents = response.json()
    if not documents:
        st.info("该知识库还没有文档")
        return
    for document in documents:
        status_map = {"queued": "排队中", "processing": "处理中", "completed": "已完成", "failed": "失败"}
        cols = st.columns([4, 2, 2, 1])
        cols[0].write(f"**{document['original_filename']}**")
        cols[1].write(f"状态：{status_map.get(document['status'], document['status'])}")
        cols[2].write(f"分块：{document['chunk_count']}")
        if cols[3].button("删除", key=f"delete-doc-{document['id']}"):
            delete_response = api_request("DELETE", f"/api/v1/documents/{document['id']}")
            if delete_response is not None and delete_response.status_code == 204:
                st.rerun()
            elif delete_response is not None:
                st.error(delete_response.json().get("detail", "删除失败"))
        if document.get("error_message"):
            st.caption(f"错误：{document['error_message']}")


def render_chat(knowledge_base_id: str) -> None:
    st.markdown("#### 知识库问答")
    with st.form(f"chat-{knowledge_base_id}"):
        question = st.text_area("请输入问题", placeholder="例如：员工报销交通费需要什么材料？", height=90)
        top_k = st.slider("引用片段数量", min_value=1, max_value=5, value=3, key=f"topk-{knowledge_base_id}")
        submitted = st.form_submit_button("开始问答", type="primary")
    if not submitted:
        return
    response = api_request("POST", "/api/v1/chat/query", json={"knowledge_base_id": knowledge_base_id, "question": question, "top_k": top_k})
    if response is None:
        return
    if not response.ok:
        st.error(response.json().get("detail", "问答失败"))
        return
    result = response.json()
    st.markdown("**回答**")
    st.write(result["answer"])
    if result["grounded"]:
        st.success(f"回答已基于知识库证据生成 · {result['llm_provider']}")
        with st.expander(f"查看引用（{len(result['citations'])}）"):
            for citation in result["citations"]:
                st.markdown(f"**[S{citation['citation_index']}] {citation['document_name']}**")
                st.caption(citation["content"])
    else:
        st.warning("证据不足，系统已拒绝生成无依据回答。")
    st.caption(f"Trace ID：{result['trace_id']} · 检索 {result['retrieval_latency_ms']} ms · 生成 {result['generation_latency_ms']} ms")


def knowledge_base_panel() -> None:
    user = st.session_state.get("current_user", {})
    st.title("知识库管理")
    st.caption(f"当前用户：{user.get('email', '')}")
    if st.sidebar.button("退出登录"):
        st.session_state.clear()
        st.rerun()

    with st.expander("创建知识库", expanded=True):
        with st.form("create_kb"):
            name = st.text_input("名称", placeholder="例如：员工制度知识库")
            description = st.text_area("描述", placeholder="知识库用途说明")
            submitted = st.form_submit_button("创建知识库", type="primary")
        if submitted:
            response = api_request("POST", "/api/v1/knowledge-bases", json={"name": name, "description": description or None})
            if response is not None and response.ok:
                st.success("知识库创建成功")
                st.rerun()
            elif response is not None:
                st.error(response.json().get("detail", "创建失败"))

    response = api_request("GET", "/api/v1/knowledge-bases")
    if response is None or not response.ok:
        return
    knowledge_bases = response.json()
    st.subheader(f"我的知识库（{len(knowledge_bases)}）")
    if not knowledge_bases:
        st.info("还没有知识库，请先创建一个。")
        return
    for item in knowledge_bases:
        with st.container(border=True):
            left, right = st.columns([5, 1])
            left.markdown(f"### {item['name']}")
            left.write(item.get("description") or "暂无描述")
            left.caption(f"ID：{item['id']}")
            if right.button("删除", key=f"delete-{item['id']}"):
                delete_response = api_request("DELETE", f"/api/v1/knowledge-bases/{item['id']}")
                if delete_response is not None and delete_response.status_code == 204:
                    st.rerun()
                elif delete_response is not None:
                    st.error(delete_response.json().get("detail", "删除失败"))
            render_documents(item["id"])
            render_chat(item["id"])


if st.session_state.get("access_token"):
    knowledge_base_panel()
else:
    auth_panel()
