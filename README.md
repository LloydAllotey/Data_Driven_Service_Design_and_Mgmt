# Case Study Tutor — Alpes Bank GenAI

A group-based, AI-scaffolded business case study platform built on the
MAS prototype architecture. Developed as part of the *Data-Driven Service
Design & Management* course at the University of St. Gallen (HSG).

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
Done  ←── stats, all synthesis contributions, alignment report
```

> 💬 **Group chat** is available in the sidebar on *every* page after login —
> students can coordinate, flag cross-section connections, and resolve
> disagreements without leaving their current step.

---

## Quick start

### 1. Install dependencies
```bash
cd case_study_tutor
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

Opens at `http://localhost:8501`.

---

## Running a group session

1. **Creator** opens the app → *Create a new group* → enters name, group size, and
   selects 2–4 interest tags → receives a **6-character group code**.
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

> **Group chat** is always available in the sidebar. Use it to flag connections
> between sections, agree on shared framing, or nudge a quiet group member —
> all without leaving your current page. Messages auto-refresh every 8 s and
> an unread badge (🔴) alerts you when something new arrives.

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
case_study_tutor/
├── app.py                         # Main Streamlit application (~1 300 lines)
│                                  #   page_lobby()     — waiting room
│                                  #   page_reading()   — case + full-case accordion
│                                  #   page_working()   — 3-tab writing page
│                                  #   page_alignment() — free-rider + coherence
│                                  #   page_synthesis() — integrated answer round
│                                  #   page_done()      — summary screen
├── case_content.py                # All case content and matching logic
│   ├── SECTIONS                   # 5 case sections (text, questions, buzz_word_slugs)
│   ├── BUZZ_WORDS                 # 12 interest tags with emoji + slug
│   ├── SECTION_CONNECTIONS        # 20 directed bridge pairs (i→j) with questions
│   ├── EXPERT_ANSWERS             # Teaching Note summaries (agents only, never shown)
│   ├── GROUP_SYNTHESIS_QUESTIONS  # 5 overarching synthesis questions
│   ├── assign_sections_by_preferences()   # Greedy preference-matching algorithm
│   └── assign_sections_to_members()       # Legacy round-robin fallback
├── config.json                    # AI model configuration
├── requirements.txt               # includes streamlit-autorefresh for chat polling
├── .env.example                   # API key template
├── agents/
│   ├── __init__.py
│   └── group_alignment_agent.py   # Free-rider + fragmentation agent
└── sessions/                      # Auto-created; one JSON file per group code
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

## Course context

- **Course:** Data-Driven Service Design & Management (4 ECTS)
- **Institution:** University of St. Gallen (HSG)
- **Challenge:** Adapt the MAS prototype to support group-based business case analysis
- **Case used:** *Alpes Bank's Journey to Creating Value at Scale with Generative AI*
  (Harvard Business Case format)
- **Teaching Note:** Used as the expert reference for agent calibration; never shown
  to students (equivalent role to the expert concept map in the original MAS)
- **Original prototype:** Diana Kozachek's MAS scaffolding system (concept maps)
