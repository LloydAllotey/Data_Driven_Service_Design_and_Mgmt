"""
Group Alignment Agent
=====================
Addresses TWO problems identified through student interviews:

  Problem 1 — Tasks split but never reconciled
    Students divide the case into sections and each works in isolation.
    Individual answers are good, but the group never integrates them into one
    coherent argument. The agent detects argument gaps, contradictions, and
    missing links ACROSS submissions and asks scaffolded questions to prompt
    integration — without giving away the Teaching Note answers.

  Problem 2 — Free-rider problem
    Some group members contribute minimal text or submit well after peers.
    The agent tracks submission status and word-count signals, then sends
    gentle, accountability-framing nudges to the whole group so that inactivity
    becomes visible without being accusatory.

Architecture
------------
  GroupAlignmentAgent
      ├── check_free_riders(group_data)  → FreeRiderReport
      ├── analyze_fragmentation(submissions, section_assignments)  → FragmentationReport
      └── generate_synthesis_prompt(group_data, synthesis_round)  → str

All heavy thinking is delegated to an LLM via the AIClient helper.
The agent NEVER reveals expert answers; it only asks questions and points to
gaps the students must fill themselves.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# Load .env from parent of this file's package directory
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

logger = logging.getLogger(__name__)

MIN_WORDS_THRESHOLD = 40      # below this → flagged as low-effort
FREE_RIDER_LATE_THRESHOLD = 2  # member counts as "late" if this many others submitted first


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class MemberStatus:
    name: str
    has_submitted: bool
    word_count: int = 0
    section_ids: List[int] = field(default_factory=list)
    is_low_effort: bool = False
    is_late: bool = False


@dataclass
class FreeRiderReport:
    has_issue: bool
    missing_members: List[str]       # submitted nothing
    low_effort_members: List[str]    # submitted but very short
    late_members: List[str]          # submitted after most peers
    group_message: str               # scaffolded message to display to the group
    private_nudge: Dict[str, str]    # {member_name: private message}


@dataclass
class FragmentationReport:
    has_gaps: bool
    missing_connections: List[str]   # theme pairs not bridged
    contradictions: List[str]        # explicit contradictions detected
    orphaned_sections: List[str]     # sections not referenced by any other section
    scaffold_questions: List[str]    # questions to prompt integration (NOT answers)
    integration_score: int           # 0–100 rough coherence estimate
    summary_html: str                # formatted HTML for display


# ── AI client helper ─────────────────────────────────────────────────────────

class _AIClient:
    """Thin wrapper around OpenAI-compatible clients (Groq / OpenRouter / OpenAI)."""

    def __init__(self, config: dict):
        client_type = config.get("client", "groq")
        self.max_tokens = config.get("max_tokens", 700)
        self.temperature = config.get("temperature", 0.5)
        self.max_retries = config.get("max_retries", 3)

        if client_type == "groq":
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise EnvironmentError("GROQ_API_KEY not set in .env")
            self._client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
            self.model = config.get("primary_model", "llama-3.3-70b-versatile")
            self.fallback = config.get("fallback_model", "llama-3.1-8b-instant")

        elif client_type == "open_router":
            api_key = os.getenv("OPEN_ROUTER_API_KEY")
            if not api_key:
                raise EnvironmentError("OPEN_ROUTER_API_KEY not set in .env")
            self._client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
            self.model = config.get("primary_model", "meta-llama/llama-3.3-70b-instruct:free")
            self.fallback = config.get("fallback_model", "qwen/qwen3-coder:free")

        elif client_type == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise EnvironmentError("OPENAI_API_KEY not set in .env")
            self._client = OpenAI(api_key=api_key)
            self.model = config.get("primary_model", "gpt-4o-mini")
            self.fallback = config.get("fallback_model", "gpt-3.5-turbo")
        else:
            raise ValueError(f"Unsupported client type: {client_type}")

    def chat(self, system: str, user: str) -> str:
        for attempt in range(self.max_retries):
            model = self.model if attempt < self.max_retries - 1 else self.fallback
            try:
                resp = self._client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user",   "content": user},
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
                return resp.choices[0].message.content.strip()
            except Exception as exc:
                logger.warning(f"AI call attempt {attempt+1} failed: {exc}")
                if attempt < self.max_retries - 1:
                    time.sleep(1.5)
        return "[AI feedback temporarily unavailable — please try again in a moment.]"


# ── Group Alignment Agent ─────────────────────────────────────────────────────

class GroupAlignmentAgent:
    """
    Orchestrates group-level scaffolding for a business case study session.
    Designed as a standalone agent (no dependency on the parent MAS BaseAgent)
    so it can be imported directly into the Streamlit app.
    """

    SYSTEM_PROMPT = """You are a Socratic learning coach for a university business case study
session. Your role is to help student groups work more effectively TOGETHER — not to give them
answers.

Core rules:
1. NEVER reveal or paraphrase the expert Teaching Note answers.
2. Always respond with questions, not conclusions.
3. Be warm, encouraging, and specific — reference what students actually wrote.
4. Keep responses concise (max 220 words per response block).
5. Focus on cross-member coherence: how do the individual analyses fit together?
6. Surface tension, gaps, and contradictions as interesting puzzles, not failures.
"""

    def __init__(self, ai_config: dict):
        self._ai = _AIClient(ai_config)

    # ── Public API ──────────────────────────────────────────────────────────

    def check_free_riders(self, group_data: dict) -> FreeRiderReport:
        """
        Inspect the current group session and flag contribution imbalances.

        Parameters
        ----------
        group_data : dict
            The full group JSON session (as loaded from sessions/<code>.json).

        Returns
        -------
        FreeRiderReport with scaffolded messages.
        """
        members: List[str] = group_data.get("members", [])
        submissions: dict = group_data.get("submissions", {})

        statuses: List[MemberStatus] = []
        submitted_count = 0

        for name in members:
            sub = submissions.get(name)
            if sub and sub.get("text", "").strip():
                wc = len(sub["text"].split())
                submitted_count += 1
                statuses.append(MemberStatus(
                    name=name,
                    has_submitted=True,
                    word_count=wc,
                    is_low_effort=wc < MIN_WORDS_THRESHOLD,
                ))
            else:
                statuses.append(MemberStatus(name=name, has_submitted=False))

        missing   = [s.name for s in statuses if not s.has_submitted]
        low_effort = [s.name for s in statuses if s.has_submitted and s.is_low_effort]
        # "late" = submitted after ≥ FREE_RIDER_LATE_THRESHOLD peers, only meaningful
        # once most of the group has submitted
        late: List[str] = []
        if submitted_count >= len(members) - 1 and missing:
            late = missing  # still missing when most are done

        has_issue = bool(missing or low_effort)

        # Build group message
        group_message = self._build_free_rider_group_message(missing, low_effort, members)

        # Build per-person private nudge
        nudges: Dict[str, str] = {}
        for name in missing:
            nudges[name] = (
                f"Hi {name} — your group has already submitted their sections. "
                f"Your contribution is needed to complete the picture. "
                f"Even a first draft of your thinking helps the group move forward!"
            )
        for name in low_effort:
            sub_text = submissions.get(name, {}).get("text", "")
            nudges[name] = self._ai.chat(
                system=self.SYSTEM_PROMPT,
                user=(
                    f"Student '{name}' submitted a very short response ({len(sub_text.split())} words). "
                    f"Their text: \"{sub_text[:300]}\"\n\n"
                    f"Write a warm, 2-sentence private nudge asking them to expand their analysis. "
                    f"Reference what they wrote and suggest one specific angle to explore further."
                ),
            )

        return FreeRiderReport(
            has_issue=has_issue,
            missing_members=missing,
            low_effort_members=low_effort,
            late_members=late,
            group_message=group_message,
            private_nudge=nudges,
        )

    def analyze_fragmentation(
        self,
        submissions: Dict[str, str],
        section_titles: Dict[str, str],
    ) -> FragmentationReport:
        """
        Compare all group submissions and identify where arguments are
        fragmented, contradictory, or siloed.

        Parameters
        ----------
        submissions : {member_name: submitted_text}
        section_titles : {member_name: section_title_they_worked_on}

        Returns
        -------
        FragmentationReport with scaffold questions.
        """
        if len(submissions) < 2:
            return FragmentationReport(
                has_gaps=False,
                missing_connections=[],
                contradictions=[],
                orphaned_sections=[],
                scaffold_questions=["Your team hasn't submitted enough sections yet to analyse coherence."],
                integration_score=0,
                summary_html="<p>Waiting for more submissions…</p>",
            )

        # Build the combined submission block for the LLM
        combined = "\n\n---\n\n".join(
            f"**{name} — {section_titles.get(name, 'Unknown section')}**\n{text}"
            for name, text in submissions.items()
        )

        prompt = f"""Below are the individual submissions from a student group working on the
Alpes Bank GenAI business case. Each student analysed a different section.

{combined}

Analyse these submissions as a whole and return a JSON object with exactly these keys:
{{
  "missing_connections": ["<short description of a thematic bridge that is missing>", ...],
  "contradictions": ["<short description of a direct contradiction between two submissions>", ...],
  "orphaned_sections": ["<section title that is not referenced or connected by any other submission>", ...],
  "scaffold_questions": ["<question that prompts the group to bridge a specific gap, without giving the answer>", ...],
  "integration_score": <integer 0-100 representing how coherent the group argument is so far>,
  "coach_summary": "<2-3 sentence narrative summary for the group coach view>"
}}

Rules:
- scaffold_questions must be genuine Socratic questions (not statements or hints)
- integration_score: 0=completely fragmented, 100=fully integrated
- Be specific: reference what students actually wrote
- Maximum 4 items per list
- Return valid JSON only, no markdown code fences
"""

        raw = self._ai.chat(system=self.SYSTEM_PROMPT, user=prompt)

        # Parse JSON safely
        try:
            # Strip any accidental markdown fencing
            clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            data = json.loads(clean)
        except Exception:
            logger.warning(f"Could not parse fragmentation JSON: {raw[:200]}")
            data = {
                "missing_connections": [],
                "contradictions": [],
                "orphaned_sections": [],
                "scaffold_questions": [
                    "Where do the arguments from each section connect? Try to draw a line between two submissions.",
                    "Does your group have one consistent recommendation, or are there competing views?",
                ],
                "integration_score": 30,
                "coach_summary": "Feedback is being processed — please refresh in a moment.",
            }

        score = max(0, min(100, int(data.get("integration_score", 30))))
        questions = data.get("scaffold_questions", [])
        summary_html = self._build_fragmentation_html(data, score)

        return FragmentationReport(
            has_gaps=score < 70,
            missing_connections=data.get("missing_connections", []),
            contradictions=data.get("contradictions", []),
            orphaned_sections=data.get("orphaned_sections", []),
            scaffold_questions=questions,
            integration_score=score,
            summary_html=summary_html,
        )

    def generate_synthesis_prompt(
        self,
        group_data: dict,
        synthesis_question: str,
    ) -> str:
        """
        For the final synthesis round: generate a tailored prompt that
        encourages the group to write ONE integrated answer drawing on all
        five sections.

        Returns a markdown string to display in the app.
        """
        submissions = group_data.get("submissions", {})
        members_text = "\n".join(
            f"- {name}: {sub.get('text', '')[:400]}…"
            for name, sub in submissions.items()
            if sub.get("text")
        )

        return self._ai.chat(
            system=self.SYSTEM_PROMPT,
            user=(
                f"The group is now writing a joint synthesis answer to:\n"
                f"\"{synthesis_question}\"\n\n"
                f"Here is what each member wrote in their individual sections:\n{members_text}\n\n"
                f"Write a 3-bullet coaching note (max 180 words total) that:\n"
                f"1. Highlights one strength in the group's combined thinking so far.\n"
                f"2. Points to one specific gap or tension they must address in the synthesis.\n"
                f"3. Asks one question that will help them build a single coherent argument.\n"
                f"Do NOT answer the synthesis question. Only coach."
            ),
        )

    def scaffold_individual_submission(
        self,
        student_name: str,
        section_title: str,
        section_question: str,
        student_text: str,
        expert_summary: str,
    ) -> str:
        """
        Provide scaffolded feedback on a single student's section submission.
        Used after individual submit (before group alignment runs).

        expert_summary is passed to the LLM as hidden context only — it must
        NOT appear verbatim in the output.
        """
        return self._ai.chat(
            system=self.SYSTEM_PROMPT,
            user=(
                f"Student: {student_name}\n"
                f"Section: {section_title}\n"
                f"Question: {section_question}\n\n"
                f"Student's answer:\n{student_text}\n\n"
                f"[Hidden expert context for calibration only — do not reproduce]:\n{expert_summary}\n\n"
                f"Provide scaffolded feedback:\n"
                f"1. Acknowledge one specific strength in what they wrote.\n"
                f"2. Ask two probing questions that push them to deepen or reconsider their argument.\n"
                f"3. Suggest one concept or connection they haven't explored yet (no spoilers).\n"
                f"Keep the tone warm, curious, and constructive. Max 200 words."
            ),
        )

    # ── Private helpers ─────────────────────────────────────────────────────

    def _build_free_rider_group_message(
        self,
        missing: List[str],
        low_effort: List[str],
        all_members: List[str],
    ) -> str:
        submitted_count = len(all_members) - len(missing)
        total = len(all_members)

        if not missing and not low_effort:
            return (
                f"All {total} group members have submitted. "
                f"The Group Alignment Agent is ready to analyse your combined work."
            )

        parts = []
        if missing:
            names = ", ".join(missing)
            parts.append(
                f"{len(missing)} member(s) ({names}) haven't submitted yet. "
                f"The full group picture can only emerge once everyone contributes."
            )
        if low_effort:
            names = ", ".join(low_effort)
            parts.append(
                f"{len(low_effort)} submission(s) ({names}) appear brief. "
                f"Richer analysis from each member will strengthen the group's final argument."
            )

        progress = f"{submitted_count}/{total} members have submitted."
        return progress + " " + " ".join(parts)

    def _build_fragmentation_html(self, data: dict, score: int) -> str:
        colour = "#27AE60" if score >= 70 else "#F39C12" if score >= 40 else "#E74C3C"
        label  = "Well integrated" if score >= 70 else "Partially integrated" if score >= 40 else "Fragmented"
        coach  = data.get("coach_summary", "")

        parts = [
            f'<div style="margin-bottom:12px">'
            f'<span style="font-weight:600;color:{colour}">'
            f'Integration score: {score}/100 — {label}'
            f'</span></div>',
            f'<p style="color:#333;margin-bottom:8px">{coach}</p>',
        ]

        if data.get("missing_connections"):
            parts.append("<p><strong>Bridges your group hasn't built yet:</strong></p><ul>")
            for item in data["missing_connections"]:
                parts.append(f"<li>{item}</li>")
            parts.append("</ul>")

        if data.get("contradictions"):
            parts.append('<p><strong style="color:#E74C3C">Tensions to resolve:</strong></p><ul>')
            for item in data["contradictions"]:
                parts.append(f"<li>{item}</li>")
            parts.append("</ul>")

        return "".join(parts)
