# Case Study Tutor — Alpes Bank GenAI

A group-based, AI-scaffolded business case study platform built on the
MAS prototype architecture. Developed as part of the *Data-Driven Service
Design & Management* course at the University of St. Gallen (HSG).

Each student opens the app in their own browser tab, enters their name
and a group code, and works through their assigned case section. The
Group Alignment Agent provides real-time feedback on contribution balance
(free-rider detection) and argument coherence (fragmentation detection).
Session data is stored as JSON files in `sessions/` so all group members
share the same state.

---

## What it does

| Feature | Description |
|---------|-------------|
| **Interest-based section matching** | Students pick 2–4 buzz-word interest tags; a greedy matching algorithm assigns each member the section with the most overlap — no two people get the same section |
| **Group lobby gate** | Sections are revealed only once the full group has joined; no one can start reading early |
| **Individual AI feedback** | Scaffolded hints after each submission (no spoilers; Teaching Note used only by agents) |
| **Cross-section connection prompts** | Every student sees directed bridge questions between their section and each colleague's — forward ("your section feeds into §X") and backward ("§X feeds into yours") |
| **Full case access** | Both the reading page and the writing page offer a collapsed full-case accordion so students can read beyond their own section without losing their draft |
| **Free-rider detection** | Flags missing or low-effort contributions; non-accusatory group nudges |
| **Fragmentation analysis** | Detects argument gaps & contradictions across submissions; scores group coherence 0–100 |
| **Contribution scoring** | Per-member score 0–100 across Completion /10, Effort /20, Substance /35, Engagement /15, Synthesis /20 — AI-evaluated once all synthesis submissions are in |
| **Synthesis round** | Guides the group toward one integrated argument with a coaching note from the Group Alignment Agent |
| **Group chat** | WhatsApp-style chat panel in the sidebar, available on every page; messages auto-refresh every 8 s; unread badge alerts members to new messages |

---

## The two problems it addresses

1. **Tasks split but never reconciled** — The Group Alignment Agent compares all
   individual submissions, scores argument coherence (0–100), and asks Socratic
   questions that push the group to integrate their analyses. Cross-section
   connection prompts nudge students toward integration *while* they write.

2. **Free-rider problem** — Contribution tracking shows word counts and submission
   status for every member in real time. Low-effort or missing submissions trigger
   automated, non-accusatory nudges. The lobby gate ensures no one can be left
   out of section assignment.

---

## Session flow

```
Welcome (buzz-word selection)
    │
    ▼
Lobby ──(refresh until full)──► all members joined
    │                                   │
    │         ◄─────── sections assigned by preference match
    ▼
Reading  ←── full case accordion available here
    │
    ▼
Writing  ←── three tabs: ✍️ Write | 📖 Your section | 📚 Full case
    │         🔗 Cross-section connection prompts inside Write tab
    │         Draft persists across tab switches via keyed session state
    ▼
Group Alignment  ←── free-rider panel + coherence score + scaffold questions
    │
    ▼
Synthesis  ←── each member contributes to one integrated answer
    │
    ▼
Done  ←── stats, contribution report card, score donut, all synthesis contributions
```

> 💬 **Group chat** is available in the sidebar on *every* page after login —
> students can coordinate, flag cross-section connections, and resolve
> disagreements without leaving their current step.

---

## Contribution score breakdown

| Component | Max | How it's measured |
|-----------|-----|-------------------|
| **Completion** | 10 | Submitted on or before the individual submission deadline = 10; after = 0; no deadline set = 7 |
| **Effort** | 20 | Word count relative to the group median; penalises outliers below 25 % of median |
| **Substance** | 35 | AI-evaluated: case-specificity, structure, depth; structural heuristic used until AI scoring runs |
| **Engagement** | 15 | AI-evaluated: cross-section references and integration; structural fallback counts explicit §-references |
| **Synthesis** | 20 | AI-evaluated: quality of synthesis contribution; structural fallback on word count + vocabulary variety |
| **Total** | 100 | |

AI scoring runs once — after all synthesis submissions are in — and the results are cached in the session file.

---

## Quick start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up your API key
```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY (free at console.groq.com)
```

### 3. Run the app
```bash
streamlit run app.py
```

Opens at `https://datadrivenservicedesignandmgmt-8q6xympjjf9tknu9xcrqww.streamlit.app/`.

---

## Running a group session

1. **Creator** opens the app → *Create a new group* → enters name, group size, interest
   tags, and optional deadlines → receives a **6-character group code**.
2. **Other members** open the same URL → *Join existing group* → enter name, group
   code, and their own interest tags.
3. Everyone waits in the **lobby** until the group is full — the lobby shows who
   has joined and their interest tags.
4. Once the last member joins, sections are assigned by preference match and
   everyone is forwarded to the reading page automatically.
5. Students read their section (and optionally browse the full case), then move
   to the writing page.
6. On the writing page, the **🔗 Cross-section connections** expander shows
   directed bridge questions for every other section. Students should reference
   at least one other section in their submission.
7. After submission, AI feedback appears in the right panel.
8. Once all members have submitted, the Group Alignment Agent runs automatically.
9. The group reviews the alignment report, discusses the scaffold questions, then
   each member writes their synthesis contribution.
10. The **Done** page shows each member's contribution report card with a score
    donut, component breakdown, and the full group synthesis.

> **Group chat** is always available in the sidebar. Use it to flag connections
> between sections, agree on shared framing, or nudge a quiet group member —
> all without leaving your current page. Messages auto-refresh every 8 s and
> an unread badge (🔴) alerts you when something new arrives.

---

## Deadlines

When creating a group the organiser can optionally set two dates:

| Deadline | Purpose |
|----------|---------|
| **Individual submission** | Members who submit on or before this date earn full Completion points (10/10); submitting after scores 0 |
| **Final submission** | Target date for the group synthesis round |

The individual submission deadline cannot be set after the final submission deadline.
Both dates are shown in the sidebar with a warning flag (⚠️) once they have passed.

---

## Buzz-word interest tags

Students select from 12 tags. Each tag maps to the sections it best matches:

| Tag | Primarily maps to |
|-----|-------------------|
| 📊 Strategy & Vision | §1, §4, §5 |
| 🏦 Banking & Finance | §1 |
| 💡 Innovation & Products | §2 |
| 🤝 Vendor Management | §3 |
| ⚖️ Governance & Compliance | §4 |
| 🏗️ Organisational Design | §5 |
| 🔬 Risk & Assessment | §2, §3, §4 |
| 🌐 Digital Transformation | §1, §2, §3 |
| 👥 Leadership & Culture | §5 |
| 🤖 AI & Technology | §1, §2, §3 |
| 📋 Policy & Frameworks | §4 |
| 💼 Change Management | §5 |

If two students pick the same top section, the greedy algorithm resolves the
conflict by maximising total preference satisfaction across the group. Falls back
to round-robin when preferences are empty or tied.

---

## The five case sections

| # | Title | Emoji |
|---|-------|-------|
| 1 | Alpes Bank & Strategic Context | 🏦 |
| 2 | Selecting the GenAI Use Case | 🔍 |
| 3 | Partner Dependencies & Risk | 🔒 |
| 4 | GenAI Governance: The 3C Framework | ⚖️ |
| 5 | Organisational Design for GenAI at Scale | 🏗️ |

---

## File structure

```
Remote_Data_Driven/
├── app.py                    # Entry point — page config, global CSS, and page router
│
├── core/                     # Domain logic: the "brain" of the app
│   ├── workflow.py           # Group lifecycle, scoring, AI agent calls
│   └── case_content.py       # All case material, interest tags, section connections
│
├── database/                 # Data persistence layer
│   └── storage.py            # Read/write group session JSON files — nothing else touches disk
│
├── components/               # Reusable UI building blocks (rendered inside pages)
│   └── sidebar.py            # Sidebar panel, step indicator, contribution score donut
│
├── views/                    # One file per screen — imports from core/ and components/
│   ├── welcome.py            # Create / join group + interest-tag selection
│   ├── lobby.py              # Waiting room until the full group has joined
│   ├── reading.py            # Case reading + full-case accordion
│   ├── working.py            # 3-tab writing page + cross-section connection prompts
│   ├── alignment.py          # Free-rider panel + coherence score + scaffold questions
│   ├── synthesis.py          # Integrated group answer round
│   └── done.py               # Summary, individual contribution report, score donut
│
├── agents/                   # AI agents (free-rider detection, fragmentation, scoring)
│   └── group_alignment_agent.py
│
├── sessions/                 # Auto-created at runtime; one JSON file per group code
├── config.json               # AI model/provider configuration
├── requirements.txt
└── .env.example              # API key template
```

### Module dependency flow

```
app.py
  └── views/*.py
        ├── core/workflow.py
        │     ├── database/storage.py
        │     ├── core/case_content.py
        │     └── agents/group_alignment_agent.py
        ├── core/case_content.py
        ├── database/storage.py
        └── components/sidebar.py
              ├── core/workflow.py
              └── core/case_content.py
```

---

## Switching AI provider

Edit `config.json`:
```json
{
  "ai_manager": {
    "client": "open_router",
    "primary_model": "meta-llama/llama-3.3-70b-instruct:free"
  }
}
```
Supported clients: `groq` (default, free), `open_router`, `openai`.
Set the matching key in `.env` (see `.env.example`).

---