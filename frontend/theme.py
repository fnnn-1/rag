import streamlit as st


def apply_theme() -> None:
    """Apply the reusable Streamlit theme used by the RAG UI."""

    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1380px;
            padding-top: 1.35rem;
            padding-bottom: 2rem;
        }

        /* Sidebar uses several nested containers in recent Streamlit versions.
           Style the section and its inner surface so the foreground/background
           colors remain readable across both light and dark app themes. */
        [data-testid="stSidebar"],
        [data-testid="stSidebar"] > div:first-child,
        [data-testid="stSidebarContent"] {
            background: #172033 !important;
            color: #f8fafc !important;
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] small {
            color: #f8fafc !important;
        }

        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
        [data-testid="stSidebar"] .stCaption {
            color: #cbd5e1 !important;
        }

        [data-testid="stSidebar"] a {
            color: #93c5fd !important;
        }

        [data-testid="stSidebar"] hr {
            border-color: #334155 !important;
        }

        [data-testid="stSidebar"] button {
            color: #f8fafc !important;
            background: #2b3448 !important;
            border-color: #475569 !important;
        }

        [data-testid="stSidebar"] button:hover {
            background: #364158 !important;
            border-color: #64748b !important;
        }

        [data-testid="stSidebar"] [data-baseweb="select"] > div {
            background: #2b3448 !important;
            color: #f8fafc !important;
            border-color: #475569 !important;
        }

        .hero {
            padding: 1.35rem 1.55rem;
            border-radius: 18px;
            color: white;
            background: linear-gradient(120deg, #173b72, #315fa8 58%, #4d7bc3);
            margin-bottom: 1rem;
            box-shadow: 0 8px 24px rgba(49, 95, 168, .14);
        }

        .hero h1 {
            margin: 0;
            font-size: 2rem;
        }

        .hero p {
            margin: .45rem 0 0;
            opacity: .9;
        }

        .source-card {
            border-left: 4px solid #315fa8;
            background: #f5f8fd;
            padding: .85rem 1rem;
            border-radius: 9px;
            margin: .55rem 0;
            line-height: 1.6;
        }

        .source-card strong {
            color: #173b72;
        }

        .muted {
            color: #667085;
            font-size: .88rem;
        }

        .status-card {
            border: 1px solid #e4e7ec;
            background: #ffffff;
            border-radius: 12px;
            padding: .8rem 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
