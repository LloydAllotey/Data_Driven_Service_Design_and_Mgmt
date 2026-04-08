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

try:
    import plotly.graph_objects as go
    _PLOTLY_AVAILABLE = True
except ImportError:
    _PLOTLY_AVAILABLE = False

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


def _create_group(creator_name: str, group_size: int, preferences: list,
                  internal_deadline: Optional[str] = None,
                  external_deadline: Optional[str] = None) -> dict:
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
        "internal_deadline": internal_deadline,   # ISO str or None — individual submission deadline
        "external_deadline": external_deadline,   # ISO str or None — synthesis / final deadline
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


def _compute_contribution_scores(group_data: dict) -> dict:
    """
    Compute a 0-100 Contribution Balance Score per member.

    Components
    ----------
    Completion   0–10   On time (≤ individual deadline) = 10; after or missing = 0
    Effort       0–20   Word count relative to group median
    Substance    0–35   AI-evaluated: relevance, depth, case-specificity
                        (structural fallback: sentence depth × vocabulary uniqueness)
    Engagement   0–15   AI-evaluated: cross-section connections and integration
                        (structural fallback: pattern-matched section references)
    Synthesis    0–20   AI-evaluated: quality of synthesis contribution
                        (structural fallback: word count + unique-word ratio)
    ─────────────────────────────────────────────────────────────────────────
    Total        0–100

    AI scores are read from group_data["ai_content_scores"] when available
    (computed once by _trigger_ai_content_scoring and cached in the session file).
    Until AI scoring runs, structural heuristics are used as provisional scores.
    """
    import statistics, re

    members       = group_data.get("members", [])
    submissions   = group_data.get("submissions", {})
    synth_subs    = group_data.get("synthesis_submissions", {})
    internal_dl   = group_data.get("internal_deadline")
    ai_cache      = group_data.get("ai_content_scores", {})   # cached AI scores

    member_set = set(m.lower() for m in members)

    word_counts = [
        submissions[m].get("word_count", 0)
        for m in members
        if m in submissions and submissions[m].get("word_count", 0) > 0
    ]
    median_wc = statistics.median(word_counts) if word_counts else 0

    # ── Structural helpers (fallback only) ────────────────────────────────────
    def _unique_word_ratio(text: str) -> float:
        content_words = [w for w in re.findall(r'[a-z]+', text.lower()) if len(w) > 3]
        if not content_words:
            return 0.0
        return len(set(content_words)) / len(content_words)

    def _sentence_rep_ratio(text: str) -> float:
        sents = [s.strip().lower() for s in re.split(r'[.!?]', text) if len(s.strip()) > 8]
        if not sents:
            return 0.0
        return 1 - (len(set(sents)) / len(sents))

    scores = {}
    for member in members:
        sub        = submissions.get(member)
        synth      = synth_subs.get(member)
        member_ai  = ai_cache.get(member, {})   # {} if AI not yet run
        ai_scored  = bool(member_ai)             # True once AI has evaluated

        # ── 1. Completion (0–10) ──────────────────────────────────────────────
        if sub:
            if internal_dl:
                try:
                    submitted_at = datetime.fromisoformat(sub.get("submitted_at", ""))
                    deadline_dt  = datetime.fromisoformat(internal_dl)
                    on_time      = submitted_at <= deadline_dt
                    completion   = 10 if on_time else 0
                    on_time_label = (
                        "Submitted on time ✓"
                        if on_time
                        else "Submitted after individual deadline"
                    )
                except Exception:
                    completion, on_time, on_time_label = 7, None, "No deadline set"
            else:
                completion, on_time, on_time_label = 7, None, "No deadline set"
        else:
            completion, on_time, on_time_label = 0, False, "Not submitted"

        # ── 2. Effort relative to median (0–20) ───────────────────────────────
        wc = sub.get("word_count", 0) if sub else 0
        if median_wc > 0 and wc > 0:
            ratio = wc / median_wc
            if   ratio >= 1.0:  effort = 20; effort_label = f"{wc} words — at or above group median"
            elif ratio >= 0.75: effort = 15; effort_label = f"{wc} words — slightly below group median"
            elif ratio >= 0.5:  effort = 10; effort_label = f"{wc} words — well below group median"
            elif ratio >= 0.25: effort = 5;  effort_label = f"{wc} words — much shorter than peers"
            else:               effort = 0;  effort_label = f"{wc} words — minimal contribution"
        elif wc > 0:
            effort = 14; effort_label = f"{wc} words (only submitter, no group median yet)"
        else:
            effort = 0;  effort_label = "No submission"

        # ── 3. Substance (0–35) — AI-primary, structural fallback ─────────────
        if ai_scored and "substance" in member_ai:
            substance       = member_ai["substance"]
            substance_label = member_ai.get("substance_feedback", "")
            substance_source = "ai"
        elif sub:
            text      = sub.get("text", "")
            raw_sents = [s.strip() for s in re.split(r'[.!?]', text) if len(s.strip()) > 8]
            n_sent    = len(raw_sents)
            uwr       = _unique_word_ratio(text)
            srr       = _sentence_rep_ratio(text)
            depth_pts = min(n_sent, 10) * 2.0                          # 0-20
            quality_m = max(0.0, min(1.0, (uwr - 0.35) / 0.30))
            sent_pen  = srr * 5
            raw_sub   = depth_pts * quality_m - sent_pen
            substance = max(0, min(35, round(raw_sub * (35 / 20))))    # scale to 35
            if uwr < 0.35:
                substance_label = (
                    f"⚠️ High word repetition ({round(uwr*100)}% unique words) — "
                    f"provisional score, AI evaluation pending"
                )
            elif n_sent >= 8:
                substance_label = f"{n_sent} sentences, {round(uwr*100)}% vocabulary variety — provisional, AI evaluation pending"
            else:
                substance_label = f"{n_sent} sentences — provisional score, AI evaluation pending"
            substance_source = "structural"
        else:
            substance = 0; substance_label = "No submission"; substance_source = "structural"

        # ── 4. Engagement (0–15) — AI-primary, structural fallback ───────────
        if ai_scored and "engagement" in member_ai:
            engagement       = member_ai["engagement"]
            engagement_label = member_ai.get("engagement_feedback", "")
            engagement_source = "ai"
        elif sub:
            text_lower = sub.get("text", "").lower()
            sec_refs = re.findall(
                r'§\s*[1-5]|section\s+[1-5one-five]|sect\.\s*[1-5]|\bpart\s+[1-5]\b',
                text_lower,
            )
            peer_refs = [
                m for m in member_set
                if m != member.lower() and len(m) > 2 and m in text_lower
            ]
            total_refs = len(set(sec_refs)) + len(peer_refs)
            engagement = min(15, total_refs * 5)
            if total_refs == 0:
                engagement_label = "No cross-section references detected — provisional, AI evaluation pending"
            elif total_refs == 1:
                engagement_label = f"1 cross-section reference — provisional, AI evaluation pending"
            else:
                engagement_label = f"{total_refs} cross-section references — provisional, AI evaluation pending"
            engagement_source = "structural"
        else:
            engagement = 0; engagement_label = "No submission"; engagement_source = "structural"

        # ── 5. Synthesis (0–20) — AI-primary, structural fallback ────────────
        if ai_scored and "synthesis" in member_ai:
            synthesis       = member_ai["synthesis"]
            synthesis_label = member_ai.get("synthesis_feedback", "")
            synthesis_source = "ai"
        elif synth:
            synth_text = synth.get("text", "")
            synth_wc   = len(synth_text.split())
            synth_uwr  = _unique_word_ratio(synth_text)
            if synth_wc >= 30 and synth_uwr >= 0.40:
                synthesis = 20
                synthesis_label = f"Contributed {synth_wc} words — provisional, AI evaluation pending"
            elif synth_wc >= 30:
                synthesis = 10
                synthesis_label = (
                    f"⚠️ High repetition in synthesis ({round(synth_uwr*100)}% unique) — "
                    f"provisional, AI evaluation pending"
                )
            elif synth_wc > 0:
                synthesis = 5
                synthesis_label = f"Only {synth_wc} words — too short (min. 30), provisional"
            else:
                synthesis = 0; synthesis_label = "Did not contribute to synthesis"
            synthesis_source = "structural"
        else:
            synthesis = 0; synthesis_label = "Did not contribute to synthesis"; synthesis_source = "structural"

        total = completion + effort + substance + engagement + synthesis

        if   total >= 80: colour = "#27AE60"; label = "Excellent"
        elif total >= 60: colour = "#F39C12"; label = "Good"
        elif total >= 40: colour = "#E67E22"; label = "Needs improvement"
        else:             colour = "#E74C3C"; label = "Low contribution"

        scores[member] = {
            "total":             total,
            "completion":        completion,
            "effort":            effort,
            "substance":         substance,
            "engagement":        engagement,
            "synthesis":         synthesis,
            "ai_scored":         ai_scored,
            "word_count":        wc,
            "median_wc":         round(median_wc),
            "on_time":           on_time,
            "on_time_label":     on_time_label,
            "effort_label":      effort_label,
            "substance_label":   substance_label,
            "engagement_label":  engagement_label,
            "synthesis_label":   synthesis_label,
            "colour":            colour,
            "label":             label,
        }

    return scores


def _trigger_ai_content_scoring(code: str, group_data: dict) -> dict:
    """
    Calls the GroupAlignmentAgent to AI-evaluate Substance, Engagement, and Synthesis
    for all members. Caches results in the session file under 'ai_content_scores'.
    Returns the updated group_data dict (with ai_content_scores populated).
    """
    agent = _get_agent()
    if not agent:
        return group_data

    assignments = group_data.get("section_assignments", {})
    section_titles = {
        m: get_section_by_id(assignments.get(m, [1])[0])["title"]
        for m in group_data.get("members", [])
        if assignments.get(m)
    }

    try:
        ai_scores = agent.score_contributions(group_data, section_titles)
        # Reload fresh copy in case another member saved in the meantime
        fresh = _load_session(code)
        if fresh is not None:
            fresh["ai_content_scores"] = ai_scores
            _save_session(fresh)
            return fresh
        group_data["ai_content_scores"] = ai_scores
        _save_session(group_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        st.warning(f"AI content scoring failed: {e}")

    return group_data


def _render_score_donut(my_score: dict) -> None:
    """
    Render a donut chart breaking down the contribution score.
    Uses plotly when available; falls back to a pure CSS/HTML conic-gradient
    chart that works with zero additional dependencies.
    """
    components = [
        ("Completion",  my_score.get("completion", 0),  "#27AE60"),
        ("Effort",      my_score.get("effort",     0),  "#3498DB"),
        ("Substance",   my_score.get("substance",  0),  "#8E44AD"),
        ("Engagement",  my_score.get("engagement", 0),  "#16A085"),
        ("Synthesis",   my_score.get("synthesis",  0),  "#E67E22"),
    ]
    total  = sum(v for _, v, _ in components)
    missed = max(0, 100 - total)
    colour = my_score.get("colour", "#2C3E50")

    # ── Plotly version (richer, interactive) ─────────────────────────────────
    if _PLOTLY_AVAILABLE:
        labels  = [c[0] for c in components] + ["Missed"]
        values  = [c[1] for c in components] + [missed]
        colours = [c[2] for c in components] + ["#ECEFF1"]

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.62,
            marker=dict(colors=colours, line=dict(color="#ffffff", width=2)),
            textinfo="label+value",
            hovertemplate="%{label}: %{value} pts<extra></extra>",
            sort=False,
        )])
        fig.update_layout(
            annotations=[dict(
                text=f"<b>{total}</b><br>/100",
                x=0.5, y=0.5,
                font=dict(size=20, color=colour),
                showarrow=False,
            )],
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="center", x=0.5),
            margin=dict(l=10, r=10, t=10, b=40),
            height=320,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        return

    # ── CSS conic-gradient fallback (no extra dependencies) ──────────────────
    # Build conic-gradient stops (each component occupies its score % of the circle)
    stops = []
    cursor = 0
    for _, val, col in components:
        if val > 0:
            stops.append(f"{col} {cursor}% {cursor + val}%")
            cursor += val
    if missed > 0:
        stops.append(f"#ECEFF1 {cursor}% 100%")
    gradient = ", ".join(stops) if stops else "#ECEFF1 0% 100%"

    # Legend rows
    legend_rows = "".join(
        f'<div style="display:flex;align-items:center;gap:7px;margin-bottom:5px">'
        f'<div style="width:11px;height:11px;border-radius:3px;background:{col};flex-shrink:0"></div>'
        f'<span style="font-size:0.78rem;color:#444">{name} <strong>{val}</strong>/{"10" if name=="Completion" else "20" if name in ("Effort","Synthesis") else "35" if name=="Substance" else "15"}</span>'
        f'</div>'
        for name, val, col in components
    )
    legend_rows += (
        f'<div style="display:flex;align-items:center;gap:7px;margin-top:4px">'
        f'<div style="width:11px;height:11px;border-radius:3px;background:#ECEFF1;'
        f'border:1px solid #ccc;flex-shrink:0"></div>'
        f'<span style="font-size:0.78rem;color:#aaa">Missed <strong>{missed}</strong></span>'
        f'</div>'
    )

    html = f"""
<div style="display:flex;align-items:center;justify-content:center;gap:28px;padding:12px 4px">
  <!-- Donut ring -->
  <div style="position:relative;width:155px;height:155px;flex-shrink:0">
    <div style="
      width:155px;height:155px;border-radius:50%;
      background:conic-gradient({gradient});
    "></div>
    <!-- Centre hole -->
    <div style="
      position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
      width:88px;height:88px;border-radius:50%;
      background:white;
      display:flex;flex-direction:column;align-items:center;justify-content:center;
      box-shadow:inset 0 0 6px rgba(0,0,0,0.04);
    ">
      <span style="font-size:1.75rem;font-weight:800;color:{colour};line-height:1">{total}</span>
      <span style="font-size:0.7rem;color:#aaa">/100</span>
    </div>
  </div>
  <!-- Legend -->
  <div style="min-width:140px">
    {legend_rows}
  </div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


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

        # ── Deadlines ─────────────────────────────────────────────────────────
        int_dl = group_data.get("internal_deadline")
        ext_dl = group_data.get("external_deadline")
        if int_dl or ext_dl:
            st.markdown("---")
            st.markdown("**⏰ Deadlines**")
            if int_dl:
                d = datetime.fromisoformat(int_dl)
                past = datetime.now() > d
                flag = " ⚠️" if past else ""
                st.markdown(f'<div style="font-size:0.82rem;color:{"#E74C3C" if past else "#2C3E50"}">📝 Individual submission: <strong>{d.strftime("%d %b %Y")}</strong>{flag}</div>', unsafe_allow_html=True)
            if ext_dl:
                d = datetime.fromisoformat(ext_dl)
                past = datetime.now() > d
                flag = " ⚠️" if past else ""
                st.markdown(f'<div style="font-size:0.82rem;color:{"#E74C3C" if past else "#2C3E50"}">🏁 Final submission: <strong>{d.strftime("%d %b %Y")}</strong>{flag}</div>', unsafe_allow_html=True)

        # ── Live contribution scores ───────────────────────────────────────────
        c_scores = _compute_contribution_scores(group_data)
        if any(c_scores[m]["total"] > 0 for m in c_scores):
            st.markdown("---")
            st.markdown("**📊 Contribution Balance**")
            for m in members:
                cs = c_scores.get(m, {})
                total  = cs.get("total", 0)
                colour = cs.get("colour", "#BDC3C7")
                lbl    = cs.get("label", "—")
                you    = " (you)" if m == current_member else ""
                bar_w  = total
                st.markdown(
                    f'<div style="margin-bottom:8px">'
                    f'<div style="display:flex;justify-content:space-between;font-size:0.8rem;margin-bottom:2px">'
                    f'<span style="font-weight:500;color:#2C3E50">{m}{you}</span>'
                    f'<span style="font-weight:700;color:{colour}">{total}/100</span>'
                    f'</div>'
                    f'<div style="background:#E9ECEF;border-radius:99px;height:6px;overflow:hidden">'
                    f'<div style="background:{colour};width:{bar_w}%;height:6px;border-radius:99px"></div>'
                    f'</div>'
                    f'<div style="font-size:0.7rem;color:#888;margin-top:1px">{lbl}</div>'
                    f'</div>',
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
                st.markdown("**Deadlines** *(optional — helps track timely contribution)*")
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    internal_date = st.date_input(
                        "📝 Individual submissions by",
                        value=None,
                        help="Members should submit their section analysis before this date.",
                    )
                with col_dl2:
                    external_date = st.date_input(
                        "🏁 Final submission",
                        value=None,
                        help="The group synthesis round should be completed by this date.",
                    )
                submitted = st.form_submit_button("Create Group →", use_container_width=True)
                if submitted:
                    if not name.strip():
                        st.error("Please enter your name.")
                    elif len(selected_bw) < 1:
                        st.error("Please select at least one interest area so we can match you to the right section.")
                    elif internal_date and external_date and internal_date > external_date:
                        st.error("⚠️ The individual submission deadline cannot be after the final submission deadline. Please correct the dates.")
                    else:
                        prefs = [bw_slug_map[b] for b in selected_bw]
                        int_dl = datetime(internal_date.year, internal_date.month, internal_date.day, 23, 59).isoformat() if internal_date else None
                        ext_dl = datetime(external_date.year, external_date.month, external_date.day, 23, 59).isoformat() if external_date else None
                        gd = _create_group(name.strip(), size, prefs, int_dl, ext_dl)
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

    # ── Contribution Balance panel ────────────────────────────────────────────
    c_scores = _compute_contribution_scores(gd)
    group_avg = round(sum(c_scores[m]["total"] for m in members) / max(len(members), 1))

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 📊 Contribution Balance")

        # Group-level summary
        avg_colour = "#27AE60" if group_avg >= 70 else "#F39C12" if group_avg >= 50 else "#E74C3C"
        st.markdown(
            f'<div style="display:flex;align-items:baseline;gap:8px;margin-bottom:4px">'
            f'<span style="font-size:2rem;font-weight:700;color:{avg_colour}">{group_avg}</span>'
            f'<span style="font-size:1rem;color:#888">/100 group average</span>'
            f'</div>'
            f'<div class="score-track" style="margin-bottom:16px">'
            f'<div style="background:{avg_colour};width:{group_avg}%;height:10px;border-radius:99px"></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Group-level narrative (Diana's recommendation) ───────────────────
        submitted_count   = sum(1 for m in members if c_scores.get(m, {}).get("total", 0) > 0)
        engaged_count     = sum(1 for m in members if c_scores.get(m, {}).get("engagement", 0) > 0)
        scores_list       = [c_scores.get(m, {}).get("total", 0) for m in members]
        max_score         = max(scores_list) if scores_list else 0
        heavy_reliance    = max_score > 0 and (max_score - min(scores_list)) >= 35

        if submitted_count == len(members):
            contrib_msg = "All members have submitted — well done!"
        elif submitted_count == 0:
            contrib_msg = "No submissions yet."
        else:
            missing_n = len(members) - submitted_count
            contrib_msg = f"{submitted_count} of {len(members)} members have submitted; {missing_n} still missing."

        if heavy_reliance:
            reliance_msg = "⚠️ The group is relying heavily on one or two members — consider redistributing effort before synthesis."
        else:
            reliance_msg = "Contribution is reasonably balanced across the group."

        if engaged_count == len(members):
            integration_msg = f"All {len(members)} members referenced other sections — strong cross-section integration."
        elif engaged_count == 0:
            integration_msg = "No members have referenced other sections yet — add cross-section links to boost your Engagement score."
        else:
            integration_msg = f"{engaged_count} of {len(members)} members connected their section to others."

        st.markdown(
            f'<div style="background:#F0F4FF;border-left:3px solid #003C87;border-radius:6px;'
            f'padding:10px 14px;margin-bottom:14px;font-size:0.83rem;line-height:1.6">'
            f'📋 <strong>Group snapshot:</strong> {contrib_msg} {reliance_msg} {integration_msg}'
            f'</div>',
            unsafe_allow_html=True,
        )

        if fr.get("has_issue"):
            st.markdown(
                f'<div class="feedback-box-warn" style="margin-bottom:12px">'
                f'⚠️ {fr.get("group_message","")}'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("**Score breakdown by member:**")
        st.markdown(
            '<div style="font-size:0.75rem;color:#888;margin-bottom:10px">'
            'Completion /10 · Effort /20 · Substance /35 · Engagement /15 · Synthesis /20 '
            '— ✨ AI-evaluated'
            '</div>',
            unsafe_allow_html=True,
        )

        for m in members:
            cs  = c_scores.get(m, {})
            tot = cs.get("total", 0)
            col = cs.get("colour", "#BDC3C7")
            lbl = cs.get("label", "—")
            you = " (you)" if m == member else ""
            sec_id = assignments.get(m, [1])[0]
            sec = get_section_by_id(sec_id)

            # Component pips
            comp_html = "".join([
                f'<span style="font-size:0.72rem;background:#E8F0FE;color:#003C87;'
                f'border-radius:4px;padding:1px 6px;margin-right:3px">'
                f'{k}: {v}</span>'
                for k, v in [
                    ("C", cs.get("completion", 0)),
                    ("E", cs.get("effort", 0)),
                    ("Su", cs.get("substance", 0)),
                    ("Eng", cs.get("engagement", 0)),
                    ("Sy", cs.get("synthesis", 0)),
                ]
            ])

            st.markdown(
                f'<div style="margin-bottom:14px">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px">'
                f'<span style="font-weight:600;font-size:0.88rem">{m}{you}</span>'
                f'<span style="font-weight:700;color:{col};font-size:0.9rem">{tot}/100 — {lbl}</span>'
                f'</div>'
                f'<div style="font-size:0.75rem;color:#888;margin-bottom:4px">{sec["emoji"]} {sec["title"]} · {cs.get("word_count",0)} words (group median: {cs.get("median_wc",0)})</div>'
                f'<div class="score-track" style="margin-bottom:4px">'
                f'<div style="background:{col};width:{tot}%;height:8px;border-radius:99px"></div>'
                f'</div>'
                f'<div>{comp_html}</div>'
                f'</div>',
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

    # ── AI content scoring (runs once; cached in session) ─────────────────────
    code = st.session_state["group_code"]
    all_synth_done = len(gd.get("synthesis_submissions", {})) >= len(members)
    ai_already_scored = bool(gd.get("ai_content_scores"))

    if all_synth_done and not ai_already_scored:
        with st.spinner("✨ AI is evaluating submission quality — this takes ~20 seconds…"):
            gd = _trigger_ai_content_scoring(code, gd)
        st.rerun()

    # ── Group-level contribution narrative ────────────────────────────────────
    st.markdown("---")
    c_scores  = _compute_contribution_scores(gd)
    group_avg = round(sum(c_scores[m]["total"] for m in members) / max(len(members), 1))

    scores_list    = [c_scores[m]["total"] for m in members]
    engaged_count  = sum(1 for m in members if c_scores[m].get("engagement", 0) > 0)
    heavy_reliance = (max(scores_list) - min(scores_list)) >= 35 if scores_list else False

    if heavy_reliance:
        reliance_msg = "⚠️ The group relied heavily on one or two members."
    else:
        reliance_msg = "Contribution was reasonably balanced across the group."

    if engaged_count == len(members):
        integration_msg = f"All {len(members)} members referenced other sections — great cross-section thinking!"
    elif engaged_count == 0:
        integration_msg = "No members referenced other sections in their analysis."
    else:
        integration_msg = f"{engaged_count} of {len(members)} members connected their section to others."

    st.markdown(
        f'<div style="background:#F0F4FF;border-left:3px solid #003C87;border-radius:6px;'
        f'padding:12px 16px;margin-bottom:16px;font-size:0.88rem;line-height:1.7">'
        f'<strong>📋 Group summary:</strong> Group average score: <strong>{group_avg}/100</strong>. '
        f'{reliance_msg} {integration_msg}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Personal contribution report card ─────────────────────────────────────
    st.markdown("### 📊 Your Contribution Report")

    my_score  = c_scores.get(member, {})

    if my_score:
        tot    = my_score["total"]
        colour = my_score["colour"]
        label  = my_score["label"]
        ai_ok  = my_score.get("ai_scored", False)
        ai_badge = (
            '<span style="font-size:0.75rem;background:#E8F5E9;color:#27AE60;'
            'border-radius:4px;padding:2px 8px;margin-left:8px">✨ AI-evaluated</span>'
            if ai_ok else
            '<span style="font-size:0.75rem;background:#FFF3E0;color:#E67E22;'
            'border-radius:4px;padding:2px 8px;margin-left:8px">⏳ Provisional</span>'
        )

        # Hero score + pie chart side by side
        col_hero, col_pie = st.columns([1, 1.2])

        with col_hero:
            st.markdown(
                f'<div class="card" style="text-align:center;padding:28px 20px;height:100%">'
                f'<div style="font-size:3.5rem;font-weight:800;color:{colour};line-height:1">{tot}</div>'
                f'<div style="font-size:1.05rem;color:{colour};font-weight:600;margin-bottom:6px">/100 — {label}</div>'
                f'{ai_badge}'
                f'<div style="font-size:0.85rem;color:#888;margin-top:8px">Group average: {group_avg}/100</div>'
                f'<div style="background:#E9ECEF;border-radius:99px;height:10px;margin:14px auto;max-width:260px;overflow:hidden">'
                f'<div style="background:{colour};width:{tot}%;height:10px;border-radius:99px"></div>'
                f'</div>'
                f'<div style="font-size:0.78rem;color:#aaa;margin-top:4px">'
                f'Completion /10 · Effort /20 · Substance /35<br>Engagement /15 · Synthesis /20'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with col_pie:
            st.markdown('<div class="card" style="padding:16px">', unsafe_allow_html=True)
            st.markdown(
                '<div style="font-size:0.85rem;font-weight:600;color:#2C3E50;margin-bottom:6px">'
                '📊 Score breakdown</div>',
                unsafe_allow_html=True,
            )
            _render_score_donut(my_score)
            st.markdown("</div>", unsafe_allow_html=True)

        # Component breakdown cards
        st.markdown("<br>", unsafe_allow_html=True)
        components = [
            {
                "name":    "Completion",
                "max":     10,
                "score":   my_score["completion"],
                "icon":    "✅",
                "detail":  my_score["on_time_label"],
                "explain": "On time = 10 pts; after the individual submission deadline = 0 pts.",
                "ai":      False,
            },
            {
                "name":    "Effort",
                "max":     20,
                "score":   my_score["effort"],
                "icon":    "✍️",
                "detail":  my_score["effort_label"],
                "explain": "Word count relative to group median. Rewards proportional contribution, not a fixed target.",
                "ai":      False,
            },
            {
                "name":    "Substance",
                "max":     35,
                "score":   my_score["substance"],
                "icon":    "🔬",
                "detail":  my_score["substance_label"],
                "explain": (
                    "AI evaluates whether your analysis is case-specific, structured, and insightful. "
                    "Off-topic or repetitive content scores near zero regardless of word count."
                ),
                "ai":      ai_ok,
            },
            {
                "name":    "Engagement",
                "max":     15,
                "score":   my_score["engagement"],
                "icon":    "🔗",
                "detail":  my_score["engagement_label"],
                "explain": (
                    "AI evaluates how well you connected your section to other parts of the case. "
                    "Explicit cross-section links and integration earn full marks."
                ),
                "ai":      ai_ok,
            },
            {
                "name":    "Synthesis",
                "max":     20,
                "score":   my_score["synthesis"],
                "icon":    "🤝",
                "detail":  my_score["synthesis_label"],
                "explain": (
                    "AI evaluates your synthesis contribution: does it integrate multiple sections "
                    "with specific Alpes Bank context?"
                ),
                "ai":      ai_ok,
            },
        ]

        cols = st.columns(2)
        for i, comp in enumerate(components):
            s      = comp["score"]
            m_val  = comp["max"]
            pct    = int(s / m_val * 100)
            c      = "#27AE60" if pct >= 80 else "#F39C12" if pct >= 50 else "#E74C3C"
            ai_pip = (
                '<span style="font-size:0.68rem;background:#E8F5E9;color:#27AE60;'
                'border-radius:3px;padding:1px 5px;margin-left:4px">✨ AI</span>'
                if comp["ai"] else ""
            )
            with cols[i % 2]:
                st.markdown(
                    f'<div class="card" style="margin-bottom:12px;padding:18px 20px">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">'
                    f'<span style="font-size:1rem">{comp["icon"]} <strong>{comp["name"]}</strong>{ai_pip}</span>'
                    f'<span style="font-weight:700;color:{c};font-size:1.1rem">{s}/{m_val}</span>'
                    f'</div>'
                    f'<div style="background:#E9ECEF;border-radius:99px;height:7px;margin-bottom:8px;overflow:hidden">'
                    f'<div style="background:{c};width:{pct}%;height:7px;border-radius:99px"></div>'
                    f'</div>'
                    f'<div style="font-size:0.82rem;color:#444;margin-bottom:4px"><strong>{comp["detail"]}</strong></div>'
                    f'<div style="font-size:0.78rem;color:#888;line-height:1.4">{comp["explain"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        # All members overview
        with st.expander("👥 See all members' scores"):
            for m in members:
                cs  = c_scores.get(m, {})
                t   = cs.get("total", 0)
                col = cs.get("colour", "#BDC3C7")
                lbl = cs.get("label", "—")
                you = " (you)" if m == member else ""
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:10px">'
                    f'<span style="font-weight:600;min-width:120px">{m}{you}</span>'
                    f'<div style="flex:1;background:#E9ECEF;border-radius:99px;height:8px;overflow:hidden">'
                    f'<div style="background:{col};width:{t}%;height:8px;border-radius:99px"></div>'
                    f'</div>'
                    f'<span style="font-weight:700;color:{col};min-width:70px;text-align:right">{t}/100 {lbl}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

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
