"""
Case Study Tutor — Alpes Bank GenAI
=====================================
A group-based AI-scaffolded business case study platform.

Run with:
    streamlit run app.py

Thin router: page config + global CSS + page dispatch.
All business logic lives in workflow.py / storage.py.
All UI components live in ui/sidebar.py.
Page views live in pages/*.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# ── Path setup (must be before local imports) ─────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── Streamlit page config (must be the first st call) ────────────────────────
st.set_page_config(
    page_title="Case Study Tutor | HSG",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
.stApp { background: #F4F6F9; color: #2C3E50; }

/* ── Force dark text on all Streamlit native elements ── */
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label,
.stTextInput label, .stSlider label,
.stSelectbox label, .stTextArea label,
.stNumberInput label, .stRadio label,
div[data-baseweb="form-control-label"] {
    color: #2C3E50 !important;
}
[data-testid="stMarkdownContainer"] > div > p,
[data-testid="stMarkdownContainer"] > div > ul > li,
.stMarkdown > div > p,
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] p,
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] div {
    color: #000000 !important;
}
[data-testid="stCaptionContainer"] p { color: #6C757D !important; }
[data-testid="stTabs"] button[role="tab"] { color: #2C3E50 !important; }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] { color: #003C87 !important; }

/* ── White text on ALL dark/blue backgrounds ── */
.card-blue * { color: white !important; }
.card-blue .section-pill {
    background: rgba(255,255,255,0.2) !important;
    color: white !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong {
    color: #2C3E50 !important;
}
[data-testid="stSidebar"] .stButton > button {
    color: #2C3E50 !important;
    background: #F0F2F6 !important;
    border: 1px solid #DDE3EC !important;
}

/* ── Top progress bar ── */
.progress-bar-wrap {
    background: #E0E7FF;
    border-radius: 99px;
    height: 8px;
    width: 100%;
    margin: 4px 0 20px;
}
.progress-bar-fill {
    background: linear-gradient(90deg, #003C87, #4F8EF7);
    border-radius: 99px;
    height: 8px;
    transition: width 0.5s ease;
}

/* ── Cards ── */
.card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 28px 32px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    margin-bottom: 20px;
    color: #2C3E50;
}
.card-blue {
    background: linear-gradient(135deg, #003C87 0%, #1A5CC8 100%);
    color: white;
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 20px;
}
.card-blue h1, .card-blue h2, .card-blue p { color: white !important; }

/* ── Section pill badge ── */
.section-pill {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 99px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    background: #E8F0FE;
    color: #003C87;
    margin-bottom: 10px;
}

/* ── Member status dots ── */
.member-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 0;
    border-bottom: 1px solid #F0F0F0;
}
.member-row:last-child { border-bottom: none; }
.dot {
    width: 11px; height: 11px;
    border-radius: 50%;
    flex-shrink: 0;
}
.dot-green  { background: #27AE60; }
.dot-orange { background: #F39C12; }
.dot-red    { background: #E74C3C; }
.dot-grey   { background: #BDC3C7; }
.member-name { font-weight: 500; font-size: 0.9rem; flex: 1; }
.word-count  { font-size: 0.78rem; color: #6C757D; }

/* ── Integration score bar ── */
.score-track {
    background: #E9ECEF;
    border-radius: 99px;
    height: 10px;
    margin: 10px 0;
    overflow: hidden;
}
.score-fill-green  { background: #27AE60; height: 10px; border-radius: 99px; }
.score-fill-orange { background: #F39C12; height: 10px; border-radius: 99px; }
.score-fill-red    { background: #E74C3C; height: 10px; border-radius: 99px; }

/* ── Feedback box ── */
.feedback-box {
    background: #F0F7FF;
    border-left: 4px solid #003C87;
    border-radius: 0 12px 12px 0;
    padding: 16px 20px;
    margin: 16px 0;
    font-size: 0.93rem;
    line-height: 1.65;
}
.feedback-box-warn {
    background: #FFF8E7;
    border-left: 4px solid #F39C12;
    border-radius: 0 12px 12px 0;
    padding: 16px 20px;
    margin: 16px 0;
}
.feedback-box-success {
    background: #EAFAF1;
    border-left: 4px solid #27AE60;
    border-radius: 0 12px 12px 0;
    padding: 16px 20px;
    margin: 16px 0;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
div[data-testid="stForm"] .stButton > button[kind="primaryFormSubmit"] {
    background: #003C87 !important;
    color: white !important;
    border: none !important;
    padding: 12px 28px !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #E9ECEF;
}
[data-testid="stSidebar"] h3 { color: #003C87; font-size: 1rem; }

/* ── Case text ── */
.case-text {
    font-size: 0.96rem;
    line-height: 1.75;
    color: #2C3E50;
}
.case-text table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
}
.case-text th {
    background: #003C87;
    color: white;
    padding: 8px 12px;
    text-align: left;
}
.case-text td {
    padding: 8px 12px;
    border-bottom: 1px solid #E9ECEF;
}

/* ── Welcome hero ── */
.hero-title {
    font-size: 2.2rem;
    font-weight: 700;
    color: #003C87;
    line-height: 1.2;
    margin-bottom: 8px;
}
.hero-sub {
    font-size: 1.05rem;
    color: #444;
    margin-bottom: 28px;
    font-weight: 400;
}

/* ── Group code display ── */
.group-code {
    font-size: 2.4rem;
    font-weight: 700;
    letter-spacing: 0.2em;
    color: #003C87;
    font-family: 'Courier New', monospace;
    background: #E8F0FE;
    border-radius: 12px;
    padding: 14px 24px;
    display: inline-block;
    margin: 12px 0;
}

/* ── Step indicator ── */
.step-wrap { display: flex; gap: 6px; align-items: center; margin-bottom: 24px; }
.step-dot {
    width: 28px; height: 28px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.8rem; font-weight: 700;
}
.step-active { background: #003C87; color: white; }
.step-done   { background: #27AE60; color: white; }
.step-todo   { background: #E9ECEF; color: #999; }
.step-line   { flex: 1; height: 2px; background: #E9ECEF; }
.step-line-done { flex: 1; height: 2px; background: #27AE60; }

/* ── Group chat ── */
.chat-feed {
    max-height: 260px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 4px 0 8px;
}
.chat-bubble-wrap-me    { display:flex; justify-content:flex-end; }
.chat-bubble-wrap-other { display:flex; justify-content:flex-start; }
.chat-bubble {
    max-width: 82%;
    padding: 7px 11px;
    border-radius: 14px;
    font-size: 0.83rem;
    line-height: 1.45;
    word-break: break-word;
}
.chat-bubble-me {
    background: #003C87;
    color: white !important;
    border-bottom-right-radius: 4px;
}
.chat-bubble-other {
    background: #F0F2F6;
    color: #2C3E50 !important;
    border-bottom-left-radius: 4px;
}
.chat-meta-me    { font-size:0.7rem; color:#999; text-align:right;  margin-top:2px; }
.chat-meta-other { font-size:0.7rem; color:#999; text-align:left;   margin-top:2px; }
.chat-empty {
    text-align:center; color:#BBB; font-size:0.82rem; padding:20px 0;
}
</style>
""", unsafe_allow_html=True)

# ── Page imports (after sys.path is set) ─────────────────────────────────────
from views.welcome   import page_welcome    # noqa: E402
from views.lobby     import page_lobby      # noqa: E402
from views.reading   import page_reading    # noqa: E402
from views.working   import page_working    # noqa: E402
from views.alignment import page_alignment  # noqa: E402
from views.synthesis import page_synthesis  # noqa: E402
from views.summary   import page_summary    # noqa: E402
from database.storage import _load_session   # noqa: E402
from core.workflow    import _all_submitted  # noqa: E402


# ══════════════════════════════════════════════════════════════════════════════
# Router
# ══════════════════════════════════════════════════════════════════════════════

def main():
    if "page" not in st.session_state:
        st.session_state["page"] = "welcome"

    page = st.session_state["page"]

    if page != "welcome" and "group_code" in st.session_state:
        gd = _load_session(st.session_state["group_code"])
        if gd is None:
            st.session_state["page"] = "welcome"
            page = "welcome"
        else:
            server_phase = gd.get("phase", "lobby")
            if server_phase == "reading_ready" and page == "lobby":
                st.session_state["page"] = "reading"
                page = "reading"
            elif server_phase == "aligning" and page == "working" and _all_submitted(gd):
                st.session_state["page"] = "alignment"
                page = "alignment"

    routes = {
        "welcome":   page_welcome,
        "lobby":     page_lobby,
        "reading":   page_reading,
        "working":   page_working,
        "alignment": page_alignment,
        "synthesis": page_synthesis,
        "done":      page_summary,
    }

    routes.get(page, page_welcome)()


if __name__ == "__main__":
    main()
