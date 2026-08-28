import os

import streamlit as st

st.set_page_config(page_title="企业智能知识库", page_icon="📚", layout="wide")

st.title("📚 企业级智能知识库问答系统")
st.caption("第一天骨架页面 · 后续将接入登录、文档上传和 RAG 问答")

with st.sidebar:
    st.header("系统导航")
    st.info("当前版本：0.1.0")
    st.write("API 地址：", os.getenv("API_BASE_URL", "http://localhost:8000"))

st.subheader("欢迎")
st.write("项目基础服务已经准备就绪。第二天将开始实现用户认证和知识库管理。")

col1, col2, col3 = st.columns(3)
col1.metric("知识库", "0")
col2.metric("文档", "0")
col3.metric("问答次数", "0")
