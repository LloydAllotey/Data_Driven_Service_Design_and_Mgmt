"""
components/sidebar.py — Sidebar, step indicator, and score donut chart.
"""

from __future__ import annotations

from datetime import datetime

import streamlit as st

try:
    from streamlit_autorefresh import st_autorefresh
    _AUTOREFRESH_AVAILABLE = True
except ImportError:
    _AUTOREFRESH_AVAILABLE = False


from core.workflow import _compute_contribution_scores, _post_message
from core.case_content import get_section_by_id


# ── Step indicator ────────────────────────────────────────────────────────────

def _render_step_indicator(current: int) -> None:
    steps = ["Setup", "Read", "Analyse", "Group Review", "Synthesis"]
    parts = []
    for i, label in enumerate(steps, 1):
        if i < current:
            cls = "step-done"
            icon = "\u2713"
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


# ── Score donut ───────────────────────────────────────────────────────────────

def _render_score_donut(my_score: dict) -> None:
    """
    Render a donut chart breaking down the contribution score.
    Uses plotly when available; falls back to a pure CSS/HTML conic-gradient chart.
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

    # CSS conic-gradient donut
    stops = []
    cursor = 0
    for _, val, col in components:
        if val > 0:
            stops.append(f"{col} {cursor}% {cursor + val}%")
            cursor += val
    if missed > 0:
        stops.append(f"#ECEFF1 {cursor}% 100%")
    gradient = ", ".join(stops) if stops else "#ECEFF1 0% 100%"

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
  <div style="position:relative;width:155px;height:155px;flex-shrink:0">
    <div style="
      width:155px;height:155px;border-radius:50%;
      background:conic-gradient({gradient});
    "></div>
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
  <div style="min-width:140px">
    {legend_rows}
  </div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────

def _render_sidebar(group_data: dict, current_member: str) -> None:
    with st.sidebar:
        st.markdown("### \U0001f4da Case Study Tutor")
        st.markdown("---")

        code = group_data["group_code"]
        st.markdown("**Group Code**")
        st.markdown(f'<div class="group-code">{code}</div>', unsafe_allow_html=True)
        st.caption("Share this code with your group members")
        st.markdown("---")

        members     = group_data.get("members", [])
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
                    dot, status = "dot-green", f"{wc} words \u2713"
            else:
                dot, status = "dot-grey", "not submitted"

            you = " (you)" if m == current_member else ""
            sec_ids = assignments.get(m, [])
            sec_labels = ", ".join(
                get_section_by_id(sid)["emoji"] + " \u00a7" + str(sid)
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

        # Deadlines
        int_dl = group_data.get("internal_deadline")
        ext_dl = group_data.get("external_deadline")
        if int_dl or ext_dl:
            st.markdown("---")
            st.markdown("**\u23f0 Deadlines**")
            if int_dl:
                d = datetime.fromisoformat(int_dl)
                past = datetime.now() > d
                flag = " \u26a0\ufe0f" if past else ""
                st.markdown(
                    f'<div style="font-size:0.82rem;color:{"#E74C3C" if past else "#2C3E50"}">'
                    f'\U0001f4dd Individual submission: <strong>{d.strftime("%d %b %Y")}</strong>{flag}</div>',
                    unsafe_allow_html=True,
                )
            if ext_dl:
                d = datetime.fromisoformat(ext_dl)
                past = datetime.now() > d
                flag = " \u26a0\ufe0f" if past else ""
                st.markdown(
                    f'<div style="font-size:0.82rem;color:{"#E74C3C" if past else "#2C3E50"}">'
                    f'\U0001f3c1 Final submission: <strong>{d.strftime("%d %b %Y")}</strong>{flag}</div>',
                    unsafe_allow_html=True,
                )

        # Live contribution scores
        c_scores = _compute_contribution_scores(group_data)
        if any(c_scores[m]["total"] > 0 for m in c_scores):
            st.markdown("---")
            st.markdown("**\U0001f4ca Contribution Balance**")
            for m in members:
                cs     = c_scores.get(m, {})
                total  = cs.get("total", 0)
                colour = cs.get("colour", "#BDC3C7")
                lbl    = cs.get("label", "\u2014")
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
            "lobby":         "\u23f3 Waiting for members",
            "reading_ready": "\U0001f4d6 Ready to read",
            "waiting":       "\u23f3 Waiting for members",
            "reading":       "\U0001f4d6 Reading case",
            "working":       "\u270d\ufe0f Analysing",
            "aligning":      "\U0001f916 Group alignment",
            "synthesis":     "\U0001f517 Synthesis round",
            "done":          "\u2705 Complete",
        }
        st.markdown(f"**Phase:** {phase_labels.get(phase, phase)}")

        if st.button("\U0001f504 Refresh", use_container_width=True):
            st.rerun()

        # Group chat
        st.markdown("---")

        if _AUTOREFRESH_AVAILABLE:
            st_autorefresh(interval=8_000, key="chat_refresh")

        messages = group_data.get("chat", [])
        unread_key = f"chat_seen_{code}"
        seen   = st.session_state.get(unread_key, 0)
        unread = len(messages) - seen
        badge  = f" \U0001f534 {unread}" if unread > 0 else ""
        st.markdown(f"**\U0001f4ac Group Chat{badge}**")

        if messages:
            bubbles = []
            for msg in messages[-30:]:
                is_me = msg["member"] == current_member
                wrap  = "chat-bubble-wrap-me"    if is_me else "chat-bubble-wrap-other"
                bub   = "chat-bubble chat-bubble-me" if is_me else "chat-bubble chat-bubble-other"
                meta  = "chat-meta-me"           if is_me else "chat-meta-other"
                name  = "You" if is_me else msg["member"]
                bubbles.append(
                    f'<div class="{wrap}">'
                    f'  <div>'
                    f'    <div class="{bub}">{msg["text"]}</div>'
                    f'    <div class="{meta}">{name} \u00b7 {msg["ts"]}</div>'
                    f'  </div>'
                    f'</div>'
                )
            st.markdown(
                f'<div class="chat-feed">{"".join(bubbles)}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="chat-empty">No messages yet.<br>Say hi to your group! \U0001f44b</div>',
                unsafe_allow_html=True,
            )

        st.session_state[unread_key] = len(messages)

        if "chat_input_n" not in st.session_state:
            st.session_state["chat_input_n"] = 0
        msg_key = f"chat_input_{st.session_state['chat_input_n']}"
        new_msg = st.text_input(
            "Message",
            placeholder="Type a message\u2026",
            label_visibility="collapsed",
            key=msg_key,
        )
        if st.button("Send \u2192", use_container_width=True, key="chat_send"):
            if new_msg.strip():
                _post_message(code, current_member, new_msg.strip())
                st.session_state["chat_input_n"] += 1
                st.rerun()
