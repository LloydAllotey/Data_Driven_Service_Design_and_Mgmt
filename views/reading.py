"""
views/reading.py — Case reading page.
"""
from __future__ import annotations

import streamlit as st

from core.case_content import SECTIONS, get_section_by_id
from database.storage import _load_session, _save_session
from components.sidebar import _render_sidebar, _render_step_indicator
from core.workflow import _member_sections


def page_reading():
    gd = _load_session(st.session_state["group_code"])
    if not gd:
        st.session_state["page"] = "welcome"
        st.rerun()

    member = st.session_state["member"]
    _render_sidebar(gd, member)
    _render_step_indicator(2)

    sec_ids  = _member_sections(gd, member)
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
            gd["phase"] = "working"
            _save_session(gd)
            st.session_state["page"] = "working"
            st.rerun()
