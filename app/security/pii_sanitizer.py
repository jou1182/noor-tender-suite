"""
PII Sanitizer Engine.

Masks sensitive contractor data before any external LLM invocation, and
provides two-way entity token replacement so authorized downstream engines can
de-anonymize locally. Enforces Saudi NCA data-protection compliance.

Masking rules:
  - Commercial Registration numbers (CR-xxxxxxxxxx) -> [CR_NUM_n]
  - Saudi IBAN bank accounts (SAxx ...)             -> [IBAN_n]
  - Phone numbers (Saudi +966 / 05xx formats)       -> [PHONE_n]
  - Unit margins / proprietary rates                -> [MARGIN_VAL_n]
"""

import re
from typing import Dict, Tuple

CR_PATTERN = re.compile(r"\b(?:CR|C\.R\.?)[-:\s]?(\d{6,10})\b", re.IGNORECASE)
IBAN_PATTERN = re.compile(r"\bSA\d{2}\s?(?:\d{4}\s?){4}\d{2}\b")
PHONE_PATTERN = re.compile(r"\b(?:\+?966|0)5\d{8}\b")
MARGIN_PATTERN = re.compile(r"(?:margin|markup)\s*[:=]?\s*(?:SAR\s*)?([\d,]+(?:\.\d+)?)", re.IGNORECASE)


class PIISanitizer:
    """Deterministic PII masking with reversible entity token mapping."""

    def __init__(self) -> None:
        self._registry: Dict[str, str] = {}  # token -> original
        self._counters: Dict[str, int] = {}

    def _token(self, kind: str, original: str) -> str:
        self._counters[kind] = self._counters.get(kind, 0) + 1
        token = f"[{kind}_{self._counters[kind]}]"
        self._registry[token] = original
        return token

    def sanitize(self, text: str) -> str:
        """Replace sensitive entities with reversible tokens."""
        self._counters = {}

        def cr_repl(m: re.Match) -> str:
            return self._token("CR_NUM", m.group(0))

        def iban_repl(m: re.Match) -> str:
            return self._token("IBAN", m.group(0).replace(" ", ""))

        def phone_repl(m: re.Match) -> str:
            return self._token("PHONE", m.group(0))

        def margin_repl(m: re.Match) -> str:
            return self._token("MARGIN_VAL", m.group(0))

        text = CR_PATTERN.sub(cr_repl, text)
        text = IBAN_PATTERN.sub(iban_repl, text)
        text = PHONE_PATTERN.sub(phone_repl, text)
        text = MARGIN_PATTERN.sub(margin_repl, text)
        return text

    def deanonymize(self, text: str) -> str:
        """Restore original entities from tokens (local, authorized engines only)."""
        for token, original in self._registry.items():
            text = text.replace(token, original)
        return text

    def registry(self) -> Dict[str, str]:
        return dict(self._registry)
