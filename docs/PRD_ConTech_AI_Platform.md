# Product Requirements Document (PRD): ConTech AI Platform

## 1. Overview
The ConTech AI Platform is an enterprise-grade multi-agent orchestration system designed to automate the rigorous auditing of infrastructure construction tenders. By cross-examining Request for Proposals (RFP), Method Statements, Primavera P6 Schedules, and Bills of Quantities (BOQ), the platform accelerates tender evaluation while ensuring strict adherence to engineering standards.

## 2. System Architecture
The platform is built on a full-stack containerized architecture:
- **Frontend**: Next.js 15, Tailwind CSS, providing a responsive drag-and-drop dashboard.
- **Backend API**: FastAPI, orchestrating background jobs and realtime Server-Sent Events (SSE) telemetry.
- **Agent Orchestrator**: LangGraph, managing state transitions across multiple sub-agents.
- **Knowledge Base**: Qdrant Vector DB, enabling hybrid semantic retrieval of engineering standards.
- **Persistence**: PostgreSQL, storing structured compliance gaps, technical scores, and audit metadata.

## 3. Multi-Agent Evaluation Workflows
The platform leverages a specialized suite of autonomous agents, including:
- **RFP Deconstructor**: Extracts critical constraints and client requirements.
- **Methodology Auditor**: Assesses contractor method statements against safety and engineering codes.
- **P6 Schedule Auditor**: Parses `.xer` files to evaluate schedule logic and integrity.
- **QA/QC & HSE Agent**: Enforces health, safety, and quality thresholds.
- **Red Team Agent**: Simulates a competitor/auditor cross-examination, outputting vulnerability severities and drafting Request for Information (RFI) letters.
- **Synthesis Scoring**: Aggregates all findings into a unified Technical Score out of 100%.

## 4. Engineering Standards & Compliance Gates
### 4.1 DCMA 14-Point Assessment
The P6 Schedule Auditor strictly enforces the Defense Contract Management Agency (DCMA) 14-point schedule assessment, identifying high negative float, missing logic ties, hard constraints, and invalid dates to prevent milestone slippage.

### 4.2 SBC / FIDIC Compliance
Through hybrid retrieval, the Methodology Auditor automatically queries the vector knowledge base to map contractor proposed statements to the **Saudi Building Code (SBC)** (e.g., SBC-303 Foundations, SBC-304 Concrete) and **FIDIC Red Book** standard conditions of contract. Citations are embedded directly into the generated gap analysis.
