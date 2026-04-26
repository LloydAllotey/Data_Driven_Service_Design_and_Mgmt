"""
core/workflow.py — Business logic.

Groups, submissions, contribution scoring, and AI agent calls.
All session I/O is delegated to database/storage.py.
"""

from __future__ import annotations

import json
import re
import statistics
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

import streamlit as st

from database.storage import (
    _load_session,
    _new_group_code,
    _save_session,
    _session_path,
)
from core.case_content import (
    assign_sections_by_preferences,
    get_section_by_id,
)

# ROOT is the project root (Remote_Data_Driven/), one level above core/
ROOT = Path(__file__).parent.parent

# ── Lazy-loaded agent singleton ───────────────────────────────────────────────
_agent = None


def _load_config() -> dict:
    cfg_path = ROOT / "config.json"
    if cfg_path.exists():
        with open(cfg_path) as f:
            return json.load(f)
    return {"ai_manager": {"client": "groq", "primary_model": "llama-3.3-70b-versatile"}}


def _get_agent():
    global _agent
    if _agent is None:
        try:
            from agents.group_alignment_agent import GroupAlignmentAgent
            cfg = _load_config()
            _agent = GroupAlignmentAgent(cfg.get("ai_manager", {}))
        except Exception as e:
            st.warning(f"AI agent unavailable: {e}. Add your API key to .env to enable feedback.")
    return _agent


# ── Group lifecycle ───────────────────────────────────────────────────────────

def _create_group(
    creator_name: str,
    group_size: int,
    preferences: list,
    internal_deadline: Optional[str] = None,
    external_deadline: Optional[str] = None,
) -> dict:
    code = _new_group_code()
    while _session_path(code).exists():
        code = _new_group_code()
    data = {
        "group_code": code,
        "created_at": datetime.now().isoformat(),
        "members": [creator_name],
        "expected_size": group_size,
        "preferences": {creator_name: preferences},
        "internal_deadline": internal_deadline,
        "external_deadline": external_deadline,
        "section_assignments": {},
        "submissions": {},
        "feedback": {},
        "alignment_reports": [],
        "synthesis_submissions": {},
        "submission_peer_comments": {},
        "phase": "lobby",
    }
    if group_size == 1:
        data["section_assignments"] = assign_sections_by_preferences(data["preferences"])
        data["phase"] = "reading_ready"
    _save_session(data)
    return data


def _join_group(
    code: str, member_name: str, preferences: list
) -> tuple[bool, str, Optional[dict]]:
    """Returns (success, error_message, group_data)."""
    data = _load_session(code)
    if data is None:
        return False, f"Group code '{code}' not found. Check the code and try again.", None
    if member_name in data["members"]:
        if preferences:
            data.setdefault("preferences", {})[member_name] = preferences
            _save_session(data)
        return True, "", data
    if len(data["members"]) >= data.get("expected_size", 5):
        return False, "This group is already full.", None
    data["members"].append(member_name)
    data.setdefault("preferences", {})[member_name] = preferences
    if len(data["members"]) >= data.get("expected_size", 5):
        data["section_assignments"] = assign_sections_by_preferences(data["preferences"])
        data["phase"] = "reading_ready"
    _save_session(data)
    return True, "", data


# ── Submissions ───────────────────────────────────────────────────────────────

def _submit_answer(code: str, member: str, section_id: int, text: str) -> dict:
    data = _load_session(code)
    if data is None:
        return {}
    data["submissions"][member] = {
        "section_id": section_id,
        "text": text,
        "word_count": len(text.split()),
        "submitted_at": datetime.now().isoformat(),
    }
    expected = data.get("expected_size", len(data["members"]))
    if len(data["submissions"]) >= expected:
        if data["phase"] in ("waiting", "reading", "working"):
            data["phase"] = "aligning"
    _save_session(data)
    return data


def _submit_synthesis(code: str, member: str, text: str) -> dict:
    data = _load_session(code)
    if data is None:
        return {}
    data["synthesis_submissions"][member] = {
        "text": text,
        "submitted_at": datetime.now().isoformat(),
    }
    if len(data["synthesis_submissions"]) >= len(data["members"]):
        data["phase"] = "done"
    _save_session(data)
    return data


def _all_submitted(group_data: dict) -> bool:
    return len(group_data.get("submissions", {})) >= len(group_data.get("members", []))


# ── Scoring ───────────────────────────────────────────────────────────────────

def _compute_contribution_scores(group_data: dict) -> dict:
    """
    Compute a 0-100 Contribution Balance Score per member.

    Components
    ----------
    Completion   0–10
    Effort       0–20
    Substance    0–35   AI-primary, structural fallback
    Engagement   0–15   AI-primary, structural fallback
    Synthesis    0–20   AI-primary, structural fallback
    """
    members     = group_data.get("members", [])
    submissions = group_data.get("submissions", {})
    synth_subs  = group_data.get("synthesis_submissions", {})
    internal_dl = group_data.get("internal_deadline")
    ai_cache    = group_data.get("ai_content_scores", {})

    member_set = set(m.lower() for m in members)

    word_counts = [
        submissions[m].get("word_count", 0)
        for m in members
        if m in submissions and submissions[m].get("word_count", 0) > 0
    ]
    median_wc = statistics.median(word_counts) if word_counts else 0

    def _unique_word_ratio(text: str) -> float:
        content_words = [w for w in re.findall(r'[a-z]+', text.lower()) if len(w) > 3]
        if not content_words:
            return 0.0
        return len(set(content_words)) / len(content_words)

    def _sentence_rep_ratio(text: str) -> float:
        sents = [s.strip().lower() for s in re.split(r'[.!?]', text) if len(s.strip()) > 8]
        if not sents:
            return 0.0
        return 1 - (len(set(sents)) / len(sents))

    scores = {}
    for member in members:
        sub       = submissions.get(member)
        synth     = synth_subs.get(member)
        member_ai = ai_cache.get(member, {})
        ai_scored = bool(member_ai)

        # 1. Completion (0–10)
        if sub:
            if internal_dl:
                try:
                    submitted_at  = datetime.fromisoformat(sub.get("submitted_at", ""))
                    deadline_dt   = datetime.fromisoformat(internal_dl)
                    on_time       = submitted_at <= deadline_dt
                    completion    = 10 if on_time else 0
                    on_time_label = (
                        "Submitted on time ✓" if on_time
                        else "Submitted after individual deadline"
                    )
                except Exception:
                    completion, on_time, on_time_label = 7, None, "No deadline set"
            else:
                completion, on_time, on_time_label = 7, None, "No deadline set"
        else:
            completion, on_time, on_time_label = 0, False, "Not submitted"

        # 2. Effort (0–20)
        wc = sub.get("word_count", 0) if sub else 0
        if median_wc > 0 and wc > 0:
            ratio = wc / median_wc
            if   ratio >= 1.0:  effort = 20; effort_label = f"{wc} words — at or above group median"
            elif ratio >= 0.75: effort = 15; effort_label = f"{wc} words — slightly below group median"
            elif ratio >= 0.5:  effort = 10; effort_label = f"{wc} words — well below group median"
            elif ratio >= 0.25: effort = 5;  effort_label = f"{wc} words — much shorter than peers"
            else:               effort = 0;  effort_label = f"{wc} words — minimal contribution"
        elif wc > 0:
            effort = 14; effort_label = f"{wc} words (only submitter, no group median yet)"
        else:
            effort = 0;  effort_label = "No submission"

        # 3. Substance (0–35) — AI-primary, structural fallback
        if ai_scored and "substance" in member_ai:
            substance        = member_ai["substance"]
            substance_label  = member_ai.get("substance_feedback", "")
            substance_source = "ai"
        elif sub:
            text      = sub.get("text", "")
            raw_sents = [s.strip() for s in re.split(r'[.!?]', text) if len(s.strip()) > 8]
            n_sent    = len(raw_sents)
            uwr       = _unique_word_ratio(text)
            srr       = _sentence_rep_ratio(text)
            depth_pts = min(n_sent, 10) * 2.0
            quality_m = max(0.0, min(1.0, (uwr - 0.35) / 0.30))
            sent_pen  = srr * 5
            raw_sub   = depth_pts * quality_m - sent_pen
            substance = max(0, min(35, round(raw_sub * (35 / 20))))
            if uwr < 0.35:
                substance_label = (
                    f"\u26a0\ufe0f High word repetition ({round(uwr*100)}% unique words) — "
                    f"provisional score, AI evaluation pending"
                )
            elif n_sent >= 8:
                substance_label = (
                    f"{n_sent} sentences, {round(uwr*100)}% vocabulary variety — "
                    f"provisional, AI evaluation pending"
                )
            else:
                substance_label = f"{n_sent} sentences — provisional score, AI evaluation pending"
            substance_source = "structural"
        else:
            substance = 0; substance_label = "No submission"; substance_source = "structural"

        # 4. Engagement (0–15) — AI-primary, structural fallback
        if ai_scored and "engagement" in member_ai:
            engagement        = member_ai["engagement"]
            engagement_label  = member_ai.get("engagement_feedback", "")
            engagement_source = "ai"
        elif sub:
            text_lower = sub.get("text", "").lower()
            sec_refs   = re.findall(
                r'\u00a7\s*[1-5]|section\s+[1-5one-five]|sect\.\s*[1-5]|\bpart\s+[1-5]\b',
                text_lower,
            )
            peer_refs = [
                m for m in member_set
                if m != member.lower() and len(m) > 2 and m in text_lower
            ]
            total_refs = len(set(sec_refs)) + len(peer_refs)
            engagement = min(15, total_refs * 5)
            if total_refs == 0:
                engagement_label = "No cross-section references detected — provisional, AI evaluation pending"
            elif total_refs == 1:
                engagement_label = "1 cross-section reference — provisional, AI evaluation pending"
            else:
                engagement_label = f"{total_refs} cross-section references — provisional, AI evaluation pending"
            engagement_source = "structural"
        else:
            engagement = 0; engagement_label = "No submission"; engagement_source = "structural"

        # 5. Synthesis (0–20) — AI-primary, structural fallback
        if ai_scored and "synthesis" in member_ai:
            synthesis        = member_ai["synthesis"]
            synthesis_label  = member_ai.get("synthesis_feedback", "")
            synthesis_source = "ai"
        elif synth:
            synth_text = synth.get("text", "")
            synth_wc   = len(synth_text.split())
            synth_uwr  = _unique_word_ratio(synth_text)
            if synth_wc >= 30 and synth_uwr >= 0.40:
                synthesis = 20
                synthesis_label = f"Contributed {synth_wc} words — provisional, AI evaluation pending"
            elif synth_wc >= 30:
                synthesis = 10
                synthesis_label = (
                    f"\u26a0\ufe0f High repetition in synthesis ({round(synth_uwr*100)}% unique) — "
                    f"provisional, AI evaluation pending"
                )
            elif synth_wc > 0:
                synthesis = 5
                synthesis_label = f"Only {synth_wc} words — too short (min. 30), provisional"
            else:
                synthesis = 0; synthesis_label = "Did not contribute to synthesis"
            synthesis_source = "structural"
        else:
            synthesis = 0; synthesis_label = "Did not contribute to synthesis"; synthesis_source = "structural"

        total = completion + effort + substance + engagement + synthesis

        if   total >= 80: colour = "#27AE60"; label = "Excellent"
        elif total >= 60: colour = "#F39C12"; label = "Good"
        elif total >= 40: colour = "#E67E22"; label = "Needs improvement"
        else:             colour = "#E74C3C"; label = "Low contribution"

        scores[member] = {
            "total":            total,
            "completion":       completion,
            "effort":           effort,
            "substance":        substance,
            "engagement":       engagement,
            "synthesis":        synthesis,
            "ai_scored":        ai_scored,
            "word_count":       wc,
            "median_wc":        round(median_wc),
            "on_time":          on_time,
            "on_time_label":    on_time_label,
            "effort_label":     effort_label,
            "substance_label":  substance_label,
            "engagement_label": engagement_label,
            "synthesis_label":  synthesis_label,
            "colour":           colour,
            "label":            label,
        }

    return scores


def _trigger_ai_content_scoring(code: str, group_data: dict) -> dict:
    """
    Calls the GroupAlignmentAgent to AI-evaluate Substance, Engagement, and Synthesis
    for all members. Caches results in the session file under 'ai_content_scores'.
    Returns the updated group_data dict.
    """
    agent = _get_agent()
    if not agent:
        return group_data

    assignments = group_data.get("section_assignments", {})
    section_titles = {
        m: get_section_by_id(assignments.get(m, [1])[0])["title"]
        for m in group_data.get("members", [])
        if assignments.get(m)
    }

    try:
        ai_scores = agent.score_contributions(group_data, section_titles)
        fresh = _load_session(code)
        if fresh is not None:
            fresh["ai_content_scores"] = ai_scores
            _save_session(fresh)
            return fresh
        group_data["ai_content_scores"] = ai_scores
        _save_session(group_data)
    except Exception as e:
        traceback.print_exc()
        st.warning(f"AI content scoring failed: {e}")

    return group_data


# ── Chat ──────────────────────────────────────────────────────────────────────

def _post_message(code: str, member: str, text: str) -> None:
    """Append a chat message to the group session file."""
    data = _load_session(code)
    if data is None:
        return
    data.setdefault("chat", []).append({
        "member": member,
        "text": text.strip(),
        "ts": datetime.now().strftime("%H:%M"),
    })
    data["chat"] = data["chat"][-200:]
    _save_session(data)


def _post_submission_peer_comment(
    code: str, author: str, target_member: str, text: str
) -> tuple[bool, str]:
    """
    Append a peer comment on another member's individual submission.

    Returns (success, error_message).
    """
    body = (text or "").strip()
    if not body:
        return False, "Comment cannot be empty."
    if len(body) > 4000:
        return False, "Comment is too long (max 4000 characters)."
    if author == target_member:
        return False, "You cannot comment on your own submission."

    data = _load_session(code)
    if data is None:
        return False, "Session not found."
    subs = data.get("submissions", {})
    if author not in subs:
        return False, "Submit your own analysis before commenting on others."
    if target_member not in subs:
        return False, "This member has not submitted yet."

    bucket = data.setdefault("submission_peer_comments", {})
    lst = bucket.setdefault(target_member, [])
    now = datetime.now()
    lst.append({
        "author": author,
        "text": body,
        "ts": now.strftime("%H:%M"),
        "at": now.isoformat(),
    })
    bucket[target_member] = lst[-100:]
    _save_session(data)
    return True, ""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _member_sections(group_data: dict, member: str) -> list:
    """Return list of section IDs assigned to this member."""
    return group_data.get("section_assignments", {}).get(member, [1])
