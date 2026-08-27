"""Tests for project-audit-evaluation skill — stdlib + pytest only, no network."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "software-development" / "project-audit-evaluation"
SCRIPT = SKILL_DIR / "scripts" / "audit_project.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("audit_project", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["audit_project"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestFrontmatter:
    def test_yaml_frontmatter_valid(self):
        content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        assert content.startswith("---")
        end = content.index("\n---\n", 3)
        fm = yaml.safe_load(content[4:end])
        assert fm["name"] == "project-audit-evaluation"

    def test_description_within_hardline_limit(self):
        content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        end = content.index("\n---\n", 3)
        fm = yaml.safe_load(content[4:end])
        desc = fm["description"]
        assert len(desc) <= 60, f"description is {len(desc)} chars, hardline is 60"
        assert desc.endswith("."), "description must end with a period"

    def test_required_frontmatter_fields(self):
        content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        end = content.index("\n---\n", 3)
        fm = yaml.safe_load(content[4:end])
        for field in ("name", "description", "version", "author", "license", "platforms"):
            assert field in fm, f"missing frontmatter field: {field}"
        assert fm["version"].count(".") == 2, "version must be semver"
        assert set(fm["platforms"]) <= {"linux", "macos", "windows"}

    def test_no_leaked_conversation_text(self):
        """Regression: an earlier draft leaked chat narration into the body."""
        content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        for marker in ("I need to check", "Let me first check", "I'll create"):
            assert marker not in content, f"leaked narration found: {marker!r}"

    def test_no_phantom_related_skills(self):
        """Regression: earlier draft referenced skills that don't exist in this repo."""
        content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        end = content.index("\n---\n", 3)
        fm = yaml.safe_load(content[4:end])
        related = fm.get("metadata", {}).get("hermes", {}).get("related_skills", [])
        repo_root = Path(__file__).resolve().parents[2]
        for name in related:
            matches = list(repo_root.glob(f"skills/**/{name}/SKILL.md")) + list(
                repo_root.glob(f"optional-skills/**/{name}/SKILL.md")
            )
            assert matches, f"related skill not in repo: {name}"


class TestAuditScript:
    def test_script_exists_and_compiles(self):
        assert SCRIPT.exists()
        compile(SCRIPT.read_text(encoding="utf-8"), str(SCRIPT), "exec")

    def test_clean_project_scores_high(self, tmp_path):
        mod = _load_module()
        (tmp_path / ".gitignore").write_text(".env\n__pycache__\nnode_modules\n")
        (tmp_path / "README.md").write_text(
            "# Project\n\n## Install\npip install -r requirements.txt\n\n## Run\npython app.py\n\n## Architecture\nlayered\n"
        )
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_app.py").write_text("def test_ok():\n    assert 1 + 1 == 2\n")
        (tmp_path / "Dockerfile").write_text("FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\n")

        report = mod.build_report(tmp_path)
        assert "Overall — 9" in report or "Overall — 10" in report  # 90+
        assert "FAIL" not in report

    def test_dirty_project_scores_low(self, tmp_path):
        mod = _load_module()
        # No .gitignore, no README, no tests, no docker → all phases suffer
        report = mod.build_report(tmp_path)
        assert "Overall — " in report
        assert "FAIL" in report

    def test_secret_detection(self, tmp_path):
        mod = _load_module()
        # Build the fake key at runtime so THIS test file never matches the scan itself.
        fake_key = "sk-" + "1" * 32
        (tmp_path / "config.py").write_text(f'API_KEY = "{fake_key}"\n')
        (tmp_path / ".env.example").write_text("OPENAI_API_KEY=your-key-here\n")  # excluded
        score, findings = mod.phase_secrets(tmp_path)
        assert score < 100, "one secret hit must reduce score"
        assert any("config.py" in msg for _, msg in findings)
        assert not any(".env.example" in msg for _, msg in findings)

    def test_deterministic_scores(self, tmp_path):
        mod = _load_module()
        (tmp_path / "README.md").write_text("# x\n")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_a.py").write_text("assert True\n")
        s1, _ = mod.phase_tests(tmp_path)
        s2, _ = mod.phase_tests(tmp_path)
        assert s1 == s2, "scores must be deterministic across runs"

    def test_trivial_tests_flagged(self, tmp_path):
        mod = _load_module()
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_empty.py").write_text("print('no assertions here')\n")
        score, findings = mod.phase_tests(tmp_path)
        assert score == 20
        assert any("zero assertions" in msg for _, msg in findings)
