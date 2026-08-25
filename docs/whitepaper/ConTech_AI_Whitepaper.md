# ConTech AI Platform: Enterprise Architecture Whitepaper

## 1. Executive Summary
The **ConTech AI Platform** is a master-level autonomous engineering and orchestration suite designed specifically for heavy civil, infrastructure, and commercial megaprojects (e.g., NEOM, Aramco, Qiddiya). By migrating from deterministic, single-threaded software into an autonomous **Multi-Agent LangGraph Swarm**, the platform radically compresses the bidding and technical proposal lifecycle from months to minutes, mathematically guaranteeing strict compliance with international engineering and legal baselines (FIDIC, SBC, ASTM, DCMA).

## 2. Multi-Agent Orchestration (LangGraph Topology)
The system operates on a state-machine architecture powered by **LangGraph**. A shared `OrchestrationState(TypedDict)` propagates through 20 specialized, domain-expert agent nodes. 

### Core Agent Nodes:
- **Client RFP & BOQ Parsers**: High-speed RegEx clustering extracts thousands of lines into normalized structures.
- **Geotech & Engineering Math**: Executes empirical validations.
- **QA/QC & HSE (ITP/HIRA)**: Synthesizes operational constraints.
- **P6 Schedule (DCMA)**: Conducts network logic mapping.
- **Arbitrator & Red Team**: Provides adversarial cross-examination of the generated proposal against historical disqualification data (Qdrant).

The Fan-Out / Fan-In graph topology ensures absolute chronological processing, passing the enriched dictionary state seamlessly down the assembly line.

## 3. Mathematical & Empirical Validation Engines
Unlike standard LLMs that hallucinate math, ConTech AI utilizes deterministic Python parsers:
*   **Geotechnical & Structural Integrity**: Validates soil bearing capacity against Saudi Building Code (SBC-303/304). 
*   **Hydraulics**: Applies the Manning Equation to storm-water systems.
*   **Cost & S-Curve Array Generation**: Vectorizes baseline time-phased cost allocations, detecting aggressive front-loading bidding strategies via early/late cash-flow plotting.

## 4. DCMA 14-Point & Monte Carlo Network Diagnostics
Oracle Primavera P6 networks are inherently vulnerable to human manipulation. The **P6 DCMA Agent**:
1.  Audits schedule integrity against the Defense Contract Management Agency (DCMA) 14-point framework (flagging Negative Lags, High Float > 44 days, Hard Constraints, and Missing Logic).
2.  Executes a **NumPy Vectorized Monte Carlo Simulator**, running 5,000 probabilistic iterations across the critical chain to statistically isolate the true P80/P90 project completion confidence intervals.

## 5. Security & Cryptographic Integrity Sealing
In high-stakes commercial tendering, strict legal auditability is required. 
The **Dossier Assembler** node aggregates the final state graph. The **Cryptographic Sealer** then processes the payload, generating a deterministic, immutable **SHA-256 Master Signature**. If a single character is manipulated in the Master Export post-generation, the hash fails verification, ensuring absolute tamper-proof legal protection.
