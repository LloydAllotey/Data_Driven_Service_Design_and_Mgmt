"""
views/synthesis.py — Group synthesis writing page.
"""
from __future__ import annotations

import streamlit as st

from core.case_content import GROUP_SYNTHESIS_QUESTIONS, get_section_by_id
from database.storage import _load_session, _save_session
from components.peer_comments import render_peer_comments_block
from components.sidebar import _render_sidebar, _render_step_indicator
from core.workflow import _get_agent, _submit_synthesis


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

    q_idx      = len(gd.get("alignment_reports", [])) % len(GROUP_SYNTHESIS_QUESTIONS)
    synthesis_q = GROUP_SYNTHESIS_QUESTIONS[q_idx]

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### The Group Synthesis Question")
    st.info(synthesis_q)

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

    code = st.session_state["group_code"]
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 💬 Peer comments on your first-phase analysis")
    st.markdown(
        '<div style="font-size:0.88rem;color:#555;margin-bottom:10px">'
        "Before you write your synthesis, review what colleagues wrote about your individual draft. "
        "Use the sidebar group chat if you want to follow up.</div>",
        unsafe_allow_html=True,
    )
    render_peer_comments_block(
        gd, code, member, member, show_composer=False,
    )
    st.markdown("</div>", unsafe_allow_html=True)

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
        members    = gd.get("members", [])
        for m in members:
            s     = synth_subs.get(m)
            icon  = "✅" if s else "⏳"
            you   = " (you)" if m == member else ""
            wc    = len(s["text"].split()) if s else 0
            wc_str = f" · {wc} words" if wc else ""
            st.markdown(f"{icon} **{m}**{you}{wc_str}")

        if len(synth_subs) == len(members):
            st.success("All members have submitted their synthesis!")
            if st.button("View Final Summary →", type="primary", use_container_width=True):
                st.session_state["page"] = "done"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("📚 Quick reference — all individual submissions"):
        assignments = gd.get("section_assignments", {})
        all_subs    = gd.get("submissions", {})
        for m in gd.get("members", []):
            sub    = all_subs.get(m, {})
            sec_id = assignments.get(m, [1])[0]
            sec    = get_section_by_id(sec_id)
            st.markdown(
                f'**{sec["emoji"]} {m} — {sec["title"]}**\n\n'
                f'{sub.get("text","(no submission)")}\n\n---'
            )
