"""
Cross-Exam Matrix Engine.

Performs clause-by-clause semantic comparison of RFP clauses against the
contractor's technical proposal sections, producing structured statuses
(COMPLIANT / MINOR_DEVIATION / CRITICAL_GAP), compliance scores, and
actionable remediation text snippets.
"""

import re
from typing import Any, Dict, List

COMPLIANT = "COMPLIANT"
MINOR_DEVIATION = "MINOR_DEVIATION"
CRITICAL_GAP = "CRITICAL_GAP"

STRICTNESS_WEIGHTS: Dict[str, float] = {
    "Mandatory": 1.0,
    "Technical Specification": 0.8,
    "Commercial/Legal": 0.7,
    "Submittal Requirements": 0.6,
    "General": 0.5,
}

# Token heuristics for semantic matching (domain vocabulary shared across RFP + proposal).
STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "for", "in", "on", "with",
    "shall", "must", "may", "will", "be", "is", "are", "was", "were", "by",
    "at", "as", "all", "any", "per", "its", "his", "her", "their", "this",
    "that", "from", "not", "no", "such", "which", "who", "whom", "into",
    "within", "under", "over", "provide", "provided", "including",
    "requirements", "requirement", "comply", "compliance",
}

TOKEN_VARIANTS: Dict[str, List[str]] = {
    "excavation": ["excavat", "earthwork", "trench", "mass grading"],
    "concrete": ["concrete", "rebar", "formwork", "pour"],
    "asphalt": ["asphalt", "paving", "bituminous", "road works"],
    "drainage": ["drainage", "stormwater", "sewer", "pipe network"],
    "structural": ["structural", "steel", "reinforcement", "foundation", "pile"],
    "mep": ["mep", "mechanical", "electrical", "plumbing", "hvac"],
    "safety": ["safety", "hse", "hira", "ppe", "protection", "barricade"],
    "quality": ["quality", "qc", "qa", "inspection", "testing", "itp"],
    "schedule": ["schedule", "programme", "program", "critical path", "baseline"],
    "submittal": ["submittal", "shop drawing", "method statement", "as-built", "report"],
    "payment": ["payment", "invoice", "milestone", "advance payment"],
    "insurance": ["insurance", "policy", "indemnity", "bond", "guarantee"],
    "personnel": ["project manager", "engineer", "superintendent", "qualified", "staffing"],
    "environmental": ["environmental", "environment", "dust", "noise", "sustainability"],
}


class CrossExamMatrixEngine:
    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"[^a-z0-9\s]", " ", text.lower())

    @staticmethod
    def _domain_variants(token: str) -> List[str]:
        token_lower = token.lower()
        if token_lower in TOKEN_VARIANTS:
            return TOKEN_VARIANTS[token_lower]
        return [token_lower]

    @staticmethod
    def _content_tokens(text: str):
        """Extract meaningful tokens, filtering stopwords and pure modality verbs."""
        tokens = set(re.findall(r"[a-z]+", CrossExamMatrixEngine._normalize(text)))
        return {t for t in tokens if t not in STOPWORDS}

    @staticmethod
    def _score_semantic_overlap(clause_text: str, proposal_text: str) -> float:
        """Deterministic semantic similarity: 0.0 (no overlap) to 1.0 (full)."""
        clause_tokens = CrossExamMatrixEngine._content_tokens(clause_text)
        proposal_tokens = CrossExamMatrixEngine._content_tokens(proposal_text)
        if not clause_tokens or not proposal_tokens:
            return 0.0

        # Expand clause tokens through the domain vocabulary.
        expanded: set = set()
        for token in clause_tokens:
            variants = CrossExamMatrixEngine._domain_variants(token)
            expanded.update(variants)

        direct = clause_tokens & proposal_tokens
        overlap = expanded & proposal_tokens
        # 50% credit for variant-expanded matches, full credit for direct matches.
        score = (len(direct) + 0.5 * (len(overlap) - len(direct))) / max(1, len(expanded))
        return score

    @staticmethod
    def _grade(similarity: float, strictness: str, has_any_signal: bool) -> str:
        """Deterministically grade a clause match based on similarity + strictness."""
        if not has_any_signal or similarity < 0.10:
            return CRITICAL_GAP
        threshold = 0.45 if strictness == "Mandatory" else 0.35
        if similarity >= threshold:
            return COMPLIANT
        return MINOR_DEVIATION

    @staticmethod
    def _build_remediation(clause: Dict[str, Any], status: str) -> str:
        """Generate actionable remediation text for non-compliant clauses."""
        ref = clause.get("ref", clause.get("clause_ref", "RFP"))
        if status == COMPLIANT:
            return ""

        if status == CRITICAL_GAP:
            snippet = (
                f"[CRITICAL GAP] RFP {ref} has no matching proposal section. "
                f"Mandatory requirement '{_summarize(clause.get('text', ''))}' is unaddressed — "
                "draft a dedicated proposal section explicitly covering this requirement, "
                "including the compliance standard (e.g. SBC code) and the acceptance criteria."
            )
        else:
            snippet = (
                f"[MINOR DEVIATION] RFP {ref} partially addressed. Enhance the corresponding "
                "proposal section to explicitly reference the requirement wording, "
                "quantify the deliverable, and cite the governing standard."
            )
        return snippet

    @staticmethod
    def compare(clauses: List[Dict[str, Any]], proposal_sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare each RFP clause against the best-matching proposal section.

        Args:
            clauses: Parsed clauses from RfpClauseParser.parse_text()["clauses"].
            proposal_sections: [{"title": ..., "text": ...}, ...]

        Returns:
            Matrix with per-clause results, section coverage, and compliance scoring.
        """
        proposal_texts = [s.get("text", "") or s.get("content", "") for s in proposal_sections]
        proposal_titles = [s.get("title", "") or s.get("section", "") for s in proposal_sections]

        matrix: List[Dict[str, Any]] = []
        for clause in clauses:
            clause_text = clause.get("text", "")
            strictness = clause.get("strictness", "General")
            best_similarity = 0.0
            best_index = -1
            for idx, proposal_text in enumerate(proposal_texts):
                similarity = CrossExamMatrixEngine._score_semantic_overlap(clause_text, proposal_text)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_index = idx

            status = CrossExamMatrixEngine._grade(best_similarity, strictness, best_index >= 0)
            matrix.append(
                {
                    "clause_id": clause.get("clause_id"),
                    "clause_ref": clause.get("ref", clause.get("clause_ref")),
                    "clause_text": clause_text,
                    "strictness": strictness,
                    "sbc_standards": clause.get("sbc_standards", []),
                    "matched_section": proposal_titles[best_index] if best_index >= 0 else None,
                    "match_score": round(best_similarity, 4),
                    "status": status,
                    "remediation": CrossExamMatrixEngine._build_remediation(clause, status),
                }
            )

        return CrossExamMatrixEngine._summarize(matrix)

    @staticmethod
    def _summarize(matrix: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = max(1, len(matrix))
        counts = {COMPLIANT: 0, MINOR_DEVIATION: 0, CRITICAL_GAP: 0}
        weighted = 0.0
        for row in matrix:
            counts[row["status"]] = counts.get(row["status"], 0) + 1
            weight = STRICTNESS_WEIGHTS.get(row.get("strictness", "General"), 0.5)
            weighted += weight * row["match_score"]

        compliance_score = round(weighted / total * 100, 2)
        return {
            "total_clauses": len(matrix),
            "status_counts": counts,
            "compliance_score": compliance_score,
            "mandatory_gap_count": sum(
                1 for row in matrix if row["status"] == CRITICAL_GAP and row.get("strictness") == "Mandatory"
            ),
            "matrix": matrix,
        }


def _summarize(text: str, limit: int = 120) -> str:
    """Short first-clause summary for embedding into remediation text."""
    first_sentence = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)[0]
    return first_sentence if len(first_sentence) <= limit else first_sentence[: limit - 3] + "..."
