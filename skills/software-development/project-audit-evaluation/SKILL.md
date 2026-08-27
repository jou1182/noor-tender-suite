---
name: project-audit-evaluation
description: Audit software projects in 5 phases with scored findings.
version: 0.1.0
author: Youssef Seleim (jou1182), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [audit, evaluation, code-quality, technical-debt]
    related_skills: []
---

# Project Audit and Evaluation Skill

Structured audit for full-stack software projects: repository hygiene, code quality, security, tests, and deployment readiness. Each phase ends with a scored finding — no vague "looks good" outputs. Designed for the terminal tool with no external dependencies beyond Python stdlib.

## When to Use

- Taking over an unfamiliar codebase and needing a baseline report
- Periodic health checks on a project you own (quarterly cadence)
- Pre-release or pre-handover due diligence
- Post-incident review to quantify what broke and why

Don't use for: single-file review (use `read_file` + `patch` directly), or live production monitoring (that is observability, not audit).

## Prerequisites

- Project root path accessible to `terminal`
- Python 3.9+ with stdlib only — no pip installs required
- For Docker-based projects: `docker` CLI reachable

## How to Run

Run the bundled audit script from the project root:

```
terminal(command="python skills/software-development/project-audit-evaluation/scripts/audit_project.py --root . --report docs/audit-report.md", timeout=300)
```

Then review the generated report with `read_file(path="docs/audit-report.md")`.

## Procedure

1. **Run the automated scan.** The script checks: repo hygiene (`.gitignore` coverage, stray binaries), secrets patterns, test presence, Docker config, and documentation. Completion criterion: `docs/audit-report.md` exists with a per-phase score.

2. **Review each phase score manually.** Read the report top-to-bottom; for every finding rated `FAIL`, open the referenced file and confirm the finding is real (scripts produce candidates, humans confirm). Completion criterion: every FAIL has a confirm/refute note.

3. **Prioritize findings.** Classify each confirmed FAIL as `BLOCKER` (ships broken/unsafe), `MAJOR` (visible degradation), or `MINOR` (cleanup). Completion criterion: every finding carries exactly one priority.

4. **Write the remediation plan.** For each BLOCKER: file + line + concrete fix + estimated effort. MAJOR: batch into next sprint. MINOR: list only. Completion criterion: no BLOCKER without a named fix.

5. **Re-run after fixes.** Re-run step 1; the score should improve. Completion criterion: all BLOCKER items closed or explicitly waived by the owner.

## Pitfalls

- **Secrets scan false positives**: placeholder values like `your-key-here` in `.env.example` match secret patterns; the script excludes `*.example` files, but review matches before raising alarms.
- **Test presence ≠ test quality**: a folder full of empty tests counts as "tests exist" in the scan; always run the suite (`pytest`) before believing coverage numbers.
- **Windows path separators**: the script uses `pathlib` throughout, but hand-written shell one-liners in the report examples assume bash; on Windows run them via git-bash.
- **Large repos**: on repos >50k files the scan takes minutes; point `--root` at a subdirectory to iterate faster.

## Verification

- Report file exists and parses (it is plain Markdown)
- Every phase in the report has a numeric score out of 100
- Every FAIL finding cites at least one real file path — spot-check three with `read_file`
- Re-running the script twice in a row produces identical scores (deterministic, no timestamps in scoring)
