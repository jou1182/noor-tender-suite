"""Regression guard: no React hooks after early returns.

Root-cause of the client-side exception crash (2026-08-27): NewCompetitionWizard
had `if (!open) return null;` followed by `useState` on line 53.
When `open` flipped true, React saw one MORE hook than the previous render
and threw "Rendered more hooks than during the previous render" — the black
"Application error" screen the user saw when clicking «منافسة جديدة».

This is a STATIC guard: it scans component files for the anti-pattern
(hook call lexically after an early `return null;` at the top level of a
component function) and fails if found. Run with:
    pytest tests/frontend/test_no_conditional_hooks.py -q
"""

from __future__ import annotations

import re
from pathlib import Path

FRONTEND_SRC = Path(__file__).resolve().parents[2] / "frontend" / "src"

HOOK_RE = re.compile(r"\buse(State|Effect|Ref|Memo|Callback|Reducer|Context|LayoutEffect|Id)\s*\(")
EARLY_RETURN_RE = re.compile(r"^\s*if\s*\([^)]*\)\s+return\s+null\s*;?\s*$", re.MULTILINE)


def _find_violations(src_file: Path) -> list[str]:
    text = src_file.read_text(encoding="utf-8", errors="ignore")
    violations: list[str] = []

    # Find every early `return null;` and check hooks AFTER it that are
    # still lexically inside the component (we approximate: hooks on lines
    # after the return that are not inside a nested function/block we parse).
    lines = text.splitlines()
    for m in EARLY_RETURN_RE.finditer(text):
        ret_line = text[: m.start()].count("\n") + 1
        # Look at the following 30 lines for hook calls
        for n in range(ret_line, min(ret_line + 30, len(lines))):
            line = lines[n - 1]
            # stop at the next early return boundary / component end heuristic
            if re.match(r"^\s*}\s*$", line) and n > ret_line + 2:
                break
            if HOOK_RE.search(line) and not line.strip().startswith(("//", "*", "/*")):
                violations.append(
                    f"{src_file.name}:{n}: hook after early return → "
                    f"'{line.strip()[:60]}' (Rules-of-Hooks violation)"
                )
    return violations


class TestNoConditionalHooks:
    def test_no_hooks_after_early_return(self):
        all_violations: list[str] = []
        for tsx in sorted(FRONTEND_SRC.rglob("*.tsx")):
            all_violations.extend(_find_violations(tsx))
        assert not all_violations, "Rules-of-Hooks violations:\n" + "\n".join(all_violations)

    def test_wizard_has_no_hook_after_return(self):
        wizard = FRONTEND_SRC / "components" / "NewCompetitionWizard.tsx"
        text = wizard.read_text(encoding="utf-8")
        # The `if (!open) return null;` must be the LAST statement of the hook
        # section: locate it and assert no `use*` appears before the component's
        # body (we know the bug was a `useState` on the line right after).
        ret_idx = text.index("if (!open) return null;")
        after = text[ret_idx: ret_idx + 2000]
        # Any hook call in the immediate aftermath (before the next `return (`)
        first_jsx = after.find("return (")
        segment = after[: first_jsx if first_jsx > 0 else len(after)]
        assert not HOOK_RE.search(segment), (
            f"NewCompetitionWizard still has a hook after its early return:\n{segment[:200]}"
        )
