"""
views/alignment.py — Group alignment report page.
"""
from __future__ import annotations

from datetime import datetime

import streamlit as st

from core.case_content import get_section_by_id
from database.storage import _load_session, _save_session
from components.sidebar import _render_sidebar, _render_step_indicator
from core.workflow import _all_submitted, _compute_contribution_scores, _get_agent, _trigger_ai_content_scoring


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

    # Run / load alignment reports
    reports = gd.get("alignment_reports", [])
    if not reports:
        with st.spinner("Running Group Alignment Agent… this takes ~15 seconds"):
            agent = _get_agent()
            if agent:
                try:
                    # Use our contribution scoring system for free-rider detection
                    c_scores_init = _compute_contribution_scores(gd)
                    scores_list   = [c_scores_init[m]["total"] for m in members]
                    low_effort    = [m for m in members if c_scores_init[m].get("effort", 0) < 10]
                    missing       = [m for m in members if m not in submissions]
                    has_issue     = bool(missing or low_effort)

                    if has_issue:
                        parts = []
                        if missing:
                            parts.append(f"{', '.join(missing)} has not submitted yet.")
                        if low_effort:
                            parts.append(f"{', '.join(low_effort)} submitted but with low effort relative to the group median.")
                        group_message = " ".join(parts) + " Consider discussing contribution balance before moving to synthesis."
                    else:
                        group_message = ""

                    sub_texts  = {m: submissions[m]["text"] for m in submissions}
                    sec_titles = {
                        m: get_section_by_id(assignments.get(m, [1])[0])["title"]
                        for m in submissions
                        if assignments.get(m)
                    }
                    frag_report = agent.analyze_fragmentation(sub_texts, sec_titles)

                    report = {
                        "timestamp": datetime.now().isoformat(),
                        "free_rider": {
                            "has_issue":     has_issue,
                            "missing":       missing,
                            "low_effort":    low_effort,
                            "group_message": group_message,
                        },
                        "fragmentation": {
                            "score":               frag_report.integration_score,
                            "has_gaps":            frag_report.has_gaps,
                            "scaffold_questions":  frag_report.scaffold_questions,
                            "missing_connections": frag_report.missing_connections,
                            "contradictions":      frag_report.contradictions,
                            "summary_html":        frag_report.summary_html,
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

    # Contribution Balance panel
    c_scores  = _compute_contribution_scores(gd)
    group_avg = round(sum(c_scores[m]["total"] for m in members) / max(len(members), 1))

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 📊 Contribution Balance")

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

        submitted_count = sum(1 for m in members if c_scores.get(m, {}).get("total", 0) > 0)
        engaged_count   = sum(1 for m in members if c_scores.get(m, {}).get("engagement", 0) > 0)
        scores_list     = [c_scores.get(m, {}).get("total", 0) for m in members]
        max_score       = max(scores_list) if scores_list else 0
        heavy_reliance  = max_score > 0 and (max_score - min(scores_list)) >= 35

        if submitted_count == len(members):
            contrib_msg = "All members have submitted — well done!"
        elif submitted_count == 0:
            contrib_msg = "No submissions yet."
        else:
            missing_n   = len(members) - submitted_count
            contrib_msg = f"{submitted_count} of {len(members)} members have submitted; {missing_n} still missing."

        reliance_msg = (
            "⚠️ The group is relying heavily on one or two members — consider redistributing effort before synthesis."
            if heavy_reliance else
            "Contribution is reasonably balanced across the group."
        )

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
            sec    = get_section_by_id(sec_id)

            comp_html = "".join([
                f'<span style="font-size:0.72rem;background:#E8F0FE;color:#003C87;'
                f'border-radius:4px;padding:1px 6px;margin-right:3px">'
                f'{k}: {v}</span>'
                for k, v in [
                    ("C",   cs.get("completion", 0)),
                    ("E",   cs.get("effort",     0)),
                    ("Su",  cs.get("substance",  0)),
                    ("Eng", cs.get("engagement", 0)),
                    ("Sy",  cs.get("synthesis",  0)),
                ]
            ])

            st.markdown(
                f'<div style="margin-bottom:14px">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px">'
                f'<span style="font-weight:600;font-size:0.88rem">{m}{you}</span>'
                f'<span style="font-weight:700;color:{col};font-size:0.9rem">{tot}/100 — {lbl}</span>'
                f'</div>'
                f'<div style="font-size:0.75rem;color:#888;margin-bottom:4px">'
                f'{sec["emoji"]} {sec["title"]} · {cs.get("word_count",0)} words (group median: {cs.get("median_wc",0)})'
                f'</div>'
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

        score   = frag.get("score", 0)
        bar_c   = "#27AE60" if score >= 70 else "#F39C12" if score >= 40 else "#E74C3C"
        label   = "Well integrated" if score >= 70 else "Partially integrated" if score >= 40 else "Fragmented"

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

    # Scaffold questions
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

    # All submissions viewer
    with st.expander("📄 Read all group submissions"):
        for m in members:
            sub    = submissions.get(m, {})
            sec_id = assignments.get(m, [1])[0]
            sec    = get_section_by_id(sec_id)
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
