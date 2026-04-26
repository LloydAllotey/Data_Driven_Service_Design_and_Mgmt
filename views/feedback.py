"""
views/feedback.py — End-of-session AI feedback questionnaire.

Students rate the quality of AI scaffolding, collaboration features, and
learning outcomes on a 9-point Likert scale (mirroring the CLT instrument
from the scaffolding_multiagentsystem prototype), plus one agent-perception
MCQ and open-ended improvement prompts.

Responses are stored in two places:
  1. sessions/{GROUP_CODE}.json  under  "feedback_responses": {member: {...}}
  2. feedback_data/feedback_{GROUP_CODE}_{member_slug}_{ts}.json  (standalone)
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from database.storage import _load_session, _save_session

ROOT         = Path(__file__).parent.parent
FEEDBACK_DIR = ROOT / "feedback_data"
FEEDBACK_DIR.mkdir(exist_ok=True)


# ── Scale definitions ─────────────────────────────────────────────────────────

_LIKERT_9 = [
    "1 — Strongly disagree",
    "2",
    "3",
    "4",
    "5 — Neutral",
    "6",
    "7",
    "8",
    "9 — Strongly agree",
]

_OVERALL_OPTIONS = [
    "1 — Poor",
    "2 — Below average",
    "3 — Average",
    "4 — Good",
    "5 — Excellent",
]

_AGENT_DIFF_OPTIONS = [
    "Yes — they clearly served different purposes",
    "Somewhat — I noticed differences but wasn't always sure which was which",
    "No — they felt like the same AI throughout",
    "I didn't notice there were two different AI components",
]


# ── Question banks ────────────────────────────────────────────────────────────

AI_SCAFFOLDING_ITEMS = [
    {
        "code":      "AS1",
        "construct": "AI_Scaffolding",
        "statement": (
            "The AI feedback on my individual submission helped me deepen "
            "my analysis of the Alpes Bank case."
        ),
    },
    {
        "code":      "AS2",
        "construct": "AI_Scaffolding",
        "statement": (
            "The scaffolding questions posed by the AI encouraged me to think "
            "beyond my assigned section."
        ),
    },
    {
        "code":      "AS3",
        "construct": "AI_Scaffolding",
        "statement": (
            "The Group Alignment Agent's report gave me a clearer understanding "
            "of how our sections connect."
        ),
    },
    {
        "code":      "AS4",
        "construct": "AI_Scaffolding",
        "statement": (
            "The AI coaching note during the synthesis round helped me write "
            "a more integrated answer."
        ),
    },
    {
        "code":      "AS5",
        "construct": "AI_Scaffolding",
        "statement": "The AI feedback was clear, relevant, and easy to act upon.",
    },
]

GROUP_COLLAB_ITEMS = [
    {
        "code":      "GC1",
        "construct": "Group_Collaboration",
        "statement": (
            "The jigsaw structure (each member responsible for one section) "
            "helped our group cover the case comprehensively."
        ),
    },
    {
        "code":      "GC2",
        "construct": "Group_Collaboration",
        "statement": (
            "Knowing that contribution scores were visible motivated me to "
            "engage more thoroughly with the case."
        ),
    },
    {
        "code":      "GC3",
        "construct": "Group_Collaboration",
        "statement": "The group chat was a useful coordination tool during the session.",
    },
    {
        "code":      "GC4",
        "construct": "Group_Collaboration",
        "statement": "The peer comment feature gave me useful perspectives on my submission.",
    },
]

LEARNING_OUTCOME_ITEMS = [
    {
        "code":      "LO1",
        "construct": "Learning_Outcomes",
        "statement": (
            "This session improved my understanding of the strategic trade-offs "
            "involved in deploying GenAI at a retail bank."
        ),
    },
    {
        "code":      "LO2",
        "construct": "Learning_Outcomes",
        "statement": (
            "The synthesis round helped me construct a more coherent argument "
            "than I would have produced individually."
        ),
    },
    {
        "code":      "LO3",
        "construct": "Learning_Outcomes",
        "statement": (
            "After this session, I feel better equipped to evaluate AI adoption "
            "decisions in a professional context."
        ),
    },
]

_ATTENTION_ITEM = {
    "code":      "AC1",
    "construct": "Attention_Check",
    "statement": "To confirm you are reading carefully, please select the number 5.",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _likert_value(label: str | None) -> int | None:
    """Convert '5 — Neutral' → 5."""
    if label is None:
        return None
    try:
        return int(label.split("—")[0].strip().split()[0])
    except (ValueError, IndexError):
        return None


def _mean(values: list[int | None]) -> float | None:
    clean = [v for v in values if v is not None]
    return round(sum(clean) / len(clean), 2) if clean else None


def _item_record(item: dict, raw_label: str | None) -> dict:
    return {
        "construct":      item["construct"],
        "code":           item["code"],
        "statement":      item["statement"],
        "response_label": raw_label,
        "response_value": _likert_value(raw_label),
    }


def _attention_insert_pos(member: str, n_items: int) -> int:
    """Stable per-member insertion position for the attention check."""
    return sum(ord(c) for c in member) % max(n_items - 1, 1) + 1


def _save_feedback(code: str, member: str, payload: dict) -> None:
    """Write responses to session JSON and to a standalone file."""
    gd = _load_session(code)
    if gd is not None:
        gd.setdefault("feedback_responses", {})[member] = payload
        _save_session(gd)

    slug  = member.lower().replace(" ", "_")
    ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = FEEDBACK_DIR / f"feedback_{code}_{slug}_{ts}.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(
            {
                "group_code":  code,
                "participant": member,
                "submitted_at": datetime.now().isoformat(),
                **payload,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )


# ── Page view ─────────────────────────────────────────────────────────────────

def page_feedback():
    code   = st.session_state.get("group_code", "")
    member = st.session_state.get("member", "")

    gd = _load_session(code)
    if not gd:
        st.session_state["page"] = "welcome"
        st.rerun()

    # ── Already submitted ─────────────────────────────────────────────────────
    if gd.get("feedback_responses", {}).get(member):
        st.markdown(
            '<div class="card-blue" style="text-align:center">'
            '<div style="font-size:2.5rem;margin-bottom:8px">✅</div>'
            '<h2 style="margin:0 0 6px;color:white !important">Feedback Submitted</h2>'
            '<p style="margin:0;opacity:0.85;color:white !important">'
            'Thank you — your responses have been recorded and will help us improve '
            'the AI tutoring system.</p></div>',
            unsafe_allow_html=True,
        )
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("↩ Back to summary", use_container_width=True):
                st.session_state["page"] = "done"
                st.rerun()
        with col_b:
            if st.button("↩ Start a new session", use_container_width=True):
                for k in ["member", "group_code", "page"]:
                    st.session_state.pop(k, None)
                st.rerun()
        return

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="card-blue">'
        '<h2 style="margin:0 0 6px;color:white !important">📝 AI Agent Feedback</h2>'
        '<p style="margin:0;opacity:0.9;color:white !important">'
        'Help us improve the AI tutoring system. Rate each statement honestly — '
        'your responses are confidential and used only to refine the agent. '
        'This takes about 3–4 minutes.'
        '</p></div>',
        unsafe_allow_html=True,
    )

    # Stable attention-check insertion position for this member
    _as_insert_pos = _attention_insert_pos(member, len(AI_SCAFFOLDING_ITEMS))
    as_items_with_attn = (
        AI_SCAFFOLDING_ITEMS[:_as_insert_pos]
        + [_ATTENTION_ITEM]
        + AI_SCAFFOLDING_ITEMS[_as_insert_pos:]
    )

    with st.form("feedback_form"):

        # ── Section A: AI Scaffolding Quality ────────────────────────────────
        st.markdown(
            '<div style="background:#E8F0FE;border-radius:10px;padding:14px 18px;'
            'margin-bottom:20px">'
            '<strong style="color:#003C87;font-size:1rem">'
            'Section A — AI Scaffolding Quality</strong><br>'
            '<span style="font-size:0.83rem;color:#555">'
            'Rate each statement from 1 (strongly disagree) to 9 (strongly agree).'
            '</span></div>',
            unsafe_allow_html=True,
        )

        as_raw: dict[str, str | None] = {}
        for item in as_items_with_attn:
            if item["construct"] == "Attention_Check":
                st.markdown(
                    '<div style="background:#FFF8E7;border-left:3px solid #F39C12;'
                    'border-radius:0 8px 8px 0;padding:8px 14px;margin:8px 0 4px;'
                    'font-size:0.87rem;color:#5D4037">'
                    f'<em>{_ATTENTION_ITEM["statement"]}</em>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                as_raw["AC1"] = st.radio(
                    _ATTENTION_ITEM["statement"],
                    options=_LIKERT_9,
                    index=None,
                    key="item_AC1",
                    label_visibility="collapsed",
                    horizontal=True,
                )
                st.markdown("")
            else:
                st.markdown(f"**{item['code']}. {item['statement']}**")
                as_raw[item["code"]] = st.radio(
                    item["statement"],
                    options=_LIKERT_9,
                    index=None,
                    key=f"item_{item['code']}",
                    label_visibility="collapsed",
                    horizontal=True,
                )
                st.markdown("")

        # ── Section B: Group Collaboration ───────────────────────────────────
        st.markdown(
            '<div style="background:#E8F0FE;border-radius:10px;padding:14px 18px;'
            'margin:24px 0 20px">'
            '<strong style="color:#003C87;font-size:1rem">'
            'Section B — Group Collaboration</strong><br>'
            '<span style="font-size:0.83rem;color:#555">'
            'Rate each statement from 1 (strongly disagree) to 9 (strongly agree).'
            '</span></div>',
            unsafe_allow_html=True,
        )

        gc_raw: dict[str, str | None] = {}
        for item in GROUP_COLLAB_ITEMS:
            st.markdown(f"**{item['code']}. {item['statement']}**")
            gc_raw[item["code"]] = st.radio(
                item["statement"],
                options=_LIKERT_9,
                index=None,
                key=f"item_{item['code']}",
                label_visibility="collapsed",
                horizontal=True,
            )
            st.markdown("")

        # ── Section C: Learning Outcomes ─────────────────────────────────────
        st.markdown(
            '<div style="background:#E8F0FE;border-radius:10px;padding:14px 18px;'
            'margin:24px 0 20px">'
            '<strong style="color:#003C87;font-size:1rem">'
            'Section C — Learning Outcomes</strong><br>'
            '<span style="font-size:0.83rem;color:#555">'
            'Rate each statement from 1 (strongly disagree) to 9 (strongly agree).'
            '</span></div>',
            unsafe_allow_html=True,
        )

        lo_raw: dict[str, str | None] = {}
        for item in LEARNING_OUTCOME_ITEMS:
            st.markdown(f"**{item['code']}. {item['statement']}**")
            lo_raw[item["code"]] = st.radio(
                item["statement"],
                options=_LIKERT_9,
                index=None,
                key=f"item_{item['code']}",
                label_visibility="collapsed",
                horizontal=True,
            )
            st.markdown("")

        # ── Section D: Agent Perception ──────────────────────────────────────
        st.markdown(
            '<div style="background:#E8F0FE;border-radius:10px;padding:14px 18px;'
            'margin:24px 0 20px">'
            '<strong style="color:#003C87;font-size:1rem">'
            'Section D — AI Agent Perception</strong>'
            '</div>',
            unsafe_allow_html=True,
        )

        agent_diff = st.radio(
            "During the session, were you able to distinguish between the AI feedback "
            "on your individual submission and the Group Alignment Agent's group-level report?",
            options=_AGENT_DIFF_OPTIONS,
            index=None,
            key="agent_diff",
        )
        agent_diff_comment = st.text_area(
            "Optional — any comments on the AI components?",
            placeholder=(
                "e.g. 'The individual feedback felt more personal; "
                "the group report was more analytical.'"
            ),
            key="agent_diff_comment",
            height=80,
        )

        # ── Section E: Overall Impressions ───────────────────────────────────
        st.markdown(
            '<div style="background:#E8F0FE;border-radius:10px;padding:14px 18px;'
            'margin:24px 0 20px">'
            '<strong style="color:#003C87;font-size:1rem">'
            'Section E — Overall Impressions</strong>'
            '</div>',
            unsafe_allow_html=True,
        )

        overall_rating = st.radio(
            "Overall, how would you rate the Case Study Tutor experience?",
            options=_OVERALL_OPTIONS,
            index=None,
            key="overall_rating",
            horizontal=True,
        )

        best_aspect = st.text_area(
            "What aspect of the AI scaffolding was most valuable to you?",
            placeholder=(
                "e.g. 'The synthesis coaching note helped me see how the sections fit together.'"
            ),
            key="best_aspect",
            height=100,
        )
        improvement = st.text_area(
            "What would you change or improve about the AI feedback?",
            placeholder=(
                "e.g. 'The individual feedback could reference specific lines from my submission.'"
            ),
            key="improvement",
            height=100,
        )
        other_comments = st.text_area(
            "Any other comments? (optional)",
            key="other_comments",
            height=80,
        )

        st.markdown("---")
        submitted = st.form_submit_button(
            "Submit Feedback →",
            use_container_width=True,
            type="primary",
        )

        if submitted:
            # ── Validation ───────────────────────────────────────────────────
            missing: list[str] = []
            for item in AI_SCAFFOLDING_ITEMS:
                if as_raw.get(item["code"]) is None:
                    missing.append(item["code"])
            for item in GROUP_COLLAB_ITEMS:
                if gc_raw.get(item["code"]) is None:
                    missing.append(item["code"])
            for item in LEARNING_OUTCOME_ITEMS:
                if lo_raw.get(item["code"]) is None:
                    missing.append(item["code"])
            if agent_diff is None:
                missing.append("Section D")
            if overall_rating is None:
                missing.append("Overall rating")

            if missing:
                st.error(
                    f"Please answer all required questions. Missing: {', '.join(missing)}"
                )
            else:
                # ── Build payload ─────────────────────────────────────────
                attn_label = as_raw.get("AC1")
                attn_pass  = _likert_value(attn_label) == 5

                payload = {
                    "ai_scaffolding": {
                        "items": {
                            i["code"]: _item_record(i, as_raw.get(i["code"]))
                            for i in AI_SCAFFOLDING_ITEMS
                        },
                        "mean_score": _mean(
                            [_likert_value(as_raw.get(i["code"])) for i in AI_SCAFFOLDING_ITEMS]
                        ),
                    },
                    "group_collaboration": {
                        "items": {
                            i["code"]: _item_record(i, gc_raw.get(i["code"]))
                            for i in GROUP_COLLAB_ITEMS
                        },
                        "mean_score": _mean(
                            [_likert_value(gc_raw.get(i["code"])) for i in GROUP_COLLAB_ITEMS]
                        ),
                    },
                    "learning_outcomes": {
                        "items": {
                            i["code"]: _item_record(i, lo_raw.get(i["code"]))
                            for i in LEARNING_OUTCOME_ITEMS
                        },
                        "mean_score": _mean(
                            [_likert_value(lo_raw.get(i["code"])) for i in LEARNING_OUTCOME_ITEMS]
                        ),
                    },
                    "attention_check": {
                        "response_label":   attn_label,
                        "response_value":   _likert_value(attn_label),
                        "passed":           attn_pass,
                        "inserted_at_pos":  _as_insert_pos,
                    },
                    "agent_differentiation": {
                        "response":  agent_diff,
                        "comment":   agent_diff_comment.strip(),
                    },
                    "overall": {
                        "rating_label": overall_rating,
                        "rating_value": _likert_value(overall_rating),
                        "best_aspect":  best_aspect.strip(),
                        "improvement":  improvement.strip(),
                        "other":        other_comments.strip(),
                    },
                    "metadata": {
                        "submitted_at":           datetime.now().isoformat(),
                        "participant":            member,
                        "group_code":             code,
                        "attention_check_passed": attn_pass,
                    },
                }

                _save_feedback(code, member, payload)
                st.rerun()
