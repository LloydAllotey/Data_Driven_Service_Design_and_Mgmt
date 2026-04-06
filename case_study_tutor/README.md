# Case Study Tutor — Alpes Bank GenAI

A group-based, AI-scaffolded business case study platform built on the
MAS prototype architecture. Developed as part of the *Data-Driven Service
Design & Management* course at the University of St. Gallen (HSG).

## What it does

| Feature | Description |
|---------|-------------|
| **Group sessions** | Students join via a shared 6-character code |
| **Section assignment** | Each member gets 1 case section assigned automatically |
| **Individual AI feedback** | Scaffolded hints after each submission (no spoilers) |
| **Free-rider detection** | Flags missing or low-effort contributions to the group |
| **Fragmentation analysis** | Detects argument gaps & contradictions across submissions |
| **Synthesis round** | Guides the group toward one integrated argument |

## The two problems it addresses

1. **Tasks split but never reconciled** — The Group Alignment Agent compares
   all individual submissions, scores argument coherence (0–100), and asks
   Socratic questions that push the group to integrate their analyses.

2. **Free-rider problem** — Contribution tracking shows word counts and
   submission status for every member in real time. Low-effort or missing
   submissions trigger automated, non-accusatory group nudges.

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

The app opens at `http://localhost:8501`.

### 4. Running a group session

1. **Creator** opens the app, clicks *"Create a new group"*, enters their name and group size → receives a **6-character group code**.
2. **Other members** open the same URL (or share via localhost for a local demo), click *"Join existing group"*, enter their name and the group code.
3. Everyone reads their assigned case section, writes their analysis, and submits.
4. Once all members submit, the Group Alignment Agent runs automatically.
5. The group reviews the alignment report, discusses the scaffold questions, then writes the synthesis.

## File structure

```
case_study_tutor/
├── app.py                    # Main Streamlit application
├── case_content.py           # Alpes Bank case text + Teaching Note (expert answers)
├── config.json               # AI model configuration
├── requirements.txt
├── .env.example              # API key template
├── agents/
│   ├── __init__.py
│   └── group_alignment_agent.py   # Free-rider + fragmentation agent
└── sessions/                 # Auto-created; stores group JSON files
```

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
And set the matching key in `.env`.

## Course context

- **Course:** Data-Driven Service Design & Management (4 ECTS)
- **Institution:** University of St. Gallen (HSG)
- **Challenge:** Design a multi-agent system that supports solving complex
  business cases
- **Case used:** *Alpes Bank's Journey to Creating Value at Scale with
  Generative AI* (based on Harvard Business Case Store format)
- **Teaching Note:** Used as the expert reference for agent calibration;
  never shown to students
