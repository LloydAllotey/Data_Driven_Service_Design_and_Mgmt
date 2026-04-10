"""
components/peer_comments.py — Peer comments on first-phase (individual) submissions.
"""

from __future__ import annotations

import html

import streamlit as st

from core.workflow import _post_submission_peer_comment


def render_peer_comments_block(
    gd: dict,
    group_code: str,
    viewer: str,
    target: str,
    *,
    show_composer: bool,
) -> None:
    """List comments left on *target*'s submission; optionally let *viewer* add one."""
    comments = gd.get("submission_peer_comments", {}).get(target, [])

    if comments:
        for c in comments:
            author = html.escape(str(c.get("author", "")))
            ts = html.escape(str(c.get("ts", "")))
            body = html.escape(str(c.get("text", ""))).replace("\n", "<br/>")
            st.markdown(
                f'<div class="feedback-box" style="margin-bottom:8px;padding:10px 14px;font-size:0.88rem">'
                f"<strong>{author}</strong> · {ts}<br/>"
                f'<span style="color:#333">{body}</span></div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("No peer comments yet.")

    if show_composer and viewer != target:
        st.caption("Share impressions, questions, or suggestions — be constructive.")
        state_key = f"peer_cmt_n_{group_code}_{viewer}_{target}"
        if state_key not in st.session_state:
            st.session_state[state_key] = 0
        n = st.session_state[state_key]
        inp_key = f"{state_key}_input_{n}"
        body = st.text_area(
            "Peer comment",
            key=inp_key,
            height=72,
            placeholder="Write your comment…",
            label_visibility="collapsed",
        )
        if st.button("Post comment", key=f"{state_key}_btn", use_container_width=True):
            ok, err = _post_submission_peer_comment(group_code, viewer, target, body)
            if ok:
                st.session_state[state_key] = n + 1
                st.rerun()
            else:
                st.warning(err)
