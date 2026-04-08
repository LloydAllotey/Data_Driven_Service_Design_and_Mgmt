"""
Case Content — Alpes Bank: Creating Value at Scale with Generative AI
Based on the Harvard Business School Teaching Case provided by Diana Kozachek (HSG).

This module contains:
  - SECTIONS: the 5 case study sections shown to students
  - EXPERT_ANSWERS: Teaching Note summaries used ONLY by agents (never shown to students)
  - GROUP_QUESTIONS: overarching synthesis questions for the group alignment round
"""

# ── Buzz words students use to express interests ─────────────────────────────
# Each entry: slug (used in matching), label (shown in UI), emoji
BUZZ_WORDS = [
    {"slug": "strategy",      "label": "Strategy & Vision",       "emoji": "📊"},
    {"slug": "banking",       "label": "Banking & Finance",        "emoji": "🏦"},
    {"slug": "innovation",    "label": "Innovation & Products",    "emoji": "💡"},
    {"slug": "vendor",        "label": "Vendor Management",        "emoji": "🤝"},
    {"slug": "governance",    "label": "Governance & Compliance",  "emoji": "⚖️"},
    {"slug": "org_design",    "label": "Organisational Design",    "emoji": "🏗️"},
    {"slug": "risk",          "label": "Risk & Assessment",        "emoji": "🔬"},
    {"slug": "digital_transf","label": "Digital Transformation",   "emoji": "🌐"},
    {"slug": "leadership",    "label": "Leadership & Culture",     "emoji": "👥"},
    {"slug": "ai_tech",       "label": "AI & Technology",          "emoji": "🤖"},
    {"slug": "policy",        "label": "Policy & Frameworks",      "emoji": "📋"},
    {"slug": "change_mgmt",   "label": "Change Management",        "emoji": "💼"},
]

# ── Colour palette referenced in the app ─────────────────────────────────────
THEME = {
    "primary":    "#003C87",   # HSG blue
    "primary_lt": "#E8F0FE",   # light blue
    "success":    "#27AE60",
    "warning":    "#F39C12",
    "danger":     "#E74C3C",
    "neutral":    "#6C757D",
    "bg":         "#F8F9FA",
    "card":       "#FFFFFF",
}

# ── Five case‑study sections ──────────────────────────────────────────────────
SECTIONS = [
    {
        "id": 1,
        "slug": "context",
        "emoji": "🏦",
        "title": "Alpes Bank & Strategic Context",
        "duration_hint": "~8 min read",
        "case_text": """
**Setting the scene — GenAI arrives in Swiss banking**

With generative artificial intelligence (GenAI) now commercially available, Swiss banks are
moving quickly to pilot it. On the customer side, banks have begun testing GenAI-enabled
robo-advisors and savings coaches, positioning them as always-on, low-cost extensions of
traditional advisory services. Inside banks, GenAI co-pilots are being tested as general
assistants. The fastest adopters in the Swiss banking industry are already sharing their first
GenAI success stories on social media, suggesting they could soon automate most of their
employees' work.

**Alpes Bank**

Alpes Bank is one of Switzerland's leading universal banks, renowned for providing
high-quality banking services. It has been in business for over a century and employs 4,000
people, serving one million customers across Switzerland. While peers shifted focus to digital
channels, Alpes Bank doubled down on personal, in-branch relationships as its core
differentiator. Though it continues to invest in digital services, the bank remains resolutely
branch-centric.

This stance reflects its customer base, which is on average 51 years old and upper-middle
class — they value in-person service and are willing to pay a premium for it. Although
customers interact with the bank across multiple channels, the bank's own study of its channel
economics found that the traditional brick-and-mortar business is still *more profitable* than
its digital channels.

This traditional model has not stopped Alpes Bank from selectively adopting AI tools. For
example, its customer analytics team uses a model that predicts "next best offers." Similarly,
the risk and compliance division has sourced a machine-learning solution for predicting credit
default. So far, the bank has followed a **buy-first approach**, sourcing AI applications from
external vendors and focusing on integration into its existing IT infrastructure.

**Tamara Maurer's Mandate**

Alpes Bank took notice of GenAI when competitors began offering GenAI-driven investment advice
at a fraction of its traditional cost. The board launched a standalone venture led by **Tamara
Maurer**, Head of Digital Transformation, to demonstrate how GenAI might be deployed without
compromising service levels. Tamara was empowered to move quickly, bypassing some traditional
processes. However, given Alpes Bank's traditional culture — which prioritises risk avoidance —
she needed to demonstrate clear business value to secure ongoing support. The CEO summarised
the mandate in one sentence:

> *"By quarter-end, I want a no-regret GenAI pilot, something we can roll out quickly,
> that shows clear business value, and does not break anything."*
""",
        "question": "How does Alpes Bank's competitive position and organisational culture shape its approach to GenAI adoption? Was the board's decision to explore GenAI strategically motivated or merely reactive?",
        "sub_questions": [
            "What makes Alpes Bank's business model distinctive in the Swiss banking market?",
            "Was the board's GenAI initiative driven by a clear strategic vision or by competitive anxiety (FOMO)?",
            "What cultural and organisational factors might support — or hinder — GenAI adoption at Alpes Bank?",
        ],
        "key_concepts": ["branch-centric model", "buy-first AI strategy", "risk-avoidance culture", "FOMO vs strategy"],
        "buzz_word_slugs": ["strategy", "banking", "digital_transf", "ai_tech"],
    },
    {
        "id": 2,
        "slug": "usecase",
        "emoji": "🔍",
        "title": "Selecting the GenAI Use Case",
        "duration_hint": "~7 min read",
        "case_text": """
**Finding a GenAI Use Case**

Tamara invited data scientists from the bank's existing data and AI teams, and colleagues from
IT to ensure technical alignment. She scheduled a one-day ideation offsite. Although the
session unfolded with less structure than initially planned, the whiteboard filled quickly with
ideas. The group converged on three promising options:

---

**Option A — Alpes Bank E-Mail Assistant**
Customer service agents rely on a single 483-page document, the *Business Case List*, to answer
many of the customer e-mails they handle. Accessing this file via the bank's wiki requires
exact search terms, making the process error-prone. A retrieval-augmented generation (RAG)
assistant could instantly draft responses — though agents would need to verify and sometimes
edit the draft. This partial automation could reduce **average handling time**, a closely
monitored board-level metric for the contact centre.

**Option B — Alpes Bank Co-Pilot**
Employees often rely on informal networks to locate information scattered across the intranet,
Confluence, archived e-mails, and other sources. An internal knowledge assistant could reduce
the time spent gathering information. However, every response would need to be grounded in an
identified source to ensure traceability and reduce the risk of false replies. Secure guardrails
would also be necessary to ensure employees see only data they are authorised to access.

**Option C — Website Help-Chatbot**
Customers increasingly expect instant responses to simple requests such as "I lost my card."
A public-facing chatbot could meet these expectations — but the reputational risks of any
mistake are considerable. The design would be deliberately constrained: only answers based on
company policies, with disclaimers, and no handling of requests requiring authentication.

---

**Tamara's Decision**

After quick impact-versus-effort estimates, Tamara made her call:

> *"In twelve weeks, I either walk into the executive board meeting with a GenAI pilot,
> or with explanations."*

She pointed to the three options and said: *"We go with the E-Mail Assistant."*
""",
        "question": "Was the e-mail assistant a strategically sound inaugural GenAI use case for Alpes Bank? Critically evaluate the use-case selection process and identify its key strengths, gaps, and risks.",
        "sub_questions": [
            "Did the use-case selection process align GenAI with Alpes Bank's core value proposition, or was it technology-first?",
            "What structured approach could have improved the selection process (e.g., decision matrix, stakeholder involvement, external benchmarking)?",
            "What are the main opportunities AND risks of the e-mail assistant across Finance, Employee, Technology, Legal, and Customer dimensions?",
        ],
        "key_concepts": ["RAG", "average handling time", "strategic alignment", "opportunity-risk matrix", "technology-first trap"],
        "buzz_word_slugs": ["innovation", "ai_tech", "risk", "digital_transf"],
    },
    {
        "id": 3,
        "slug": "dependencies",
        "emoji": "🔒",
        "title": "Partner Dependencies & Risk",
        "duration_hint": "~8 min read",
        "case_text": """
**Building a Custom GenAI Solution**

To build the e-mail assistant, Tamara partnered with **AILabs**, an external AI consultancy
experienced in RAG-based applications. AILabs would use **Microsoft Azure** as the cloud
hosting environment and **OpenAI** as the large-language-model (LLM) provider — creating a
three-layer dependency chain.

The RAG system works as follows: when a customer service agent receives an e-mail, they enter
a query. The system searches the Business Case List, retrieves the most relevant passages, and
feeds them to the OpenAI model, which generates a draft reply. The agent reviews the draft,
edits as needed, and sends it.

**Tensions During Development**

The project surfaced several tensions:

- **Agile vs. stage-gate:** AILabs worked in agile two-week sprints, whereas Alpes Bank's IT
  governance required formal sign-offs at defined gates. Neither side had fully mapped the
  other's process at the start.
- **"Definition of done":** The bank's business side considered the pilot "done" when it
  reduced average handling time. The technical team considered it "done" when the system
  passed integration tests. These definitions were never aligned upfront.
- **Language edge cases:** German-language e-mails occasionally containing Romansh words
  disrupted the retrieval logic — an unanticipated failure mode discovered only in testing.
- **Fairness risks:** The system performed less well on dialect-rich messages, raising concerns
  about unequal service quality for some customer segments.

**Pilot Results**

Despite the tensions, the pilot launched on schedule. In the first three months, the e-mail
assistant cut **average handling time by 21%** — a result that exceeded the board's
expectations and secured continued investment.
""",
        "question": "Analyse the risks arising from Alpes Bank's three-layer dependency on AILabs, Microsoft Azure, and OpenAI. What short-term and long-term mitigation strategies would you recommend?",
        "sub_questions": [
            "Categorise the dependency risks across Economic, Organisational, Technological, and Legal dimensions for each provider.",
            "Which risk poses the greatest threat to Alpes Bank's long-term GenAI ambitions, and why?",
            "What short-term (during pilot) and long-term (post-scale) mitigation strategies would you propose?",
        ],
        "key_concepts": ["vendor lock-in", "RAG pipeline", "agile vs stage-gate", "definition of done", "fairness risk"],
        "buzz_word_slugs": ["vendor", "risk", "ai_tech", "digital_transf"],
    },
    {
        "id": 4,
        "slug": "governance",
        "emoji": "⚖️",
        "title": "GenAI Governance: The 3C Framework",
        "duration_hint": "~6 min read",
        "case_text": """
**Scaling Requires Governance**

The e-mail assistant's success created a new problem: every division now wanted a GenAI pilot.
The CEO was supportive but insistent:

> *"Without governance, GenAI will create unmanaged risk. Before we scale, we need a
> framework that every team understands and follows."*

Tamara designed a governance framework anchored in three principles — **Competent, Compliant,
Calculated** (the "3C framework"):

| Principle | Meaning |
|-----------|---------|
| **Competent** | We have the skills and knowledge to build and operate GenAI responsibly |
| **Compliant** | We follow all applicable regulations, internal policies, and ethical guidelines |
| **Calculated** | We take deliberate, evidence-based decisions about where and how to deploy GenAI |

**Roles in the Governance Process**

Tamara also defined clear accountability roles:

- **Head of AI** — Sets strategy and ensures cross-divisional alignment
- **Tech Owner** — Responsible for the technical implementation and security of each use case
- **Business Owner** — Accountable for business outcomes and ROI
- **Knowledge Owner** — Manages the data and content fed into the AI system
- **End User** — The employee using the tool day-to-day; responsible for verification

**Operationalising Governance**

Tamara insisted that each new use case pass through a formal GenAI governance process before
deployment — covering data privacy, model selection, fairness testing, and rollback planning.
She was careful not to make this process so burdensome that it would kill innovation. The
mantra across the team became: *"Move fast but don't break trust."*
""",
        "question": "Evaluate the strengths and weaknesses of Tamara's 3C governance framework. How would you operationalise it across Alpes Bank's business divisions?",
        "sub_questions": [
            "What are the strengths of the Competent-Compliant-Calculated framework? What potential gaps do you see?",
            "Assign specific skills and responsibilities to each governance role (Head of AI, Tech Owner, Business Owner, Knowledge Owner, End User).",
            "What concrete actions could Alpes Bank take under each C to ensure the governance framework is more than just a slogan?",
        ],
        "key_concepts": ["3C framework", "AI governance", "accountability roles", "compliance", "risk management"],
        "buzz_word_slugs": ["governance", "policy", "risk", "strategy"],
    },
    {
        "id": 5,
        "slug": "orgdesign",
        "emoji": "🏗️",
        "title": "Organisational Design for GenAI at Scale",
        "duration_hint": "~7 min read",
        "case_text": """
**One Year Later**

Twelve months after the e-mail assistant pilot, Alpes Bank has deployed several additional
GenAI use cases — but the CEO is not satisfied:

> *"We are still thinking about GenAI in ways that simply replicate our existing
> organisational structure. Each division builds its own silo. The greatest value will
> come from improving end-to-end processes, or rethinking them altogether."*

**The Organisational Design Challenge**

Tamara is tasked with proposing an organisational design that enables GenAI innovation across
divisional boundaries. She is considering three models:

**Model A — Centralised AI Centre of Excellence (CoE)**
A dedicated AI unit owns all GenAI projects, talent, and infrastructure. Business units submit
use-case requests and receive delivered solutions. *Pro:* standardisation and talent
concentration. *Con:* bottleneck risk; business units feel disempowered.

**Model B — Federated Model**
Each division has its own AI team, guided by shared standards from a small central office.
*Pro:* speed and business-unit ownership. *Con:* risk of duplicated effort and inconsistent
standards.

**Model C — Embedded + Hub-and-Spoke**
Small AI pods are embedded in key business units, coordinated by a central hub that owns
governance, tooling, and foundational models. *Pro:* balances speed with consistency.
*Con:* requires strong matrix management and clear role definitions.

**The End-to-End Imperative**

Regardless of the model chosen, the CEO's view is that GenAI's highest value lies not in
automating single tasks, but in **reimagining end-to-end processes** that currently span
multiple organisational silos. For example: the journey from a customer complaint e-mail →
routing → drafting → compliance review → sending could be almost fully automated — but only if
the customer service, compliance, and IT divisions coordinate their GenAI efforts.
""",
        "question": "Propose an organisational design that enables Alpes Bank to unlock GenAI value across end-to-end processes rather than within divisional silos. Justify your choice and address the implementation risks.",
        "sub_questions": [
            "Compare the three organisational models (CoE, Federated, Hub-and-Spoke) against Alpes Bank's specific culture and strategic needs.",
            "Which end-to-end process offers the highest GenAI value potential beyond the e-mail assistant? Map out the cross-divisional steps.",
            "What change-management challenges would Tamara face in implementing your proposed design, and how would you address them?",
        ],
        "key_concepts": ["centre of excellence", "federated AI", "hub-and-spoke", "end-to-end process", "change management"],
        "buzz_word_slugs": ["org_design", "leadership", "change_mgmt", "strategy"],
    },
]

# ── Expert answers (Teaching Note) — NEVER shown to students ─────────────────
# Used only by the GroupAlignmentAgent and individual scaffolding agents
# to assess quality and provide scaffolded hints (not direct answers).
EXPERT_ANSWERS = {
    "context": {
        "summary": """
Alpes Bank positions itself as a branch-centric universal bank using digital tools to complement,
not replace, in-person service. It outperforms industry peers in the branch channel (CHF 140
profit/customer vs CHF 80 for peers) but underperforms across digital channels. Its customer
base (avg. age 51, upper-middle class) values high-touch service and pays a premium for it.

Critically, the board's GenAI initiative was driven by competitive anxiety (FOMO) — a reaction
to competitors offering GenAI investment advice at lower cost — rather than a proactive vision
for how GenAI could strengthen Alpes Bank's distinctive value proposition. This distinction is
important: it shaped many of the downstream challenges Tamara encountered.

Cultural factors that may hinder adoption: risk-avoidance culture, stage-gate IT processes,
branch-centric mindset, older customer base sceptical of AI.
Cultural factors that may support adoption: existing buy-first AI experience, Tamara's mandate
to move quickly, board-level urgency.
""",
        "key_themes": ["branch-centric strategy", "FOMO vs vision", "CHF 140 vs CHF 80", "risk-avoidance culture"],
    },
    "usecase": {
        "summary": """
The use-case selection lacked a guiding strategic vision. Tamara's team started from the
technology (GenAI) rather than from business problems or Alpes Bank's core value proposition.
Key process gaps:
1. No external benchmarking (how do peers use GenAI?)
2. No structured decision matrix (impact/effort/risk scoring)
3. Limited stakeholder inclusion (no compliance, legal, or business-unit employees)
4. Cost-savings estimates ignored people/change-management investment
5. No phased roll-out plan or explicit success metrics defined upfront

Opportunities of the e-mail assistant: boosts productivity, reduces cognitive load, faster
replies improve NPS, lays RAG groundwork for future use cases.
Risks: fairness issues for dialect speakers, data privacy (personal data in e-mails),
hallucination risk, employee job-security concerns, ongoing maintenance costs.
""",
        "key_themes": ["technology-first trap", "strategic anchor", "decision matrix", "opportunity-risk matrix", "stakeholder inclusion"],
    },
    "dependencies": {
        "summary": """
Three-layer dependency chain: AILabs (integration) → Microsoft Azure (cloud) → OpenAI (LLM).
Each layer introduces distinct risks:

AILabs: critical GenAI expertise outside the bank; agile-vs-stage-gate tension; lock-in risk;
unclear IP ownership of jointly developed prompts.
Azure: regional outage risk; vendor-specific governance tooling; data residency requirements
under Swiss law.
OpenAI: model deprecation risk; silent updates change behaviour; cross-border data flows;
token price increases; no data-retention guarantees without explicit contract.

Short-term mitigation: SLAs with cap on costs; data-residency guarantees; modular codebase;
API-first design.
Long-term mitigation: build internal GenAI team; multi-cloud posture; open-source fallback
models; annual price benchmarking; LLM model-broker layer.
""",
        "key_themes": ["vendor lock-in", "data residency", "model deprecation", "SLA", "internal capability building"],
    },
    "governance": {
        "summary": """
Strengths of 3C: simple mnemonic, covers three essential dimensions, gives employees a shared
language, flexible enough for different use cases.
Potential gaps: no explicit human-oversight requirement; no fairness/bias testing mandate;
unclear escalation path when a use case fails; no sunset clause for discontinued models.

Role responsibilities (Teaching Note guidance):
- Head of AI: portfolio strategy, cross-divisional alignment, external horizon scanning
- Tech Owner: architecture, security, SLA compliance, model monitoring
- Business Owner: ROI accountability, change management, user adoption
- Knowledge Owner: data quality, access controls, content freshness
- End User: prompt quality, output verification, incident reporting

Concrete 3C actions:
Competent: mandatory GenAI literacy training; internal CoE; rotation programme.
Compliant: data-privacy impact assessments; EU AI Act mapping; audit trails.
Calculated: use-case scoring matrix; staged rollouts; KPI dashboards; kill-switch protocols.
""",
        "key_themes": ["3C framework", "role clarity", "fairness testing", "audit trail", "kill-switch"],
    },
    "orgdesign": {
        "summary": """
Teaching Note recommendation: Hub-and-spoke (Model C) best fits Alpes Bank's need to balance
speed with governance, given its risk-averse culture and multiple business units.

The central hub owns: governance standards, foundational model contracts, shared tooling,
enterprise-wide data infrastructure. Business-unit pods own: use-case ideation, domain-specific
prompt engineering, change management.

Highest-value end-to-end process: customer complaint handling (complaint e-mail → triage →
draft → compliance review → send → CRM update). Spans customer service, compliance, and IT.

Change-management challenges: divisional turf protection; talent competition between hub and
pods; resistance from branch staff fearing automation; need for new matrix accountability
structures. Mitigation: phased rollout with early-adopter divisions; transparent communication
about job redesign (not elimination); shared KPIs across hub and pods.
""",
        "key_themes": ["hub-and-spoke", "end-to-end process", "change management", "matrix accountability", "talent strategy"],
    },
}

# ── Group synthesis questions (used in the final integration round) ───────────
GROUP_SYNTHESIS_QUESTIONS = [
    "How does Alpes Bank's strategic context (Section 1) explain the governance gaps identified in Sections 3 and 4?",
    "Is the 3C governance framework (Section 4) sufficient to manage the dependency risks identified in Section 3? What additional safeguards are needed?",
    "Does the organisational design proposed in Section 5 address the root cause identified in Section 1 (FOMO vs. strategic vision)?",
    "How do the risks in Section 2 (use-case selection) cascade into the challenges in Sections 3 and 4?",
    "Build a single coherent argument: What is the most important recommendation Tamara should make to the CEO, drawing on all five sections?",
]

# ── Cross-section connection map ─────────────────────────────────────────────
# Keys: (from_section_id, to_section_id)
# Values: (direction_label, bridge_question)
#   direction_label — short phrase describing the relationship
#   bridge_question — the reflective question shown to the student
SECTION_CONNECTIONS: dict[tuple[int, int], tuple[str, str]] = {
    # § 1 → others
    (1, 2): (
        "§1 sets the stage for §2",
        "Your analysis of Alpes Bank's FOMO-driven culture and buy-first strategy should "
        "explain *why* the email assistant was chosen. Does your section make that selection "
        "feel inevitable — or does it reveal it as a strategic misstep?",
    ),
    (1, 3): (
        "§1 explains the risk appetite behind §3",
        "The bank's risk-avoidance culture (§1) should show up in how it managed vendor "
        "dependencies. How does the strategic context you describe predict — or fail to "
        "prevent — the lock-in risks your colleague analyses in §3?",
    ),
    (1, 4): (
        "§1 reveals the governance void that §4 must fill",
        "FOMO-led AI adoption without a clear strategy is precisely what governance "
        "frameworks are designed to prevent. How does the strategic gap you identify "
        "strengthen the case for the 3C framework in §4?",
    ),
    (1, 5): (
        "§1's strategy must be reflected in §5's org design",
        "A branch-centric, relationship-first bank needs a very specific type of AI "
        "organisation. Does the strategic positioning you describe in §1 align with "
        "the organisational model your colleague proposes in §5?",
    ),
    # § 2 → others
    (2, 1): (
        "§2 stress-tests the strategic narrative in §1",
        "The use-case selection process reveals whether Alpes Bank's stated strategy "
        "actually guided decisions — or whether it was bypassed. How does your analysis "
        "of the email assistant choice confirm or complicate the strategic picture in §1?",
    ),
    (2, 3): (
        "§2's use-case choice directly created §3's dependency problem",
        "Selecting the email assistant meant selecting a RAG pipeline and specific "
        "vendors. How did the decision your section evaluates make the lock-in risks "
        "in §3 almost unavoidable? Could a different use-case choice have reduced them?",
    ),
    (2, 4): (
        "§2's selection process exposed a governance gap that §4 must close",
        "Did the use-case selection follow any structured governance? What governance "
        "controls (from §4's 3C framework) would have most improved the process you "
        "evaluate?",
    ),
    (2, 5): (
        "§2 reveals which organisational capabilities §5 must build",
        "Selecting and evaluating a GenAI use case requires specific skills and "
        "decision-making structures. What organisational capabilities does your "
        "analysis show were missing — and how should §5's org design address them?",
    ),
    # § 3 → others
    (3, 1): (
        "§3's risks are a product of §1's strategic choices",
        "The vendor dependencies you analyse emerged from a buy-first, speed-first "
        "culture. How does your risk analysis reflect back on the strategic stance "
        "described in §1? Does it vindicate or challenge that strategy?",
    ),
    (3, 2): (
        "§3 is the downstream consequence of §2's decisions",
        "The dependency risks you map are largely a consequence of how the email "
        "assistant use case was selected and scoped. How does your analysis in §3 "
        "change how we should evaluate the decision in §2?",
    ),
    (3, 4): (
        "§3's risks are exactly what §4's governance must manage",
        "Vendor lock-in, fairness risk, and agile-vs-stage-gate tensions all need "
        "governance responses. Which specific elements of the 3C framework (§4) are "
        "most critical for mitigating the risks you identify?",
    ),
    (3, 5): (
        "§3 reveals the organisational capabilities §5 must build",
        "Managing complex vendor relationships and technical dependencies requires "
        "dedicated roles and structures. What does your dependency analysis imply "
        "for the hub-and-spoke or CoE models your colleague evaluates in §5?",
    ),
    # § 4 → others
    (4, 1): (
        "§4's framework is a direct response to §1's strategic vacuum",
        "The 3C framework addresses the very FOMO-driven, ungoverned AI adoption "
        "described in §1. How does your governance analysis diagnose the root cause "
        "your colleague identified — and does it fully solve it?",
    ),
    (4, 2): (
        "§4's governance would have transformed §2's selection process",
        "A 'Calculated' pillar in the 3C framework focuses on structured use-case "
        "evaluation. How would applying your governance framework have changed the "
        "email assistant selection process analysed in §2?",
    ),
    (4, 3): (
        "§4 is the control layer that manages §3's risks",
        "Dependency and vendor risks (§3) need governance controls to manage them. "
        "How explicitly does your 3C framework address the specific risks your "
        "colleague maps — and where are the remaining gaps?",
    ),
    (4, 5): (
        "§4's framework needs §5's org design to become real",
        "A governance framework is only as strong as the people and structures "
        "implementing it. How should the organisational design in §5 be shaped to "
        "operationalise the 3C framework you propose?",
    ),
    # § 5 → others
    (5, 1): (
        "§5's org design must fit §1's strategic identity",
        "A federated hub-and-spoke model may feel alien to a relationship-first, "
        "branch-centric bank. How does your proposed organisational design account "
        "for the cultural and strategic context described in §1?",
    ),
    (5, 2): (
        "§5's structure determines whether §2-style mistakes recur",
        "Good use-case selection requires the right people in the right roles with "
        "the right mandate. How would your organisational model have prevented the "
        "selection process gaps identified in §2?",
    ),
    (5, 3): (
        "§5's org design must manage the risks in §3",
        "Vendor dependency management needs clear ownership and capability. How does "
        "your proposed structure allocate responsibility for the risks your colleague "
        "identifies in §3?",
    ),
    (5, 4): (
        "§5 is the implementation layer for §4's governance",
        "The 3C governance framework (§4) needs concrete roles, teams, and processes. "
        "How explicitly does your organisational design operationalise each of the "
        "three Cs — and where does the link feel weakest?",
    ),
}

# ── Section assignment helpers ────────────────────────────────────────────────

def assign_sections_by_preferences(member_preferences: dict) -> dict:
    """
    Smart section assignment based on each member's buzz-word preferences.

    member_preferences: {member_name: [buzz_word_slug, ...]}
    Returns: {member_name: [section_id, ...]}

    Algorithm:
      1. Score every (member, section) pair by counting overlapping buzz words.
      2. Greedily assign the best-scoring available section to each member
         (maximises total preference satisfaction without repeating sections).
      3. Distribute any remaining unassigned sections round-robin.
      4. Falls back to round-robin when preferences are empty.
    """
    members = list(member_preferences.keys())
    n = len(members)
    if n == 0:
        return {}

    # Build score matrix
    scores: dict[str, dict[int, int]] = {}
    for member, prefs in member_preferences.items():
        pref_set = set(prefs)
        scores[member] = {
            sec["id"]: len(pref_set & set(sec.get("buzz_word_slugs", [])))
            for sec in SECTIONS
        }

    # Ranked list of (score, member, section_id) — higher is better
    ranked = sorted(
        [
            (scores[m][sec["id"]], m, sec["id"])
            for m in members
            for sec in SECTIONS
        ],
        reverse=True,
    )

    assignments: dict[str, list] = {m: [] for m in members}
    assigned_members: set = set()
    used_sections: set = set()

    # First pass: one primary section per member
    for _score, member, sid in ranked:
        if member not in assigned_members and sid not in used_sections:
            assignments[member].append(sid)
            assigned_members.add(member)
            used_sections.add(sid)
        if len(assigned_members) == n:
            break

    # Fallback: any member still without a section (all had zero score + collisions)
    remaining_primary = [s["id"] for s in SECTIONS if s["id"] not in used_sections]
    for member in members:
        if member not in assigned_members and remaining_primary:
            sid = remaining_primary.pop(0)
            assignments[member].append(sid)
            used_sections.add(sid)

    # Second pass: distribute leftover sections (when group < 5)
    leftover = [s["id"] for s in SECTIONS if s["id"] not in used_sections]
    for i, sid in enumerate(leftover):
        assignments[members[i % n]].append(sid)

    return assignments


def assign_sections_to_members(member_names: list) -> dict:
    """
    Legacy round-robin assignment (used as fallback when no preferences given).
    Kept for backward compatibility with existing session files.
    """
    prefs = {name: [] for name in member_names}
    return assign_sections_by_preferences(prefs)


def get_section_by_id(section_id: int) -> dict:
    """Return the section dict for a given section ID (1–5)."""
    for s in SECTIONS:
        if s["id"] == section_id:
            return s
    raise ValueError(f"No section with id {section_id}")


def get_section_by_slug(slug: str) -> dict:
    """Return the section dict for a given slug."""
    for s in SECTIONS:
        if s["slug"] == slug:
            return s
    raise ValueError(f"No section with slug '{slug}'")
