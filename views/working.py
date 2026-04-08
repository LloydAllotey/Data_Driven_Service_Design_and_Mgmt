"""
views/working.py — Individual analysis writing page.
"""
from __future__ import annotations

import streamlit as st

from core.case_content import EXPERT_ANSWERS, SECTION_CONNECTIONS, SECTIONS, get_section_by_id
from database.storage import _load_session, _save_session
from components.sidebar import _render_sidebar, _render_step_indicator
from core.workflow import _get_agent, _member_sections, _submit_answer


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

    st.markdown(
        f'<div class="card-blue">'
        f'<div class="section-pill">Section {primary_sec["id"]} of 5</div>'
        f'<h2 style="margin:4px 0 6px;color:white !important">{primary_sec["emoji"]} {primary_sec["title"]}</h2>'
        f'<p style="margin:0;opacity:0.9;color:white !important">{primary_sec["question"]}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    tab_write, tab_case, tab_full = st.tabs([
        "✍️ Write your analysis",
        "📖 Read your section",
        "📚 Read full case",
    ])

    with tab_case:
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

            # Cross-section connections
            my_sid    = primary_sec["id"]
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
                member_assignments = gd.get("section_assignments", {})
                sid_to_member = {}
                for m, sids in member_assignments.items():
                    for sid in sids:
                        sid_to_member[sid] = m

                for other in other_secs:
                    oid  = other["id"]
                    fwd  = SECTION_CONNECTIONS.get((my_sid, oid))
                    bwd  = SECTION_CONNECTIONS.get((oid, my_sid))
                    colleague = sid_to_member.get(oid, "a colleague")
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:10px;margin:14px 0 6px">'
                        f'<span style="font-size:1.3rem">{other["emoji"]}</span>'
                        f'<strong style="color:#003C87">§{oid}: {other["title"]}</strong>'
                        f'<span style="font-size:0.78rem;color:#888;margin-left:4px">— {colleague}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    if fwd:
                        _, bridge_q = fwd
                        st.markdown(
                            f'<div style="background:#EEF5FF;border-left:3px solid #4F8EF7;'
                            f'border-radius:0 8px 8px 0;padding:10px 14px;font-size:0.85rem;margin-bottom:6px">'
                            f'<span style="color:#003C87;font-weight:600">→ Your section feeds into §{oid}</span>'
                            f'<br><span style="color:#333">{bridge_q}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    if bwd:
                        _, bridge_q = bwd
                        st.markdown(
                            f'<div style="background:#F0FFF4;border-left:3px solid #27AE60;'
                            f'border-radius:0 8px 8px 0;padding:10px 14px;font-size:0.85rem;margin-bottom:6px">'
                            f'<span style="color:#1A7A3C;font-weight:600">← §{oid} feeds into your section</span>'
                            f'<br><span style="color:#333">{bridge_q}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

            already_submitted = bool(my_sub)

            if not already_submitted:
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

            members     = gd.get("members", [])
            subs        = gd.get("submissions", {})
            submitted_n = len(subs)
            total_n     = len(members)

            pct         = int(submitted_n / max(total_n, 1) * 100)
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
                    wc   = sub.get("word_count", 0)
                    icon = "🟡" if wc < 40 else "🟢"
                    lbl  = f"{wc} words"
                else:
                    icon = "⚪"
                    lbl  = "pending"
                you = " **(you)**" if m == member else ""
                st.markdown(f"{icon} **{m}**{you} — {lbl}")

            if submitted_n == total_n:
                st.success("All members submitted! Move to Group Alignment →")
                if st.button("Go to Group Alignment →", type="primary", use_container_width=True):
                    st.session_state["page"] = "alignment"
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
