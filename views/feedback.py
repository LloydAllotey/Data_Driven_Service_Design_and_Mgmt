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

# Single-digit labels so all 9 columns are equal width (no skewed layout).
# Anchors are shown separately as a legend above each item.
_LIKERT_9 = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]

_LIKERT_LEGEND = (
    '<div style="display:flex;justify-content:space-between;'
    'font-size:0.75rem;color:#555;margin:-6px 0 10px;padding:0 4px">'
    '<span>1 — Strongly disagree</span>'
    '<span>5 — Neutral</span>'
    '<span>9 — Strongly agree</span>'
    '</div>'
)

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

# Two attention checks — rendered as plain Likert items, no special styling.
# AC1 is inserted at index 3 in Section A (after AS1, AS2, AS3).
# AC2 is inserted at index 1 in Section C (after LO1).
_ATTENTION_ITEM_1 = {
    "code":           "AC1",
    "construct":      "Attention_Check",
    "correct_value":  5,
    "statement":      "For this item, please select the number 5.",
}
_ATTENTION_ITEM_2 = {
    "code":           "AC2",
    "construct":      "Attention_Check",
    "correct_value":  9,
    "statement":      "For this item, please select the number 9.",
}

# Build Section A and C item sequences with attention checks spliced in
_AS_ITEMS_ORDERED = (
    AI_SCAFFOLDING_ITEMS[:3]
    + [_ATTENTION_ITEM_1]
    + AI_SCAFFOLDING_ITEMS[3:]
)
_LO_ITEMS_ORDERED = (
    LEARNING_OUTCOME_ITEMS[:1]
    + [_ATTENTION_ITEM_2]
    + LEARNING_OUTCOME_ITEMS[1:]
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _likert_value(label: str | None) -> int | None:
    """Convert '5' or '5 — Neutral' → 5."""
    if label is None:
        return None
    try:
        return int(label.split("—")[0].strip().split()[0])
    except (ValueError, IndexError):
        return None


def _likert_radio(statement: str, key: str) -> str | None:
    """Render a plain Likert item (statement + evenly-spaced 1-9 radio)."""
    st.markdown(f"**{statement}**")
    val = st.radio(
        statement,
        options=_LIKERT_9,
        index=None,
        key=key,
        label_visibility="collapsed",
        horizontal=True,
    )
    st.markdown("")
    return val


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


def _save_feedback(code: str, member: str, payload: dict, both_passed: bool) -> None:
    """Always persist to session JSON; write standalone file only when both attention checks pass."""
    gd = _load_session(code)
    if gd is not None:
        gd.setdefault("feedback_responses", {})[member] = payload
        _save_session(gd)

    if both_passed:
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

    # ── Force radio option labels to dark text (overrides global white CSS) ──
    st.markdown("""
<style>
/* Radio option labels inside the feedback form */
div[role="radiogroup"] label,
div[role="radiogroup"] label p,
div[role="radiogroup"] span[data-testid="stMarkdownContainer"] p {
    color: #2C3E50 !important;
}
</style>
""", unsafe_allow_html=True)

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
        for item in _AS_ITEMS_ORDERED:
            as_raw[item["code"]] = _likert_radio(
                item["statement"] if item["construct"] == "Attention_Check"
                else f"{item['code']}. {item['statement']}",
                f"item_{item['code']}",
            )

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
            gc_raw[item["code"]] = _likert_radio(
                f"{item['code']}. {item['statement']}",
                f"item_{item['code']}",
            )

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
        for item in _LO_ITEMS_ORDERED:
            lo_raw[item["code"]] = _likert_radio(
                item["statement"] if item["construct"] == "Attention_Check"
                else f"{item['code']}. {item['statement']}",
                f"item_{item['code']}",
            )

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
            # ── Completeness check (attention check items are required too) ──
            missing: list[str] = []
            for item in _AS_ITEMS_ORDERED:
                if as_raw.get(item["code"]) is None:
                    missing.append(item["code"])
            for item in GROUP_COLLAB_ITEMS:
                if gc_raw.get(item["code"]) is None:
                    missing.append(item["code"])
            for item in _LO_ITEMS_ORDERED:
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
                # ── Attention check evaluation ────────────────────────────
                ac1_val      = _likert_value(as_raw.get("AC1"))
                ac2_val      = _likert_value(lo_raw.get("AC2"))
                ac1_pass     = ac1_val == _ATTENTION_ITEM_1["correct_value"]
                ac2_pass     = ac2_val == _ATTENTION_ITEM_2["correct_value"]
                both_passed  = ac1_pass and ac2_pass

                # ── Build payload ─────────────────────────────────────────
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
                    "attention_checks": {
                        "AC1": {
                            "response_value": ac1_val,
                            "correct_value":  _ATTENTION_ITEM_1["correct_value"],
                            "passed":         ac1_pass,
                        },
                        "AC2": {
                            "response_value": ac2_val,
                            "correct_value":  _ATTENTION_ITEM_2["correct_value"],
                            "passed":         ac2_pass,
                        },
                        "both_passed": both_passed,
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
                        "submitted_at":        datetime.now().isoformat(),
                        "participant":         member,
                        "group_code":          code,
                        "attention_checks_passed": both_passed,
                    },
                }

                _save_feedback(code, member, payload, both_passed)
                st.rerun()
