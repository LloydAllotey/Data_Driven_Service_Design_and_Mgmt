"""
views/summary.py — Session summary / contribution report page.
"""
from __future__ import annotations

import streamlit as st

from database.storage import _load_session
from components.sidebar import _render_score_donut, _render_sidebar
from core.workflow import _compute_contribution_scores, _trigger_ai_content_scoring


def page_summary():
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

    # AI content scoring (runs once; cached in session)
    code              = st.session_state["group_code"]
    all_synth_done    = len(gd.get("synthesis_submissions", {})) >= len(members)
    ai_already_scored = bool(gd.get("ai_content_scores"))

    if all_synth_done and not ai_already_scored:
        with st.spinner("✨ AI is evaluating submission quality — this takes ~20 seconds…"):
            gd = _trigger_ai_content_scoring(code, gd)
        st.rerun()

    # Group-level contribution narrative
    st.markdown("---")
    c_scores  = _compute_contribution_scores(gd)
    group_avg = round(sum(c_scores[m]["total"] for m in members) / max(len(members), 1))

    scores_list    = [c_scores[m]["total"] for m in members]
    engaged_count  = sum(1 for m in members if c_scores[m].get("engagement", 0) > 0)
    heavy_reliance = (max(scores_list) - min(scores_list)) >= 35 if scores_list else False

    reliance_msg = (
        "⚠️ The group relied heavily on one or two members."
        if heavy_reliance else
        "Contribution was reasonably balanced across the group."
    )

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

    # Personal contribution report card
    st.markdown("### 📊 Your Contribution Report")
    my_score = c_scores.get(member, {})

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
            s     = comp["score"]
            m_val = comp["max"]
            pct   = int(s / m_val * 100)
            c     = "#27AE60" if pct >= 80 else "#F39C12" if pct >= 50 else "#E74C3C"
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

    if reports:
        with st.expander("🤖 Group Alignment Agent Report"):
            latest = reports[-1]
            frag   = latest.get("fragmentation", {})
            st.markdown(f"**Integration score:** {frag.get('score', 0)}/100")
            st.markdown("**Scaffold questions posed:**")
            for q in frag.get("scaffold_questions", []):
                st.markdown(f"- {q}")

    st.markdown("---")
    if st.button("↩ Start a new session", use_container_width=False):
        for key in ["member", "group_code", "page"]:
            st.session_state.pop(key, None)
        st.rerun()
