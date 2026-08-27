#!/usr/bin/env python3
"""Project audit scanner — deterministic, stdlib-only, no network.

Usage:
    python audit_project.py --root . --report docs/audit-report.md

Phases (each scored 0-100):
  1. Repo hygiene     — .gitignore, stray artifacts
  2. Secrets          — pattern scan (excludes *.example, *.md)
  3. Tests            — presence + non-trivial assertions
  4. Deployment       — Dockerfile/compose presence and sanity
  5. Documentation    — README currency and coverage

Output: Markdown report with per-phase score and file-cited findings.
Deterministic: no timestamps in scoring, same tree -> same scores.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- helpers

SECRET_PATTERNS = [
    re.compile(r"(sk-[A-Za-z0-9]{20,})"),                       # OpenAI-style
    re.compile(r"(AKIA[0-9A-Z]{16})"),                          # AWS access key
    re.compile(r"(-----BEGIN (RSA |EC )?PRIVATE KEY-----)"),    # private key block
    re.compile(r"(?i)(api[_-]?key\s*[:=]\s*['\"])([A-Za-z0-9]{16,})(['\"])"),
]
SECRET_EXCLUDE_SUFFIXES = (".example", ".md", ".txt", ".lock", ".pyc")
SECRET_EXCLUDE_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".next"}

TEST_DIRS = {"tests", "test", "spec"}
TEST_FILES = ("test_*.py", "*_test.py", "*.spec.ts", "*.test.ts", "*.test.js")

DOCKER_FILES = ("Dockerfile", "docker-compose.yml", "compose.yml")


def iter_code_files(root: Path):
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SECRET_EXCLUDE_DIRS for part in p.parts):
            continue
        yield p


# ---------------------------------------------------------------- phases

def phase_repo_hygiene(root: Path) -> tuple[int, list[str]]:
    findings: list[str] = []
    score = 100

    gitignore = root / ".gitignore"
    if not gitignore.exists():
        score -= 40
        findings.append(("FAIL", f"No .gitignore at project root: {root}"))
    else:
        gi = gitignore.read_text(encoding="utf-8", errors="ignore")
        for needed in (".env", "__pycache__", "node_modules"):
            if needed not in gi:
                score -= 10
                findings.append(("FAIL", f".gitignore missing entry: {needed}"))

    # stray artifacts that should never be committed
    heavy = [p for p in root.rglob("*") if p.is_file() and p.suffix in {".db", ".sqlite", ".sqlite3", ".mp4"}
             and ".git" not in p.parts and "node_modules" not in p.parts and ".venv" not in p.parts]
    if heavy:
        score -= 15
        names = ", ".join(str(p.relative_to(root)) for p in heavy[:5])
        findings.append(("MAJOR", f"Binary/db artifacts present in tree: {names}"))

    readme = root / "README.md"
    if not readme.exists() and not (root / "readme.md").exists():
        score -= 20
        findings.append(("FAIL", "No README at project root"))
    return max(0, score), findings


def phase_secrets(root: Path) -> tuple[int, list[str]]:
    findings: list[str] = []
    hits = 0
    for p in iter_code_files(root):
        if p.suffix.lower() in SECRET_EXCLUDE_SUFFIXES:
            continue
        if p.stat().st_size > 2_000_000:  # skip >2MB files
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat in SECRET_PATTERNS:
            m = pat.search(text)
            if m:
                hits += 1
                findings.append(("FAIL", f"Possible secret in {p.relative_to(root)} (pattern: {pat.pattern[:40]}…)"))
                break
    score = max(0, 100 - hits * 30)
    if hits == 0:
        findings.append(("PASS", "No secret patterns matched"))
    return score, findings


def phase_tests(root: Path) -> tuple[int, list[str]]:
    findings: list[str] = []
    test_files = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SECRET_EXCLUDE_DIRS for part in p.parts):
            continue
        rel = str(p.relative_to(root)).replace("\\", "/")
        if any(f"/{d}/" in f"/{rel}/" for d in TEST_DIRS):
            test_files.append(p)
        elif any(p.match(pat) for pat in TEST_FILES):
            test_files.append(p)

    if not test_files:
        return 0, [("FAIL", "No test files found anywhere in the tree")]

    trivial = 0
    for tf in test_files[:500]:
        try:
            text = tf.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        asserts = len(re.findall(r"\bassert\b|\bexpect\(|\bshould\b", text))
        if asserts == 0:
            trivial += 1

    total = len(test_files)
    if trivial == total:
        score, verdict = 20, ("FAIL", f"All {total} test files have zero assertions")
    elif trivial > 0:
        score, verdict = 70, ("MAJOR", f"{trivial}/{total} test files contain no assertions")
    else:
        score, verdict = 95, ("PASS", f"{total} test files, all with assertions")
    findings.append(verdict)
    return score, findings


def phase_deployment(root: Path) -> tuple[int, list[str]]:
    findings: list[str] = []
    present = [f for f in DOCKER_FILES if (root / f).exists()]
    if not present:
        return 40, [("MAJOR", "No Dockerfile or compose file found — deployment story unknown")]

    score = 70
    dockerfile = root / "Dockerfile"
    if dockerfile.exists():
        text = dockerfile.read_text(encoding="utf-8", errors="ignore")
        if "FROM" not in text:
            findings.append(("FAIL", "Dockerfile has no FROM instruction"))
            score -= 30
        if "latest" in text.split("FROM")[-1].splitlines()[0]:
            findings.append(("MAJOR", "Dockerfile FROM uses floating tag 'latest'"))
            score -= 10
        else:
            findings.append(("PASS", "Dockerfile pinned base image"))
    for comp in ("docker-compose.yml", "compose.yml"):
        cf = root / comp
        if cf.exists():
            findings.append(("PASS", f"{comp} present"))
            score = min(100, score + 15)
            break
    return max(0, min(100, score)), findings


def phase_docs(root: Path) -> tuple[int, list[str]]:
    findings: list[str] = []
    readme = None
    for name in ("README.md", "readme.md", "Readme.md"):
        if (root / name).exists():
            readme = root / name
            break
    if readme is None:
        return 0, [("FAIL", "No README — onboarding depends entirely on tribal knowledge")]

    text = readme.read_text(encoding="utf-8", errors="ignore")
    score = 60
    checks = [
        ("install/setup instructions", re.compile(r"(?i)(install|setup|getting started)")),
        ("run instructions", re.compile(r"(?i)(run|start|launch|serve)")),
        ("architecture section", re.compile(r"(?i)(architecture|structure|layout)")),
    ]
    for label, pat in checks:
        if pat.search(text):
            score += 12
            findings.append(("PASS", f"README covers {label}"))
        else:
            findings.append(("MINOR", f"README missing {label}"))
            score -= 5
    return max(0, min(100, score)), findings


# ---------------------------------------------------------------- report

PHASES = [
    ("Repo Hygiene", phase_repo_hygiene),
    ("Secrets", phase_secrets),
    ("Tests", phase_tests),
    ("Deployment", phase_deployment),
    ("Documentation", phase_docs),
]

PRIORITY_ORDER = {"FAIL": "BLOCKER", "MAJOR": "MAJOR", "MINOR": "MINOR", "PASS": None}


def build_report(root: Path) -> str:
    lines = ["# Project Audit Report", "", f"Root: `{root.resolve()}`", ""]
    total = 0
    all_findings: list[tuple[str, str]] = []

    for name, fn in PHASES:
        score, findings = fn(root)
        total += score
        lines.append(f"## {name} — {score}/100")
        lines.append("")
        for sev, msg in findings:
            lines.append(f"- **{sev}**: {msg}")
            if sev != "PASS":
                all_findings.append((sev, msg))
        lines.append("")

    overall = round(total / len(PHASES))
    lines.append(f"## Overall — {overall}/100")
    lines.append("")
    blockers = [f for f in all_findings if f[0] == "FAIL"]
    majors = [f for f in all_findings if f[0] == "MAJOR"]
    minors = [f for f in all_findings if f[0] == "MINOR"]
    lines.append(f"- Blockers (failed checks): {len(blockers)}")
    lines.append(f"- Major: {len(majors)}")
    lines.append(f"- Minor: {len(minors)}")
    if blockers:
        lines.append("")
        lines.append("**Remediate before any release.** Each FAIL needs a named fix in the remediation plan.")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic project audit scanner")
    ap.add_argument("--root", default=".", help="Project root to audit")
    ap.add_argument("--report", default="docs/audit-report.md", help="Output report path")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"ERROR: root does not exist: {root}", file=sys.stderr)
        return 2

    report = build_report(root)
    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"Report written: {out}")
    # Print summary to stdout too
    print("\n".join(report.splitlines()[-8:]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
