from __future__ import annotations

from html import escape

import streamlit as st


def render_citations(citations: list[dict]) -> None:
    """Render grounded sources without allowing document text to inject HTML."""

    if not citations:
        return

    with st.expander(f"引用来源（{len(citations)}）"):
        for citation in citations:
            index = escape(str(citation.get("citation_index", "?")))
            document_name = escape(str(citation.get("document_name", "未命名文档")))
            content = escape(str(citation.get("content", ""))).replace("\n", "<br>")
            page_number = citation.get("page_number")
            location = f" · 第 {escape(str(page_number))} 页" if page_number else ""
            section = citation.get("section")
            section_text = f" · {escape(str(section))}" if section else ""

            st.markdown(
                f"""
                <div class="source-card">
                    <strong>[S{index}] {document_name}</strong>
                    <span class="muted">{location}{section_text}</span><br>
                    <span>{content}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )