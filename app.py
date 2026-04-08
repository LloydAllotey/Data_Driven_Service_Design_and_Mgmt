"""
Case Study Tutor — Alpes Bank GenAI
=====================================
A group-based AI-scaffolded business case study platform.

Run with:
    streamlit run app.py

Each student opens this URL in their own browser tab, enters their name
and the group code, and works through their assigned case section.
The Group Alignment Agent (group_alignment_agent.py) provides real-time
feedback on contribution balance (free-rider detection) and argument
coherence (fragmentation detection).

Session data is stored as JSON files in the sessions/ subfolder so that
all group members share the same state.
"""

from __future__ import annotations

import json
import os
import random
import string
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import streamlit as st
try:
    from streamlit_autorefresh import st_autorefresh   # pip install streamlit-autorefresh
    _AUTOREFRESH_AVAILABLE = True
except ImportError:
    _AUTOREFRESH_AVAILABLE = False

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
SESSIONS_DIR = ROOT / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

# ── Local imports ─────────────────────────────────────────────────────────────
import sys
sys.path.insert(0, str(ROOT))

from case_content import (
    SECTIONS,
    BUZZ_WORDS,
    SECTION_CONNECTIONS,
    EXPERT_ANSWERS,
    GROUP_SYNTHESIS_QUESTIONS,
    assign_sections_by_preferences,
    assign_sections_to_members,
    get_section_by_id,
)

# Agent is imported lazily so the app still renders if the API key is missing
_agent = None

def _get_agent():
    global _agent
    if _agent is None:
        try:
            from agents.group_alignment_agent import GroupAlignmentAgent
            cfg = _load_config()
            _agent = GroupAlignmentAgent(cfg.get("ai_manager", {}))
        except Exception as e:
            st.warning(f"AI agent unavailable: {e}. Add your API key to .env to enable feedback.")
    return _agent


def _load_config() -> dict:
    cfg_path = ROOT / "config.json"
    if cfg_path.exists():
        with open(cfg_path) as f:
            return json.load(f)
    return {"ai_manager": {"client": "groq", "primary_model": "llama-3.3-70b-versatile"}}


# ── Streamlit page config ─────────────────────────────────────────────────────
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
/* Labels (text inputs, sliders, selectboxes, etc.) */
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label,
.stTextInput label, .stSlider label,
.stSelectbox label, .stTextArea label,
.stNumberInput label, .stRadio label,
div[data-baseweb="form-control-label"] {
    color: #2C3E50 !important;
}
/* Markdown blocks */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] strong,
.stMarkdown p, .stMarkdown li, .stMarkdown span {
    color: #2C3E50 !important;
}
/* Caption / helper text */
[data-testid="stCaptionContainer"] p { color: #6C757D !important; }
/* Tab labels */
[data-testid="stTabs"] button[role="tab"] { color: #2C3E50 !important; }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] { color: #003C87 !important; }

/* ── White text on ALL dark/blue backgrounds — overrides everything above ── */
.card-blue * { color: white !important; }
.card-blue .section-pill {
    background: rgba(255,255,255,0.2) !important;
    color: white !important;
}
/* Sidebar: keep phase label and button legible */
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


# ══════════════════════════════════════════════════════════════════════════════
# Session helpers
# ══════════════════════════════════════════════════════════════════════════════

def _session_path(code: str) -> Path:
    return SESSIONS_DIR / f"{code.upper()}.json"


def _load_session(code: str) -> Optional[dict]:
    p = _session_path(code)
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)


def _save_session(data: dict) -> None:
    code = data["group_code"]
    with open(_session_path(code), "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _new_group_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def _create_group(creator_name: str, group_size: int, preferences: list) -> dict:
    code = _new_group_code()
    # Ensure unique
    while _session_path(code).exists():
        code = _new_group_code()
    data = {
        "group_code": code,
        "created_at": datetime.now().isoformat(),
        "members": [creator_name],
        "expected_size": group_size,
        "preferences": {creator_name: preferences},
        "section_assignments": {},
        "submissions": {},
        "feedback": {},
        "alignment_reports": [],
        "synthesis_submissions": {},
        # lobby: waiting for the group to fill up before sections are revealed
        # reading_ready: everyone joined, sections assigned, ready to start
        "phase": "lobby",
    }
    # If group of 1 (edge case), assign immediately
    if group_size == 1:
        data["section_assignments"] = assign_sections_by_preferences(data["preferences"])
        data["phase"] = "reading_ready"
    _save_session(data)
    return data


def _join_group(code: str, member_name: str, preferences: list) -> tuple[bool, str, Optional[dict]]:
    """Returns (success, error_message, group_data)."""
    data = _load_session(code)
    if data is None:
        return False, f"Group code '{code}' not found. Check the code and try again.", None
    if member_name in data["members"]:
        # Re-joining: update preferences if provided, stay in current phase
        if preferences:
            data.setdefault("preferences", {})[member_name] = preferences
            _save_session(data)
        return True, "", data
    if len(data["members"]) >= data.get("expected_size", 5):
        return False, "This group is already full.", None
    data["members"].append(member_name)
    data.setdefault("preferences", {})[member_name] = preferences
    # Section assignment only fires when the group reaches its expected size
    if len(data["members"]) >= data.get("expected_size", 5):
        data["section_assignments"] = assign_sections_by_preferences(data["preferences"])
        data["phase"] = "reading_ready"
    _save_session(data)
    return True, "", data


def _submit_answer(code: str, member: str, section_id: int, text: str) -> dict:
    data = _load_session(code)
    if data is None:
        return {}
    data["submissions"][member] = {
        "section_id": section_id,
        "text": text,
        "word_count": len(text.split()),
        "submitted_at": datetime.now().isoformat(),
    }
    # Advance phase if all members submitted
    expected = data.get("expected_size", len(data["members"]))
    if len(data["submissions"]) >= expected:
        if data["phase"] in ("waiting", "reading", "working"):
            data["phase"] = "aligning"
    _save_session(data)
    return data


def _submit_synthesis(code: str, member: str, text: str) -> dict:
    data = _load_session(code)
    if data is None:
        return {}
    data["synthesis_submissions"][member] = {
        "text": text,
        "submitted_at": datetime.now().isoformat(),
    }
    if len(data["synthesis_submissions"]) >= len(data["members"]):
        data["phase"] = "done"
    _save_session(data)
    return data


def _all_submitted(group_data: dict) -> bool:
    return len(group_data.get("submissions", {})) >= len(group_data.get("members", []))


def _post_message(code: str, member: str, text: str) -> None:
    """Append a chat message to the group session file."""
    data = _load_session(code)
    if data is None:
        return
    data.setdefault("chat", []).append({
        "member": member,
        "text": text.strip(),
        "ts": datetime.now().strftime("%H:%M"),
    })
    # Keep at most 200 messages to avoid bloating the session file
    data["chat"] = data["chat"][-200:]
    _save_session(data)


def _member_sections(group_data: dict, member: str) -> list[int]:
    """Return list of section IDs assigned to this member."""
    return group_data.get("section_assignments", {}).get(member, [1])


# ══════════════════════════════════════════════════════════════════════════════
# UI Components
# ══════════════════════════════════════════════════════════════════════════════

def _render_step_indicator(current: int):
    steps = ["Setup", "Read", "Analyse", "Group Review", "Synthesis"]
    parts = []
    for i, label in enumerate(steps, 1):
        if i < current:
            cls = "step-done"
            icon = "✓"
        elif i == current:
            cls = "step-active"
            icon = str(i)
        else:
            cls = "step-todo"
            icon = str(i)
        parts.append(f'<div class="step-dot {cls}">{icon}</div>')
        if i < len(steps):
            line_cls = "step-line-done" if i < current else "step-line"
            parts.append(f'<div class="{line_cls}"></div>')
    st.markdown(f'<div class="step-wrap">{"".join(parts)}</div>', unsafe_allow_html=True)


def _render_sidebar(group_data: dict, current_member: str):
    with st.sidebar:
        st.markdown(f"### 📚 Case Study Tutor")
        st.markdown("---")

        code = group_data["group_code"]
        st.markdown(f"**Group Code**")
        st.markdown(f'<div class="group-code">{code}</div>', unsafe_allow_html=True)
        st.caption("Share this code with your group members")
        st.markdown("---")

        members = group_data.get("members", [])
        submissions = group_data.get("submissions", {})
        assignments = group_data.get("section_assignments", {})

        st.markdown("**Group Members**")
        for m in members:
            sub = submissions.get(m)
            if sub:
                wc = sub.get("word_count", 0)
                if wc < 40:
                    dot, status = "dot-orange", f"{wc} words"
                else:
                    dot, status = "dot-green", f"{wc} words ✓"
            else:
                dot, status = "dot-grey", "not submitted"

            you = " (you)" if m == current_member else ""
            sec_ids = assignments.get(m, [])
            sec_labels = ", ".join(
                get_section_by_id(sid)["emoji"] + " §" + str(sid)
                for sid in sec_ids
            )
            st.markdown(
                f'<div class="member-row">'
                f'<div class="dot {dot}"></div>'
                f'<span class="member-name">{m}{you}</span>'
                f'<span class="word-count">{status}</span>'
                f'</div>'
                f'<div style="font-size:0.72rem;color:#999;padding-left:21px;margin-bottom:4px">{sec_labels}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        phase = group_data.get("phase", "waiting")
        phase_labels = {
            "lobby":         "⏳ Waiting for members",
            "reading_ready": "📖 Ready to read",
            "waiting":       "⏳ Waiting for members",
            "reading":       "📖 Reading case",
            "working":       "✍️ Analysing",
            "aligning":      "🤖 Group alignment",
            "synthesis":     "🔗 Synthesis round",
            "done":          "✅ Complete",
        }
        st.markdown(f"**Phase:** {phase_labels.get(phase, phase)}")

        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        # ── Group chat ────────────────────────────────────────────────────────
        st.markdown("---")

        # Auto-refresh every 8 s when the package is available
        if _AUTOREFRESH_AVAILABLE:
            st_autorefresh(interval=8_000, key="chat_refresh")

        messages = group_data.get("chat", [])
        unread_key = f"chat_seen_{code}"
        seen = st.session_state.get(unread_key, 0)
        unread = len(messages) - seen
        badge = f" 🔴 {unread}" if unread > 0 else ""
        st.markdown(f"**💬 Group Chat{badge}**")

        # Message feed — rendered as HTML bubbles for a WhatsApp-style look
        if messages:
            bubbles = []
            for msg in messages[-30:]:         # show last 30
                is_me = msg["member"] == current_member
                wrap  = "chat-bubble-wrap-me"    if is_me else "chat-bubble-wrap-other"
                bub   = "chat-bubble chat-bubble-me" if is_me else "chat-bubble chat-bubble-other"
                meta  = "chat-meta-me"           if is_me else "chat-meta-other"
                name  = "You" if is_me else msg["member"]
                bubbles.append(
                    f'<div class="{wrap}">'
                    f'  <div>'
                    f'    <div class="{bub}">{msg["text"]}</div>'
                    f'    <div class="{meta}">{name} · {msg["ts"]}</div>'
                    f'  </div>'
                    f'</div>'
                )
            st.markdown(
                f'<div class="chat-feed">{"".join(bubbles)}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="chat-empty">No messages yet.<br>Say hi to your group! 👋</div>',
                unsafe_allow_html=True,
            )

        # Mark messages as seen
        st.session_state[unread_key] = len(messages)

        # Message input — use a counter-based key so incrementing it on send
        # creates a brand-new widget instance (naturally empty) on the next run.
        # This avoids the StreamlitAPIException that occurs when you try to write
        # to session_state for an already-instantiated widget key.
        if "chat_input_n" not in st.session_state:
            st.session_state["chat_input_n"] = 0
        msg_key = f"chat_input_{st.session_state['chat_input_n']}"
        new_msg = st.text_input(
            "Message",
            placeholder="Type a message…",
            label_visibility="collapsed",
            key=msg_key,
        )
        if st.button("Send →", use_container_width=True, key="chat_send"):
            if new_msg.strip():
                _post_message(code, current_member, new_msg.strip())
                # Bump counter → next run gets a fresh widget key → input is blank
                st.session_state["chat_input_n"] += 1
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# Pages
# ══════════════════════════════════════════════════════════════════════════════

def page_welcome():
    col_left, col_right = st.columns([1.1, 0.9])

    with col_left:
        st.markdown(
            '<div class="hero-title">Case Study Tutor</div>'
            '<div class="hero-sub">AI-scaffolded group analysis · Alpes Bank GenAI</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="card">', unsafe_allow_html=True)

        tab_create, tab_join = st.tabs(["✨ Create a new group", "🔑 Join existing group"])

        # Build multiselect options once
        bw_options = [f"{b['emoji']} {b['label']}" for b in BUZZ_WORDS]
        bw_slug_map = {f"{b['emoji']} {b['label']}": b["slug"] for b in BUZZ_WORDS}

        with tab_create:
            st.markdown("**Start a new group session**")
            with st.form("create_form"):
                name = st.text_input("Your name", placeholder="e.g. Alice")
                size = st.slider("Group size (including you)", min_value=2, max_value=5, value=3)
                st.markdown("**Your interests** *(pick 2–4 topics — we'll match you to the most relevant case section)*")
                selected_bw = st.multiselect(
                    "Select your interest areas",
                    options=bw_options,
                    max_selections=4,
                    label_visibility="collapsed",
                )
                submitted = st.form_submit_button("Create Group →", use_container_width=True)
                if submitted:
                    if not name.strip():
                        st.error("Please enter your name.")
                    elif len(selected_bw) < 1:
                        st.error("Please select at least one interest area so we can match you to the right section.")
                    else:
                        prefs = [bw_slug_map[b] for b in selected_bw]
                        gd = _create_group(name.strip(), size, prefs)
                        st.session_state["member"] = name.strip()
                        st.session_state["group_code"] = gd["group_code"]
                        st.session_state["page"] = "lobby"
                        st.rerun()

        with tab_join:
            st.markdown("**Join your group's session**")
            with st.form("join_form"):
                name = st.text_input("Your name", placeholder="e.g. Bob")
                code = st.text_input("Group code", placeholder="e.g. ABC123").upper()
                st.markdown("**Your interests** *(pick 2–4 topics — we'll match you to the most relevant case section)*")
                selected_bw = st.multiselect(
                    "Select your interest areas",
                    options=bw_options,
                    max_selections=4,
                    label_visibility="collapsed",
                    key="join_bw",
                )
                submitted = st.form_submit_button("Join Group →", use_container_width=True)
                if submitted:
                    if not name.strip() or not code.strip():
                        st.error("Please enter your name and group code.")
                    elif len(selected_bw) < 1:
                        st.error("Please select at least one interest area.")
                    else:
                        prefs = [bw_slug_map[b] for b in selected_bw]
                        ok, err, gd = _join_group(code.strip(), name.strip(), prefs)
                        if ok:
                            st.session_state["member"] = name.strip()
                            st.session_state["group_code"] = code.strip()
                            st.session_state["page"] = "lobby"
                            st.rerun()
                        else:
                            st.error(err)

        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown("""
<div class="card">
<h3 style="color:#003C87;margin-top:0">How it works</h3>

<div style="display:flex;gap:14px;align-items:flex-start;margin-bottom:16px">
  <div style="font-size:1.8rem;flex-shrink:0">📖</div>
  <div style="color:#2C3E50"><strong style="color:#003C87">Read your section</strong><br>
  Each member gets one section of the Alpes Bank case to analyse in depth.</div>
</div>

<div style="display:flex;gap:14px;align-items:flex-start;margin-bottom:16px">
  <div style="font-size:1.8rem;flex-shrink:0">✍️</div>
  <div style="color:#2C3E50"><strong style="color:#003C87">Submit your analysis</strong><br>
  Answer the section question. An AI tutor gives you scaffolded feedback — no spoilers.</div>
</div>

<div style="display:flex;gap:14px;align-items:flex-start;margin-bottom:16px">
  <div style="font-size:1.8rem;flex-shrink:0">🤝</div>
  <div style="color:#2C3E50"><strong style="color:#003C87">Group alignment</strong><br>
  The Group Alignment Agent compares all submissions, surfaces gaps and free-rider signals.</div>
</div>

<div style="display:flex;gap:14px;align-items:flex-start">
  <div style="font-size:1.8rem;flex-shrink:0">🔗</div>
  <div style="color:#2C3E50"><strong style="color:#003C87">Synthesis</strong><br>
  Your group writes one integrated answer together, drawing on all five sections.</div>
</div>
</div>
""", unsafe_allow_html=True)


def page_lobby():
    """Waiting room — shown after joining/creating until the group is full and sections are assigned."""
    gd = _load_session(st.session_state["group_code"])
    if not gd:
        st.session_state["page"] = "welcome"
        st.rerun()

    member  = st.session_state["member"]
    members = gd.get("members", [])
    expected = gd.get("expected_size", 5)
    phase    = gd.get("phase", "lobby")
    prefs    = gd.get("preferences", {})
    assignments = gd.get("section_assignments", {})

    # Slug → label lookup for displaying tags
    slug_to_label = {b["slug"]: f"{b['emoji']} {b['label']}" for b in BUZZ_WORDS}

    _render_step_indicator(1)

    # ── Auto-advance if group is already full ─────────────────────────────────
    if phase == "reading_ready":
        st.session_state["page"] = "reading"
        st.rerun()

    # ── Header ────────────────────────────────────────────────────────────────
    joined_n  = len(members)
    waiting_n = expected - joined_n

    st.markdown(
        f'<div class="card-blue">'
        f'<h2 style="margin:0 0 6px;color:white !important">⏳ Waiting for your group…</h2>'
        f'<p style="margin:0;opacity:0.85;color:white !important">'
        f'<strong>{joined_n}</strong> of <strong>{expected}</strong> members have joined. '
        f'Sections will be assigned once everyone is in.'
        f'</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    col_code, col_members = st.columns([0.4, 0.6])

    with col_code:
        code = gd["group_code"]
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 🔑 Share this code")
        st.markdown(
            f'<div class="group-code">{code}</div>',
            unsafe_allow_html=True,
        )
        st.caption("Ask your group members to open the app and enter this code.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_members:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 👥 Who's here")

        for m in members:
            member_prefs = prefs.get(m, [])
            tags_html = " ".join(
                f'<span style="background:#E8F0FE;color:#003C87;border-radius:99px;'
                f'padding:2px 10px;font-size:0.75rem;font-weight:600;margin:2px">'
                f'{slug_to_label.get(s, s)}</span>'
                for s in member_prefs
            )
            you = " <em style='color:#6C757D;font-size:0.8rem'>(you)</em>" if m == member else ""
            st.markdown(
                f'<div class="member-row">'
                f'<div class="dot dot-green"></div>'
                f'<span class="member-name">{m}{you}</span>'
                f'</div>'
                f'<div style="padding-left:21px;margin-bottom:8px">{tags_html}</div>',
                unsafe_allow_html=True,
            )

        for i in range(waiting_n):
            st.markdown(
                f'<div class="member-row">'
                f'<div class="dot dot-grey"></div>'
                f'<span class="member-name" style="color:#AAA">Waiting for member {joined_n + i + 1}…</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="feedback-box" style="margin-top:8px">'
        '💡 <strong>While you wait:</strong> Think about what you already know about '
        'GenAI in banking. What risks and opportunities come to mind? '
        'Your section will be tailored to your interests.'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.button("🔄 Check — has everyone joined?", type="primary", use_container_width=False):
        st.rerun()


def page_reading():
    gd = _load_session(st.session_state["group_code"])
    if not gd:
        st.session_state["page"] = "welcome"
        st.rerun()

    member = st.session_state["member"]
    _render_sidebar(gd, member)
    _render_step_indicator(2)

    # Assigned sections
    sec_ids = _member_sections(gd, member)
    sections = [get_section_by_id(sid) for sid in sec_ids]

    st.markdown(
        f'<div class="card-blue">'
        f'<h2 style="margin:0 0 6px;color:white !important">📖 Read your assigned section(s)</h2>'
        f'<p style="margin:0;opacity:0.85;color:white !important">Study the case material carefully before writing your analysis.</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    for sec in sections:
        with st.expander(f"{sec['emoji']} Section {sec['id']}: {sec['title']} ({sec['duration_hint']})", expanded=True):
            st.markdown(
                f'<div class="case-text">{sec["case_text"]}</div>',
                unsafe_allow_html=True,
            )
            st.markdown("---")
            st.markdown(f"**Your section question:**")
            st.info(sec["question"])
            for q in sec["sub_questions"]:
                st.markdown(f"- {q}")

    # ── Full case accordion ───────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("📚 Read the full case study — all five sections", expanded=False):
        st.markdown(
            '<div style="background:#FFF8E7;border-left:4px solid #F39C12;'
            'border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:16px;'
            'font-size:0.88rem;color:#5D4037">'
            '💡 <strong>Context matters.</strong> Reading the other sections helps you understand '
            'how your argument fits into the group\'s overall analysis — and avoids isolated thinking. '
            'Your assigned section is highlighted below.'
            '</div>',
            unsafe_allow_html=True,
        )
        for sec in SECTIONS:
            is_mine = sec["id"] in sec_ids
            badge = "  ← your section" if is_mine else ""
            with st.expander(
                f"{sec['emoji']} §{sec['id']}: {sec['title']}{badge}",
                expanded=is_mine,
            ):
                if is_mine:
                    st.markdown(
                        '<div style="background:#E8F0FE;border-radius:8px;padding:8px 14px;'
                        'font-size:0.83rem;color:#003C87;font-weight:600;margin-bottom:12px">'
                        '⭐ This is your assigned section.</div>',
                        unsafe_allow_html=True,
                    )
                st.markdown(
                    f'<div class="case-text">{sec["case_text"]}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown("---")
                st.markdown(f"**Section question:** {sec['question']}")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            '<div class="feedback-box">'
            '💡 <strong>Tip:</strong> Take notes while reading. '
            'Focus on the core argument of your section before writing.'
            '</div>',
            unsafe_allow_html=True,
        )
    with col2:
        if st.button("I'm ready to write →", type="primary", use_container_width=True):
            # Advance group phase
            gd["phase"] = "working"
            _save_session(gd)
            st.session_state["page"] = "working"
            st.rerun()


def page_working():
    gd = _load_session(st.session_state["group_code"])
    if not gd:
        st.session_state["page"] = "welcome"
        st.rerun()

    member = st.session_state["member"]
    _render_sidebar(gd, member)
    _render_step_indicator(3)

    sec_ids     = _member_sections(gd, member)
    primary_sec = get_section_by_id(sec_ids[0])
    my_sub      = gd.get("submissions", {}).get(member)
    my_feedback = gd.get("feedback", {}).get(member)

    # Blue header bar
    st.markdown(
        f'<div class="card-blue">'
        f'<div class="section-pill">Section {primary_sec["id"]} of 5</div>'
        f'<h2 style="margin:4px 0 6px;color:white !important">{primary_sec["emoji"]} {primary_sec["title"]}</h2>'
        f'<p style="margin:0;opacity:0.9;color:white !important">{primary_sec["question"]}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Three tabs: Write | Read your section | Read full case ───────────────
    tab_write, tab_case, tab_full = st.tabs([
        "✍️ Write your analysis",
        "📖 Read your section",
        "📚 Read full case",
    ])

    with tab_case:
        # Assigned section only — no progress lost, just a tab switch
        st.markdown(
            f'<div class="feedback-box" style="margin-bottom:16px">'
            f'💡 Switching back to <strong>✍️ Write</strong> will restore your draft exactly as you left it. '
            f'Want to read the other sections too? Use the <strong>📚 Read full case</strong> tab.'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="case-text">{primary_sec["case_text"]}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.markdown(f"**Section question:** {primary_sec['question']}")
        for q in primary_sec["sub_questions"]:
            st.markdown(f"- {q}")

    with tab_full:
        # Every section — helps students see the full picture and avoid isolated thinking
        st.markdown(
            '<div class="feedback-box" style="margin-bottom:20px">'
            '📚 <strong>Full case reference</strong> — Reading across all five sections helps you understand '
            'how your argument fits into the bigger picture. Your draft is safe on the '
            '<strong>✍️ Write</strong> tab whenever you return.'
            '</div>',
            unsafe_allow_html=True,
        )
        for sec in SECTIONS:
            is_mine = sec["id"] == primary_sec["id"]
            label = f"{sec['emoji']} §{sec['id']}: {sec['title']}"
            if is_mine:
                label += "  ← **your section**"
            with st.expander(label, expanded=is_mine):
                if is_mine:
                    st.markdown(
                        '<div style="background:#E8F0FE;border-radius:8px;padding:8px 14px;'
                        'font-size:0.83rem;color:#003C87;font-weight:600;margin-bottom:12px">'
                        '⭐ This is your assigned section — you are the group expert on this part.'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                st.markdown(
                    f'<div class="case-text">{sec["case_text"]}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown("---")
                st.markdown(f"**Section question:** {sec['question']}")

    with tab_write:
        col_work, col_feedback = st.columns([1.1, 0.9])

        with col_work:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("#### ✍️ Your Analysis")

            with st.expander("Sub-questions to guide you"):
                for q in primary_sec["sub_questions"]:
                    st.markdown(f"- {q}")
            with st.expander("Key concepts for this section"):
                st.markdown(", ".join(f"`{k}`" for k in primary_sec["key_concepts"]))

            # ── Cross-section connections ─────────────────────────────────────
            my_sid = primary_sec["id"]
            other_secs = [s for s in SECTIONS if s["id"] != my_sid]
            with st.expander("🔗 How your section connects to the group", expanded=True):
                st.markdown(
                    '<div style="font-size:0.9rem;color:#444;margin-bottom:12px">'
                    'A strong analysis doesn\'t stop at your own section. '
                    'As you write, consider these bridges to your colleagues\' work — '
                    'reference at least one in your submission.'
                    '</div>',
                    unsafe_allow_html=True,
                )
                # Assignments may not exist for old sessions — fall back gracefully
                member_assignments = gd.get("section_assignments", {})
                # Build a reverse map: section_id → member name
                sid_to_member = {}
                for m, sids in member_assignments.items():
                    for sid in sids:
                        sid_to_member[sid] = m

                for other in other_secs:
                    oid = other["id"]
                    fwd = SECTION_CONNECTIONS.get((my_sid, oid))
                    bwd = SECTION_CONNECTIONS.get((oid, my_sid))
                    colleague = sid_to_member.get(oid, "a colleague")
                    # Section header row
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:10px;'
                        f'margin:14px 0 6px">'
                        f'<span style="font-size:1.3rem">{other["emoji"]}</span>'
                        f'<strong style="color:#003C87">§{oid}: {other["title"]}</strong>'
                        f'<span style="font-size:0.78rem;color:#888;margin-left:4px">'
                        f'— {colleague}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    if fwd:
                        direction_label, bridge_q = fwd
                        st.markdown(
                            f'<div style="background:#EEF5FF;border-left:3px solid #4F8EF7;'
                            f'border-radius:0 8px 8px 0;padding:10px 14px;'
                            f'font-size:0.85rem;margin-bottom:6px">'
                            f'<span style="color:#003C87;font-weight:600">→ Your section feeds into §{oid}</span>'
                            f'<br><span style="color:#333">{bridge_q}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    if bwd:
                        direction_label, bridge_q = bwd
                        st.markdown(
                            f'<div style="background:#F0FFF4;border-left:3px solid #27AE60;'
                            f'border-radius:0 8px 8px 0;padding:10px 14px;'
                            f'font-size:0.85rem;margin-bottom:6px">'
                            f'<span style="color:#1A7A3C;font-weight:600">← §{oid} feeds into your section</span>'
                            f'<br><span style="color:#333">{bridge_q}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

            already_submitted = bool(my_sub)

            if not already_submitted:
                # ── Draft persisted in session_state via key ──────────────────
                # Using key= means the value survives tab switches and reruns
                draft_key = f"draft_{member}"
                answer = st.text_area(
                    "Write your analysis here",
                    height=300,
                    placeholder=(
                        "Start with your main argument, then support it with evidence from the case.\n\n"
                        "Aim for 150–300 words. As you write, also note how your analysis connects "
                        "to at least one other section — e.g. 'This finding in §X is important because "
                        "it directly shapes the challenge in §Y…'\n\n"
                        "Switch to the 📖 or 📚 tabs at any time to re-read the case without losing your draft."
                    ),
                    key=draft_key,
                )
                word_est = len(answer.split()) if answer else 0
                col_wc, col_btn = st.columns([1, 1])
                with col_wc:
                    colour = "#27AE60" if word_est >= 150 else "#F39C12" if word_est >= 50 else "#E74C3C"
                    st.markdown(
                        f'<p style="color:{colour};font-weight:500;margin-top:8px">'
                        f'~{word_est} words '
                        f'{"✓" if word_est >= 150 else "(aim for 150+)"}'
                        f'</p>',
                        unsafe_allow_html=True,
                    )
                with col_btn:
                    submit = st.button(
                        "Submit & Get Feedback →",
                        type="primary",
                        use_container_width=True,
                        disabled=(word_est < 30),
                    )

                if word_est > 0 and word_est < 30:
                    st.caption("Write at least 30 words to enable submission.")

                if submit:
                    with st.spinner("Saving and generating feedback…"):
                        gd = _submit_answer(
                            st.session_state["group_code"],
                            member,
                            primary_sec["id"],
                            answer,
                        )
                        agent = _get_agent()
                        if agent:
                            try:
                                fb = agent.scaffold_individual_submission(
                                    student_name=member,
                                    section_title=primary_sec["title"],
                                    section_question=primary_sec["question"],
                                    student_text=answer,
                                    expert_summary=EXPERT_ANSWERS[primary_sec["slug"]]["summary"],
                                )
                                gd["feedback"][member] = fb
                                _save_session(gd)
                            except Exception as e:
                                st.warning(f"Feedback generation skipped: {e}")
                    st.rerun()
            else:
                wc = my_sub.get("word_count", 0)
                st.markdown(
                    f'<div class="feedback-box-success">'
                    f'✅ <strong>Submitted!</strong> Your analysis ({wc} words) has been saved.<br>'
                    f'<small>Submitted at {my_sub.get("submitted_at","")[:16]}</small>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.markdown("**Your submitted text:**")
                st.markdown(
                    f'<div style="background:#F8F9FA;border-radius:10px;padding:16px;'
                    f'font-size:0.92rem;line-height:1.7;color:#333">'
                    f'{my_sub["text"]}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)

    with col_feedback:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 🤖 AI Tutor Feedback")

        if my_feedback:
            st.markdown(
                f'<div class="feedback-box">{my_feedback}</div>',
                unsafe_allow_html=True,
            )
        elif my_sub:
            st.info("Feedback is being generated… click Refresh Group Status in the sidebar.")
        else:
            st.markdown(
                '<div style="color:#999;text-align:center;padding:40px 20px">'
                '🎓<br><br>Submit your analysis to receive<br>personalised AI feedback.'
                '</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown("#### 👥 Group Progress")

        members = gd.get("members", [])
        subs    = gd.get("submissions", {})
        submitted_n = len(subs)
        total_n = len(members)

        pct = int(submitted_n / max(total_n, 1) * 100)
        fill_colour = "#27AE60" if pct == 100 else "#F39C12" if pct >= 50 else "#E74C3C"
        st.markdown(
            f'<div style="font-size:0.9rem;margin-bottom:6px">'
            f'<strong>{submitted_n}/{total_n}</strong> members submitted</div>'
            f'<div class="score-track">'
            f'<div style="background:{fill_colour};height:10px;border-radius:99px;width:{pct}%"></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        for m in members:
            sub = subs.get(m)
            if sub:
                wc = sub.get("word_count", 0)
                icon = "🟡" if wc < 40 else "🟢"
                label = f"{wc} words"
            else:
                icon = "⚪"
                label = "pending"
            you = " **(you)**" if m == member else ""
            st.markdown(f"{icon} **{m}**{you} — {label}")

        if submitted_n == total_n:
            st.success("All members submitted! Move to Group Alignment →")
            if st.button("Go to Group Alignment →", type="primary", use_container_width=True):
                st.session_state["page"] = "alignment"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


def page_alignment():
    gd = _load_session(st.session_state["group_code"])
    if not gd:
        st.session_state["page"] = "welcome"
        st.rerun()

    member = st.session_state["member"]
    _render_sidebar(gd, member)
    _render_step_indicator(4)

    st.markdown(
        '<div class="card-blue">'
        '<h2 style="margin:0 0 6px;color:white !important">🤖 Group Alignment Report</h2>'
        '<p style="margin:0;opacity:0.85;color:white !important">'
        'The Group Alignment Agent has analysed all submissions for coherence gaps and contribution balance.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    members     = gd.get("members", [])
    submissions = gd.get("submissions", {})
    assignments = gd.get("section_assignments", {})

    if not _all_submitted(gd):
        missing = [m for m in members if m not in submissions]
        st.warning(
            f"Waiting for {len(missing)} more member(s) to submit: {', '.join(missing)}. "
            "Ask them to join the session and submit their section."
        )
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
        return

    # ── Run / load alignment reports ─────────────────────────────────────────
    reports = gd.get("alignment_reports", [])
    if not reports:
        with st.spinner("Running Group Alignment Agent… this takes ~15 seconds"):
            agent = _get_agent()
            if agent:
                try:
                    # Free-rider check
                    fr_report = agent.check_free_riders(gd)

                    # Fragmentation check
                    sub_texts = {m: submissions[m]["text"] for m in submissions}
                    sec_titles = {
                        m: get_section_by_id(assignments.get(m, [1])[0])["title"]
                        for m in submissions
                        if assignments.get(m)
                    }
                    frag_report = agent.analyze_fragmentation(sub_texts, sec_titles)

                    report = {
                        "timestamp": datetime.now().isoformat(),
                        "free_rider": {
                            "has_issue": fr_report.has_issue,
                            "missing": fr_report.missing_members,
                            "low_effort": fr_report.low_effort_members,
                            "group_message": fr_report.group_message,
                        },
                        "fragmentation": {
                            "score": frag_report.integration_score,
                            "has_gaps": frag_report.has_gaps,
                            "scaffold_questions": frag_report.scaffold_questions,
                            "missing_connections": frag_report.missing_connections,
                            "contradictions": frag_report.contradictions,
                            "summary_html": frag_report.summary_html,
                        },
                    }
                    gd["alignment_reports"].append(report)
                    gd["phase"] = "synthesis"
                    _save_session(gd)
                    reports = gd["alignment_reports"]
                except Exception as e:
                    st.error(f"Alignment analysis failed: {e}")
                    reports = []
            else:
                st.warning("AI agent not available — check your .env file.")

    if not reports:
        return

    latest = reports[-1]
    fr   = latest.get("free_rider", {})
    frag = latest.get("fragmentation", {})

    # ── Free-rider panel ─────────────────────────────────────────────────────
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 👥 Contribution Balance")

        if fr.get("has_issue"):
            st.markdown(
                f'<div class="feedback-box-warn">'
                f'⚠️ {fr.get("group_message","")}'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="feedback-box-success">'
                '✅ All members have contributed a substantive analysis.</div>',
                unsafe_allow_html=True,
            )

        st.markdown("**Submission overview:**")
        for m in members:
            sub = submissions.get(m, {})
            wc  = sub.get("word_count", 0)
            sec_id = assignments.get(m, [1])[0]
            sec = get_section_by_id(sec_id)

            bar_w = min(100, int(wc / 3))  # 300 words = full bar
            bar_c = "#27AE60" if wc >= 150 else "#F39C12" if wc >= 40 else "#E74C3C"

            you = " **(you)**" if m == member else ""
            st.markdown(
                f'<div style="margin-bottom:12px">'
                f'<div style="display:flex;justify-content:space-between;margin-bottom:3px">'
                f'<span style="font-weight:500">{m}{you}</span>'
                f'<span style="font-size:0.8rem;color:#666">{sec["emoji"]} {sec["title"]} · {wc} words</span>'
                f'</div>'
                f'<div class="score-track">'
                f'<div style="background:{bar_c};height:10px;border-radius:99px;width:{bar_w}%"></div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 🧩 Argument Coherence")

        score = frag.get("score", 0)
        bar_c = "#27AE60" if score >= 70 else "#F39C12" if score >= 40 else "#E74C3C"
        label = "Well integrated" if score >= 70 else "Partially integrated" if score >= 40 else "Fragmented"

        st.markdown(
            f'<div style="font-size:1.5rem;font-weight:700;color:{bar_c}">{score}/100</div>'
            f'<div style="color:{bar_c};font-weight:500;margin-bottom:8px">{label}</div>'
            f'<div class="score-track">'
            f'<div style="background:{bar_c};height:10px;border-radius:99px;width:{score}%"></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown(frag.get("summary_html", ""), unsafe_allow_html=True)

        if frag.get("missing_connections"):
            st.markdown("**Bridges to build:**")
            for item in frag["missing_connections"]:
                st.markdown(f"- {item}")

        if frag.get("contradictions"):
            st.markdown("**Tensions to resolve:**")
            for item in frag["contradictions"]:
                st.markdown(f"- ⚡ {item}")

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Scaffold questions ────────────────────────────────────────────────────
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 🎯 Questions to Guide Your Group Discussion")
    st.markdown(
        "Before moving to the synthesis, discuss these questions as a group. "
        "They are designed to help you bridge the gaps between your individual analyses."
    )

    questions = frag.get("scaffold_questions", [])
    for i, q in enumerate(questions, 1):
        st.markdown(
            f'<div class="feedback-box" style="margin-bottom:10px">'
            f'<strong>Q{i}.</strong> {q}'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # ── All submissions viewer ────────────────────────────────────────────────
    with st.expander("📄 Read all group submissions"):
        for m in members:
            sub = submissions.get(m, {})
            sec_id = assignments.get(m, [1])[0]
            sec = get_section_by_id(sec_id)
            st.markdown(
                f'<div class="card" style="margin-bottom:12px">'
                f'<div class="section-pill">{sec["emoji"]} Section {sec_id}: {sec["title"]}</div>'
                f'<div style="font-weight:600;margin-bottom:8px">{m}</div>'
                f'<div style="font-size:0.92rem;line-height:1.7;color:#333">'
                f'{sub.get("text","(no submission)")}'
                f'</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")
    if st.button("Continue to Group Synthesis →", type="primary", use_container_width=True):
        st.session_state["page"] = "synthesis"
        st.rerun()


def page_synthesis():
    gd = _load_session(st.session_state["group_code"])
    if not gd:
        st.session_state["page"] = "welcome"
        st.rerun()

    member = st.session_state["member"]
    _render_sidebar(gd, member)
    _render_step_indicator(5)

    st.markdown(
        '<div class="card-blue">'
        '<h2 style="margin:0 0 6px;color:white !important">🔗 Group Synthesis</h2>'
        '<p style="margin:0;opacity:0.85;color:white !important">'
        'Work together to write one integrated answer that draws on all five sections.'
        '</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Pick a synthesis question (rotate based on session)
    q_idx = len(gd.get("alignment_reports", [])) % len(GROUP_SYNTHESIS_QUESTIONS)
    synthesis_q = GROUP_SYNTHESIS_QUESTIONS[q_idx]

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### The Group Synthesis Question")
    st.info(synthesis_q)

    # Get coaching note from agent
    if "synthesis_coaching" not in gd:
        with st.spinner("Getting coaching note from Group Alignment Agent…"):
            agent = _get_agent()
            if agent:
                try:
                    coaching = agent.generate_synthesis_prompt(gd, synthesis_q)
                    gd["synthesis_coaching"] = coaching
                    _save_session(gd)
                except Exception:
                    gd["synthesis_coaching"] = (
                        "Review each member's section, identify the central argument, "
                        "and discuss: how do the five sections form one coherent story?"
                    )
                    _save_session(gd)

    coaching = gd.get("synthesis_coaching", "")
    if coaching:
        st.markdown(
            f'<div class="feedback-box">'
            f'🤖 <strong>Group Alignment Agent coaching note:</strong><br><br>{coaching}'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # Each member writes their synthesis contribution
    my_synth = gd.get("synthesis_submissions", {}).get(member)

    col_write, col_progress = st.columns([1.2, 0.8])

    with col_write:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"#### ✍️ Your synthesis contribution, {member}")

        if not my_synth:
            with st.form("synthesis_form"):
                synth_text = st.text_area(
                    "Write your integrated answer",
                    height=300,
                    placeholder=(
                        "Draw on your section AND reference at least two other sections. "
                        "Build toward one coherent recommendation for Tamara and the CEO."
                    ),
                )
                wc = len(synth_text.split()) if synth_text else 0
                st.caption(f"~{wc} words")
                submit = st.form_submit_button("Submit Synthesis →", use_container_width=True)
                if submit:
                    if wc < 40:
                        st.warning("Please write at least 40 words.")
                    else:
                        _submit_synthesis(st.session_state["group_code"], member, synth_text)
                        st.rerun()
        else:
            st.markdown(
                '<div class="feedback-box-success">✅ Your synthesis has been submitted!</div>',
                unsafe_allow_html=True,
            )
            st.markdown(my_synth.get("text", ""))

        st.markdown("</div>", unsafe_allow_html=True)

    with col_progress:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### Group Synthesis Progress")
        synth_subs = gd.get("synthesis_submissions", {})
        members = gd.get("members", [])
        for m in members:
            s = synth_subs.get(m)
            icon = "✅" if s else "⏳"
            you = " (you)" if m == member else ""
            wc = len(s["text"].split()) if s else 0
            wc_str = f" · {wc} words" if wc else ""
            st.markdown(f"{icon} **{m}**{you}{wc_str}")

        if len(synth_subs) == len(members):
            st.success("All members have submitted their synthesis!")
            if st.button("View Final Summary →", type="primary", use_container_width=True):
                st.session_state["page"] = "done"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # Reference panel
    with st.expander("📚 Quick reference — all individual submissions"):
        assignments = gd.get("section_assignments", {})
        all_subs = gd.get("submissions", {})
        for m in gd.get("members", []):
            sub = all_subs.get(m, {})
            sec_id = assignments.get(m, [1])[0]
            sec = get_section_by_id(sec_id)
            st.markdown(
                f'**{sec["emoji"]} {m} — {sec["title"]}**\n\n'
                f'{sub.get("text","(no submission)")}\n\n---'
            )


def page_done():
    gd = _load_session(st.session_state["group_code"])
    if not gd:
        st.session_state["page"] = "welcome"
        st.rerun()

    member = st.session_state["member"]
    _render_sidebar(gd, member)

    st.markdown(
        '<div class="card-blue" style="text-align:center">'
        '<div style="font-size:3rem;margin-bottom:8px">🎉</div>'
        '<h2 style="margin:0 0 6px;color:white !important">Session Complete!</h2>'
        '<p style="margin:0;opacity:0.85;color:white !important">'
        'Your group has completed the Alpes Bank case study analysis.'
        '</p></div>',
        unsafe_allow_html=True,
    )

    # Summary stats
    members     = gd.get("members", [])
    subs        = gd.get("submissions", {})
    synth_subs  = gd.get("synthesis_submissions", {})
    assignments = gd.get("section_assignments", {})
    reports     = gd.get("alignment_reports", [])

    col1, col2, col3, col4 = st.columns(4)
    total_words = sum(s.get("word_count", 0) for s in subs.values())
    with col1:
        st.metric("Group Members", len(members))
    with col2:
        st.metric("Total Words Written", total_words)
    with col3:
        score = reports[-1]["fragmentation"]["score"] if reports else 0
        st.metric("Integration Score", f"{score}/100")
    with col4:
        st.metric("Sections Covered", len(subs))

    st.markdown("---")

    # All synthesis contributions
    st.markdown("### 📋 Group Synthesis — All Contributions")
    for m in members:
        s = synth_subs.get(m, {})
        st.markdown(
            f'<div class="card">'
            f'<div style="font-weight:600;color:#003C87;margin-bottom:8px">{m}</div>'
            f'<div style="font-size:0.93rem;line-height:1.75;color:#333">'
            f'{s.get("text","Not submitted")}'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    # Alignment report summary
    if reports:
        with st.expander("🤖 Group Alignment Agent Report"):
            latest = reports[-1]
            frag = latest.get("fragmentation", {})
            st.markdown(f"**Integration score:** {frag.get('score', 0)}/100")
            st.markdown("**Scaffold questions posed:**")
            for q in frag.get("scaffold_questions", []):
                st.markdown(f"- {q}")

    st.markdown("---")
    if st.button("↩ Start a new session", use_container_width=False):
        for key in ["member", "group_code", "page"]:
            st.session_state.pop(key, None)
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# Router
# ══════════════════════════════════════════════════════════════════════════════

def main():
    # Init session state
    if "page" not in st.session_state:
        st.session_state["page"] = "welcome"

    page = st.session_state["page"]

    # If we have a group code, reload latest group data at the top
    if page != "welcome" and "group_code" in st.session_state:
        gd = _load_session(st.session_state["group_code"])
        if gd is None:
            st.session_state["page"] = "welcome"
            page = "welcome"
        else:
            # Auto-advance based on server-side phase
            server_phase = gd.get("phase", "lobby")
            # Group filled up while this member was in the lobby
            if server_phase == "reading_ready" and page == "lobby":
                st.session_state["page"] = "reading"
                page = "reading"
            # All submitted — move to alignment
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
        "done":      page_done,
    }

    routes.get(page, page_welcome)()


if __name__ == "__main__":
    main()
