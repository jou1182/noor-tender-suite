# ConTech AI Platform — منصة الذكاء المتعدد الوكلاء لمنافسات البناء

> **Multi-Agent Tender Intelligence for Saudi Construction**
> 37 AI agents read the RFP, cross-examine your proposal clause-by-clause, and surface disqualification gaps before the evaluator does.

<p align="center">
  <b>FastAPI · LangGraph · Next.js 15 · PostgreSQL · Qdrant · Redis · Docker</b><br/>
  <sub>187 passing tests · Arabic-first UI with English toggle · Deterministic engines + LLM hybrid</sub>
</p>

---

## العربية — نظرة سريعة

منصة تحلل كراسات المنافسات (RFP) الإنشائية السعودية عبر 37 وكيلاً متخصصاً:
تقارن عرضك الفني مع كراسة الشروط بنداً-بنداً، تكشف فجوات الاستبعاد، تتحقق هندسياً ضد
الكود السعودي SBC، وتدقق الجداول الزمنية بمعايير DCMA — ثم تُصدّر تقريراً مختوماً
ببصمة SHA-256. الواجهة عربية أولاً مع زر تبديل للإنجليزية، وكل وكيل قابل للتدريب
وإعادة التسمية من شاشة الإعدادات.

**البدء في 3 خطوات**: انظر [Quick Start](#quick-start) أدناه — أو انقر مرتين على
`ConTech.bat` على سطح المكتب (يشغّل Docker ويفتح المتصفح تلقائياً).

---

## What It Solves

| Pain | Before | With ConTech AI |
|---|---|---|
| RFPs of 2000+ pages | Days of manual reading | Structured extraction in minutes |
| Administrative disqualification (Etimad) | Discovered after submission | Flagged before you submit |
| Self-graded proposals (bias) | "We think we're compliant" | Clause-level COMPLIANT / DEVIATION / GAP verdicts |
| Hidden schedule risks in P6/XER | Found on site | DCMA 14-point + Monte Carlo (5000 runs) upfront |
| Knowledge leaves with employees | Tribal knowledge | Institutional memory across tenders |
| Compliance claims you can't prove | Verbal assurances | SHA-256 sealed audit dossier |

## Core Capabilities

- **Swarm Orchestration** — LangGraph pipeline of 37 agents; launch on any tender with one click (`إنطلقوا أيها الوكلاء`)
- **RFP Compliance Studio** — live compliance matrix with per-clause verdicts and severity
- **Proposal Evaluation** — scores your team's technical proposal against competition criteria: strengths, weaknesses, partial coverage, score /100 (bilingual Arabic/English matcher)
- **Agent Training Room** — rename agents (ar/en), edit system prompts, adjust temperature, live-preview behavior before saving
- **Universal LLM Providers** — 12 ready templates (DeepSeek, Groq, OpenRouter, Together, Mistral, Claude, Gemini, Ollama, LM Studio…) + any custom OpenAI-compatible endpoint; automatic model-fallback
- **Document Intelligence** — auto-classification (criteria/specs/BOQ/drawings/proposal…), OCR for scanned PDFs, ZIP auto-extraction with zip-bomb & path-traversal guards, RAG Q&A over the corpus with file+page citations
- **Sealed Output** — every audit dossier stamped with SHA-256 for legal traceability

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│  Browser (localhost:3000)                                  │
│  Next.js 15 · App Router · Tajawal · i18n ar/en · SSE      │
└──────────────┬─────────────────────────────────────────────┘
               │ REST + Server-Sent Events
┌──────────────▼─────────────────────────────────────────────┐
│  Backend (localhost:8000)                                  │
│  FastAPI · RBAC (JWT) · BackgroundTasks · Fernet vault     │
│                                                            │
│  ┌──────────────── LangGraph Swarm ─────────────────┐      │
│  │ 37 agents: client_rfp → compliance → engineering │      │
│  │ → schedule(DCMA) → pricing → redteam → dossier   │      │
│  └──────────────────────────────────────────────────┘      │
│  Deterministic engines: SBC-304 · DCMA · Etimad ·          │
│  CrossExamMatrix · ProposalEvaluator                       │
└───┬──────────┬──────────┬──────────┬───────────────────────┘
    │          │          │          │
┌───▼───┐ ┌────▼───┐ ┌────▼───┐ ┌────▼────┐
│Postgres│ │ Qdrant │ │ Redis  │ │ LLM API │
│ (DB)  │ │vectors │ │ queue  │ │/Ollama  │
└───────┘ └────────┘ └────────┘ └─────────┘
```

**Design principle**: deterministic engines do the math and compliance checks (no hallucination possible); LLMs only enrich language. Every agent is bindable to a different provider/model from Settings.

## Quick Start

### One-click (recommended)

Double-click **`ConTech.bat`** on the desktop (auto-created at deploy). It starts Docker Desktop if needed, brings up the stack, waits for health, and opens the browser.

### Manual setup

```bash
# 1) Prerequisites: Docker Desktop + git
# 2) Clone and configure
git clone https://github.com/jou1182/contech-ai-platform.git
cd contech-ai-platform
cp .env.docker.example .env   # then edit values (see inside)

# 3) Start the full stack
docker compose up -d --build

# 4) Verify
curl http://localhost:8000/api/v1/health   # {"status":"UP",...}
# Open http://localhost:3000
```

### First competition workflow

1. **Start Fresh** (`بدء من جديد`) → blank workspace
2. **New Competition** (`منافسة جديدة`) → wizard: name it (e.g. صيانة طريق مكة-جدة), add client, drop RFP files (+XER if available)
3. Upload the team's proposal via the purple **Upload Proposal** button
4. **Evaluate Proposal** → strengths / weaknesses / score
5. **Launch Agents** (`إنطلقوا أيها الوكلاء`) → full swarm audit
6. Ask the corpus questions; every answer cites file & page

## Running for Development

```bash
# Backend (venv)
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Windows
.venv/Scripts/python -m uvicorn app.main:app --port 8000

# Frontend
cd frontend
npm install
npm run dev            # localhost:3000

# Full test suite (187 tests)
.venv/Scripts/python -m pytest tests/ -p no:cacheprovider

# Frontend type check
cd frontend && npx tsc --noEmit
```

> **Deployment rule**: after any code change with Docker running —
> `docker compose build backend frontend && docker compose up -d backend frontend`
> — otherwise containers keep serving the old image.

## Project Structure

```
├── app/                        # FastAPI backend
│   ├── agents/                 # 37 swarm agents + graph.py orchestrator
│   ├── parsers/                # deterministic engines (SBC, DCMA, cross-exam…)
│   ├── api/v1/endpoints/       # tenders, documents, agents, analytics…
│   ├── core/                   # llm_gateway, security, crypto, i18n seeds
│   ├── services/               # document_pipeline, zip_extractor…
│   └── models/                 # SQLAlchemy models
├── frontend/
│   └── src/
│       ├── app/                # pages (/, /settings, /dashboard…)
│       ├── components/         # studios, library, wizard, canvas…
│       ├── lib/                # api clients, i18n dictionary
│       └── hooks/              # useTenderAudit, telemetry
├── skills/software-development/  # hermes-agent skill (project auditor)
├── tests/                      # 187 tests (pytest)
├── docs/                       # USER_GUIDE_AR · HANDOVER · MARKETING · AUDIT
├── docker-compose.yml          # 5 containers
└── ConTech.bat                 # one-click launcher
```

## Configuration

All secrets via environment — never committed (see `.env.example`):

| Variable | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | JWT + crypto vault derivation | dev-only value (change in prod!) |
| `DATABASE_URL` | PostgreSQL connection | compose internal |
| `ALLOWED_ORIGINS` | CORS whitelist | `http://localhost:3000` |
| `QDRANT_URL` / `REDIS_URL` | Vector store / queue | compose internal |

LLM providers are configured **from the UI** (Settings → LLM Providers): pick a template, paste the key — it's Fernet-encrypted in the database.

## Testing

```bash
.venv/Scripts/python -m pytest tests/ -p no:cacheprovider
# 187 passed — includes RBAC, ingestion, swarm lifecycle, RBAC isolation,
# proposal evaluation, and the audit-skill self-tests
```

## Documentation

| Doc | Audience |
|---|---|
| [`docs/USER_GUIDE_AR.md`](docs/USER_GUIDE_AR.md) | End users (Arabic, full workflow) |
| [`docs/HANDOVER.md`](docs/HANDOVER.md) | Next developer/agent (state, decisions, pitfalls) |
| [`docs/MARKETING_PLAYBOOK_AR.md`](docs/MARKETING_PLAYBOOK_AR.md) | Sales: pains, personas, ROI, objections |
| [`docs/PLATFORM_AUDIT_REPORT.md`](docs/PLATFORM_AUDIT_REPORT.md) | Technical health snapshot |

## Status & Roadmap

- ✅ MVP complete: ingestion → swarm → studios → sealed dossier
- ✅ Security audit passed (path traversal, CORS, secrets — all patched)
- 🔜 Portfolio dashboard live data binding
- 🔜 Pilot on 3–5 real tenders (the sales gate)
- 🔜 Full RTL polish + English docs mirror

## Author

**Youssef Seleim (jou1182)** — owner & product vision, with Hermes Agent as engineering collaborator.

## License

Private commercial project — © 2026 Youssef Seleim. All rights reserved.
