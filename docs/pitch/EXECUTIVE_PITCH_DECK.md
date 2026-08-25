# ConTech AI Platform — Executive Pitch Deck

> Enterprise Autonomous Tender Intelligence for the Kingdom's Megaproject Pipeline
> Version 1.0 · Confidential — For Stakeholder Review

---

## Slide 1 — Cover

**ConTech AI Platform**

Autonomous Multi-Agent Tender Intelligence & Technical Bid Production

- From RFP to Certified Submission in hours, not months
- SBC-304 / FIDIC / ASTM deterministic governance
- Built for Saudi Arabia's giga-project ecosystem (NEOM, Qiddiya, ROSHN, Aramco)

---

## Slide 2 — Problem Statement

**The tender lifecycle is the highest-risk, highest-cost phase of infrastructure delivery.**

- 60–120 days consumed per major bid across estimation, compliance, and proposal assembly
- Engineering standards (SBC-304, FIDIC Red Book) are manually cross-referenced — error-prone
- Cost overruns on bids originate in missed clauses, schedule flaws, and pricing blind spots
- Team attrition compounds institutional knowledge loss

---

## Slide 3 — Solution: ConTech AI Platform

**A deterministic multi-agent swarm that audits and produces technical bids end-to-end.**

| Capability | Manual Baseline | ConTech AI |
|---|---|---|
| BOQ parsing (5,000 lines) | 5–10 days | < 5 seconds |
| SBC-304 compliance audit | 2–4 weeks | Real-time |
| VE opportunity identification | Ad-hoc | Automated |
| Proposal document assembly | 2–3 weeks | Minutes |

---

## Slide 4 — Multi-Agent Architecture (LangGraph)

```
RFP/BOQ/Schedule ──▶ Ingestion ──▶ ┌── SBC-304 Audit ──┐
                                    ├── GIS Logistics ──┤
                                    ├── FIDIC Risk ─────┤
                                    ├── VE Optimization ┤
                                    └── Cash Flow ──────┘
                                            │
                                     Risk Gate (<70%)
                                            │
                              Strategic Pricing ──▶ Pre-Submission Gatekeeper
                                            │
                              Certified PDF/DOCX + PAdES Signature
```

- Shared `OverallTenderState` TypedDict propagates through 20+ specialized nodes
- Parallel branch execution for SBC, GIS, and FIDIC audits
- Persistent checkpointer for resilient, resumable runs

---

## Slide 5 — SBC-304 & FIDIC Governance

**Deterministic rule engines, not probabilistic guesswork.**

- **SBC-304 Structural Engine**: f'c, w/c, fy, cover validated per exposure class (S1–S4) and placement context — every substitution blocked or cleared with a machine-readable reason
- **FIDIC Rule Engine**: Sub-Clauses 4.2 (performance security), 8.7 (LD cap ≤ 10%), 14.2/14.3 (payment), 20.1 (claim windows) — legal exposure scored 0–100
- **DCMA 14-Point Schedule Audit**: missing logic, negative lags, hard constraints, high float
- Every compliance verdict embeds the governing clause reference

---

## Slide 6 — Game-Theoretic Pricing Advantage

**Friedman & Gates bid models solved for the optimal markup.**

- Win-probability curves computed across competitor cost-ratio distributions
- Expected Value (EV = Markup × P_win) maximized to find m*
- Monte Carlo margin simulator: VaR + P10/P50/P90 net profit at proposed price
- Combined-score integration (technical weight W_t vs financial weight W_f)

---

## Slide 7 — Live Infrastructure Demo Case Study

**Highway Corridor 10 Rehabilitation — Ministry of Transport**

| Metric | Result |
|---|---|
| BOQ lines parsed | 5,000 (3 sheets, summary rows excluded) |
| SBC-304 violations flagged | 12 → 0 after remediation |
| VE net savings identified | SAR 42.75M (8.9% of package) |
| DCMA schedule integrity | 4/4 gates passed |
| Compliance score | 91% |

---

## Slide 8 — Financial ROI Projections

**A 12-person estimation team running 15 tenders/year at SAR 250M average value:**

| Line Item | Value |
|---|---|
| Direct labor hours saved / year | 41,400 hours |
| Win-rate uplift (55% → 68%) | +SAR 1.37B additional award value |
| Annual platform cost (cloud) | SAR 1.35M |
| **Net payback period** | **~3.9 months** |

*See `scripts/roi_calculator.py` for the full model.*

---

## Slide 9 — Enterprise Deployment Options

| Dimension | Sovereign On-Premises | Saudi Cloud |
|---|---|---|
| Data residency | 100% in-Kingdom | 100% in-Kingdom (KSA regions) |
| LLM inference | Local Ollama GGUF (air-gapped) | Hybrid cloud + local fallback |
| Compliance | NCA ECC · full audit trail | NCA ECC · full audit trail |
| Control plane | Kubernetes / Helm | Managed K8s + Terraform |

---

## Slide 10 — Security & Cryptographic Assurance

- **AES-256-GCM** encrypted backups; **TLS 1.3** in transit
- **PAdES-LTV** digital signatures with RFC 3161 TSA timestamps
- **DocMDP** permissions block post-signing modification
- Tamper-evident **SHA-256 chained audit log** (blockchain-style)
- QR verification: scan any certified PDF → validate signature + SBC clearance

---

## Slide 11 — Roadmap

| Phase | Scope | Status |
|---|---|---|
| Phase 1 — Alpha | Core engines + SBC gating | ✅ Completed |
| Phase 2 — Beta | Full agentic integration + workspace UI | 🔄 Current |
| Phase 3 — Launch | Multi-tenancy, ERP/Primavera, Etimad/Balady | 📅 Planned |

---

## Slide 12 — Ask & Next Steps

**We seek enterprise pilot sponsorship for two live tenders in the next quarter.**

1. Deploy to a sovereign sandbox with one client package (BOQ + specs + schedule)
2. Benchmark ConTech AI vs the current manual baseline on compliance accuracy and cycle time
3. Agree on rollout to the full pipeline portfolio

---

*Contact: Platform Engineering · ConTech AI*  
*All figures indicative; financial model available in `scripts/roi_calculator.py`.*
