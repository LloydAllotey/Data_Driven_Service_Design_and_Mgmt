"""
views/lobby.py — Waiting room shown after joining until the group is full.
"""
from __future__ import annotations

import streamlit as st

from core.case_content import BUZZ_WORDS
from database.storage import _load_session
from components.sidebar import _render_step_indicator


def page_lobby():
    gd = _load_session(st.session_state["group_code"])
    if not gd:
        st.session_state["page"] = "welcome"
        st.rerun()

    member   = st.session_state["member"]
    members  = gd.get("members", [])
    expected = gd.get("expected_size", 5)
    phase    = gd.get("phase", "lobby")
    prefs    = gd.get("preferences", {})

    slug_to_label = {b["slug"]: f"{b['emoji']} {b['label']}" for b in BUZZ_WORDS}

    _render_step_indicator(1)

    # Auto-advance if group is already full
    if phase == "reading_ready":
        st.session_state["page"] = "reading"
        st.rerun()

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
        st.markdown(f'<div class="group-code">{code}</div>', unsafe_allow_html=True)
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
