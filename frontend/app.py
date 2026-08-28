import uuid

import requests
import streamlit as st

st.set_page_config(page_title="企业智能知识库", page_icon="📚", layout="wide")
API_BASE_URL = st.sidebar.text_input("API 地址", st.session_state.get("api_base_url", "http://localhost:8000"))
st.session_state["api_base_url"] = API_BASE_URL.rstrip("/")


def api_request(method: str, path: str, **kwargs):
    headers = kwargs.pop("headers", {})
    token = st.session_state.get("access_token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        return requests.request(method, f"{API_BASE_URL.rstrip('/')}{path}", headers=headers, timeout=15, **kwargs)
    except requests.RequestException as exc:
        st.error(f"无法连接 API：{exc}")
        return None


def auth_panel() -> None:
    st.title("📚 企业级智能知识库问答系统")
    st.caption("第二天版本：用户认证与知识库管理")
    mode = st.radio("操作", ["登录", "注册"], horizontal=True)
    with st.form("auth_form"):
        email = st.text_input("邮箱")
        password = st.text_input("密码", type="password")
        display_name = st.text_input("显示名称") if mode == "注册" else None
        submitted = st.form_submit_button(mode, type="primary")

    if not submitted:
        return
    if mode == "注册":
        response = api_request(
            "POST",
            "/api/v1/auth/register",
            json={"email": email, "password": password, "display_name": display_name},
        )
        if response is not None and response.ok:
            st.success("注册成功，请登录")
        elif response is not None:
            st.error(response.json().get("detail", "注册失败"))
    else:
        response = api_request(
            "POST",
            "/api/v1/auth/login",
            data={"username": email, "password": password},
        )
        if response is not None and response.ok:
            body = response.json()
            st.session_state["access_token"] = body["access_token"]
            st.session_state["current_user"] = body["user"]
            st.rerun()
        elif response is not None:
            st.error(response.json().get("detail", "登录失败"))


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
            response = api_request(
                "POST",
                "/api/v1/knowledge-bases",
                json={"name": name, "description": description or None},
            )
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
                    st.success("已删除")
                    st.rerun()
                elif delete_response is not None:
                    st.error(delete_response.json().get("detail", "删除失败"))


if st.session_state.get("access_token"):
    knowledge_base_panel()
else:
    auth_panel()
