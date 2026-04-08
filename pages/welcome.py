"""
pages/welcome.py — Welcome / login page.
"""
from __future__ import annotations

from datetime import datetime

import streamlit as st

from core.case_content import BUZZ_WORDS
from core.workflow import _create_group, _join_group


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

        bw_options  = [f"{b['emoji']} {b['label']}" for b in BUZZ_WORDS]
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
                        prefs  = [bw_slug_map[b] for b in selected_bw]
                        int_dl = datetime(internal_date.year, internal_date.month, internal_date.day, 23, 59).isoformat() if internal_date else None
                        ext_dl = datetime(external_date.year, external_date.month, external_date.day, 23, 59).isoformat() if external_date else None
                        gd = _create_group(name.strip(), size, prefs, int_dl, ext_dl)
                        st.session_state["member"]     = name.strip()
                        st.session_state["group_code"] = gd["group_code"]
                        st.session_state["page"]       = "lobby"
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
                            st.session_state["member"]     = name.strip()
                            st.session_state["group_code"] = code.strip()
                            st.session_state["page"]       = "lobby"
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
