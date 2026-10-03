"""
RFP Clause Parsing Engine (English + Arabic).

Ingests raw RFP text (or a PDF path) and:
  1. Cleans extraction noise: running page headers/footers, table-of-contents
     dot-leader lines, "N من M" page markers, Arabic-Indic digits.
  2. Segments clauses (numbered items, Arabic section headings, bullets) and
     classifies strictness:
       - Mandatory
       - Technical Specification
       - Commercial/Legal
       - Submittal Requirements
     plus ``is_requirement`` (a binding modal such as shall/must/يجب/على المقاول).
  3. Identifies critical compliance gates:
       - SBC / referenced-standard citations (SBC, ASTM, AASHTO, ISO, SASO ...)
       - Key personnel qualification requirements
       - Penalty / liquidated damages thresholds (absolute amount or % of contract)
"""

import re
from collections import Counter
from typing import Any, Dict, List

from app.parsers.arabic_text import fix_presentation_forms
from app.parsers.pdf_parser import extract_text_from_pdf

STRICTNESS = "strictness"
CLAUSE_TEXT = "text"
CLAUSE_REF = "ref"
CLAUSE_ID = "clause_id"
SECTION = "section"

# ---------------------------------------------------------------- Arabic ---

_ARABIC_DIGITS = str.maketrans({**{ord(a): b for a, b in zip("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")}, 0x066B: ".", 0x066A: "%"})
_DIACRITICS_TATWEEL = re.compile("[ً-ٰٟـ]")
_ALEF_YA = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي"})
_AR = "ء-ي"  # Arabic letter range (hamza .. ya)


def normalize_ar(text: str) -> str:
    """Digits to ASCII, strip diacritics/tatweel, unify alef/ya — for matching only."""
    return _DIACRITICS_TATWEEL.sub("", text.translate(_ARABIC_DIGITS)).translate(_ALEF_YA)


def _ar(*words: str) -> str:
    """Regex alternation for Arabic words/phrases (already-normalised spelling).

    Allows conjunction/preposition prefixes (و ف ب ل ك, and ل+ال -> لل), tolerates
    missing spaces inside phrases (PDF extraction glues words: "علىالمقاول"), and
    refuses to match inside a longer word (so ``يجب`` does not fire on ``يجبر``).
    """
    alts = []
    for w in words:
        w = normalize_ar(w)
        alts.append(re.escape(w).replace(r"\ ", r"\s*"))
        if w.startswith("ال") and len(w) > 3:
            alts.append("لل" + re.escape(w[2:]).replace(r"\ ", r"\s*"))
    body = "|".join(alts)
    return rf"(?<![{_AR}])(?:و|ف)?(?:[بلك])?(?:{body})(?![{_AR}])"


# Domain-specific strictness categories are checked before the generic
# mandatory modality keywords so a clause keeps its domain classification
# (e.g. "must submit a method statement" -> Submittal Requirements).
STRICTNESS_RULES: List[Dict[str, Any]] = [
    {
        "strictness": "Technical Specification",
        "patterns": [
            r"\btechnical\s+specification\b",
            r"\bspecification\b",
            r"\bdesign\s+criteria\b",
            r"\bconform(?:s|ance)?\s+to\b",
            r"\bper\s+(?:the\s+)?(?:latest|applicable)?\s*standard",
            r"\bstandards?\b",
            r"\bmaterial(?:s)?\s+(?:shall|must|to)\b",
            _ar("المواصفات", "مواصفات", "المواصفه", "المعايير", "معايير", "المعيار", "الكود", "كود",
                "الاختبارات", "اختبارات", "فحص", "الفحوصات", "المواد", "جودة", "ضبط الجودة"),
        ],
    },
    {
        "strictness": "Commercial/Legal",
        "patterns": [
            r"\bcommercial\b",
            r"\blegal\b",
            r"\bcontract\b",
            r"\bliability\b",
            r"\bindemnif",
            r"\binsurance\b",
            r"\bliquidated\s+damages\b",
            r"\bpenalty\b",
            r"\bbond\b",
            r"\bpayment\b",
            r"\bguarantee\b",
            r"\bwarranty\b",
            r"\bdamages\b",
            _ar("غرامة", "غرامات", "الغرامة", "الغرامات", "ضمان", "الضمان", "الضمانات", "كفالة", "تامين",
                "التامين", "عقد", "العقد", "دفعة", "الدفعات", "سداد", "مستخلص", "المستخلصات", "ضريبة",
                "الضريبة", "تعويض", "التعويض", "تعويضات", "سعر", "الاسعار", "الأسعار", "فسخ", "انهاء العقد"),
        ],
    },
    {
        "strictness": "Submittal Requirements",
        "patterns": [
            r"\bsubmittal\b",
            r"\bsubmission\b",
            r"\bsubmit\b",
            r"\bshop\s+drawings?\b",
            r"\bmethod\s+statement\b",
            r"\bprogramme\b",
            r"\bschedule\b",
            r"\bdeliverable(?:s)?\b",
            r"\breport(?:s)?\b",
            _ar("تقديم", "يقدم", "تقدم", "ارفاق", "يرفق", "المستندات", "مستندات", "الخطة", "خطة",
                "الجدول الزمني", "جدول زمني", "مخططات", "المخططات", "رسومات تنفيذية", "تقرير", "التقارير",
                "تقارير", "شهادة", "شهادات", "الشهادات", "طريقة التنفيذ", "منهجية", "عينات"),
        ],
    },
    {
        "strictness": "Mandatory",
        "patterns": [
            r"\bshall\b",
            r"\bmust\b",
            r"\bmandatory\b",
            r"\bshall not\b",
            r"\bis required\b",
            r"\bits mandatory\b",
            _ar("يجب", "يلزم", "يلتزم", "ملزم", "الزامي", "الزاميه", "يتعين", "ينبغي", "يشترط", "يحظر",
                "لا يجوز", "يتعهد", "على المقاول", "على المتنافس", "على مقدم العرض", "يتوجب"),
        ],
    },
]

# A clause is a *requirement* when it carries a binding modal.
_REQUIREMENT_PATTERN = re.compile(
    "|".join(
        [
            r"\bshall\b", r"\bmust\b", r"\bis required\b", r"\bmandatory\b", r"\bshall not\b",
            _ar("يجب", "يلزم", "يلتزم", "ملزم", "الزامي", "يتعين", "ينبغي", "يشترط", "يحظر", "لا يجوز",
                "يتعهد", "على المقاول", "على المتنافس", "على مقدم العرض", "يتوجب"),
        ]
    )
)

# Compliance gate extraction rules (independent of strictness).
SBC_STANDARD_PATTERN = re.compile(r"\bSBC\s*(?:-\s*)?(\d{3}(?:[A-Z])?(?:/\d+)?)\b", re.IGNORECASE)
# Other referenced standards frequent in road/building RFPs (ASTM D 6927, AASHTO T 166, ISO 9001 ...).
REFERENCED_STANDARD_PATTERN = re.compile(
    r"\b(ASTM|AASHTO|ISO|SASO|SSA|BS\s?EN|EN|ACI|AISC|AWS|API|NFPA)\s*-?\s*([A-Z]?\s?\d{1,5}(?:[-/]\d{1,4})?[A-Z]?)\b"
)

PERSONNEL_KEYWORDS = (
    "qualification",
    "qualified",
    "certified",
    "credentials",
    "years of experience",
    "professional engineer",
    "registered engineer",
    "licensed",
    "project manager",
    "hse officer",
    "safety officer",
    "civil engineer",
)
_PERSONNEL_AR = re.compile(
    _ar("مهندس", "المهندس", "مهندسين", "المهندسين", "مؤهلات", "المؤهلات", "خبرة", "الخبرة", "خبرات",
        "مدير المشروع", "مدير مشروع", "مسؤول السلامة", "مسؤول سلامة", "فريق العمل", "طاقم العمل",
        "ترخيص", "مرخص")
)
_PENALTY_EN = re.compile(
    r"penalty|liquidated damages|delay damages|\bld\b|per day|per week|% of the contract|\bcap\b"
)
_PENALTY_AR = re.compile(_ar("غرامة", "غرامات", "الغرامة", "الغرامات", "غرامة التاخير", "جزاء", "الجزاءات", "جزاءات"))
_TOC_DOTS = re.compile(r"[.…·]{4,}")
_PAGE_MARK = re.compile(r"^\s*\d+\s*(?:من|of|/)\s*\d+\s*$", re.IGNORECASE)
MAX_CLAUSE_CHARS = 1500
MIN_SENTENCE_CHUNK = 120
_BULLET = r"[•●▪■◦•●−–—\-]"


def _penalty_present(lowered_norm: str) -> bool:
    return bool(_PENALTY_EN.search(lowered_norm) or _PENALTY_AR.search(lowered_norm))


def _clean_extraction_noise(raw_text: str) -> str:
    """Drop running headers/footers, page markers and table-of-contents lines."""
    pages = raw_text.split("\f")
    n_pages = len(pages)

    def key(line: str) -> str:
        return re.sub(r"\d+", "#", re.sub(r"\s+", " ", normalize_ar(line)).strip().lower())

    boilerplate = set()
    if n_pages >= 4:
        seen: Counter = Counter()
        for page in pages:
            for k in {key(l) for l in page.splitlines() if l.strip()}:
                seen[k] += 1
        threshold = max(3, int(0.3 * n_pages))
        boilerplate = {k for k, c in seen.items() if c >= threshold and len(k) > 3}

    kept: List[str] = []
    for page in pages:
        for line in page.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if _TOC_DOTS.search(stripped) or _PAGE_MARK.match(normalize_ar(stripped)):
                continue
            if key(stripped) in boilerplate:
                continue
            kept.append(stripped)
        kept.append("")  # keep a blank between pages
    return "\n".join(kept)


class RfpClauseParser:
    @staticmethod
    def _split_clauses(raw_text: str) -> List[str]:
        """Split RFP text into individual clause strings."""
        if not raw_text or not raw_text.strip():
            return []

        text = raw_text.strip()
        # Boundaries: numbered clauses ("3.2.1", "10."), "Section/Clause 5", UPPERCASE: headings,
        # Arabic section headings (القسم/الباب/المادة/البند ...) and bullet items.
        clause_boundary = re.compile(
            r"(?m)(?=^\s*(?:\d{1,2}(?:\.\d{1,2}){0,3}\.?\s+"
            r"|(?:Section|Clause|Article|CL)\s*\d+(?:[\.\-]\d+)*\b"
            r"|[A-Z][A-Z\s]{4,}:"
            r"|(?:القسم|الباب|الفصل|المادة|البند|الماده)\s+[^\n]{1,40}"
            rf"|{_BULLET}\s+))"
        )
        parts = [p.strip() for p in clause_boundary.split(text) if p and p.strip()]
        # Drop fragments with almost no letters (stray numbers/punctuation).
        parts = [p for p in parts if sum(ch.isalpha() for ch in p) >= 8]
        parts = [piece for p in parts for piece in RfpClauseParser._split_oversized(p)]
        return parts if parts else [text]

    @staticmethod
    def _split_oversized(segment: str) -> List[str]:
        """Unnumbered documents yield huge segments; split them at sentence-ending line breaks."""
        if len(segment) <= MAX_CLAUSE_CHARS:
            return [segment]
        pieces: List[str] = []
        current = ""
        for line in segment.splitlines():
            line = line.strip()
            if not line:
                continue
            current = f"{current}\n{line}" if current else line
            ends_sentence = re.search(r"[.!?؟؛:]\s*$", line) is not None
            if (ends_sentence and len(current) >= MIN_SENTENCE_CHUNK) or len(current) >= MAX_CLAUSE_CHARS // 2:
                pieces.append(current)
                current = ""
        if current:
            pieces.append(current)
        return [p for p in pieces if sum(ch.isalpha() for ch in p) >= 8]

    @staticmethod
    def _classify_strictness(clause_text: str) -> str:
        lowered = normalize_ar(clause_text.lower())
        for rule in STRICTNESS_RULES:
            for pattern in rule["patterns"]:
                if re.search(pattern, lowered):
                    return rule["strictness"]
        return "General"

    @staticmethod
    def _is_requirement(clause_text: str) -> bool:
        return bool(_REQUIREMENT_PATTERN.search(normalize_ar(clause_text.lower())))

    @staticmethod
    def _extract_sbc_standards(clause_text: str) -> List[str]:
        return sorted({m.group(1).upper() for m in SBC_STANDARD_PATTERN.finditer(clause_text)})

    @staticmethod
    def _extract_referenced_standards(clause_text: str) -> List[str]:
        return sorted({f"{m.group(1).replace(' ', '')} {m.group(2).strip()}" for m in REFERENCED_STANDARD_PATTERN.finditer(clause_text)})

    @staticmethod
    def _extract_penalty_threshold(clause_text: str) -> Dict[str, Any]:
        """Extract penalty / liquidated damages thresholds (rate and cap)."""
        gate: Dict[str, Any] = {"detected": False}
        norm = normalize_ar(clause_text)
        if not _penalty_present(norm.lower()):
            return gate

        gate["detected"] = True
        rate_match = re.search(
            r"(?:sar|sr|usd|us\$|\$)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:per\s+day|per\s+week|/day|/week)",
            norm,
            re.IGNORECASE,
        )
        if rate_match:
            gate["rate"] = float(rate_match.group(1).replace(",", ""))

        cap_match = re.search(
            r"(?:capped?\s+at|maximum|max|not\s+to\s+exceed|limit(?:ed)?\s+to)\s*(?:sar|sr|usd|us\$|\$)?\s*"
            r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?)",
            norm,
            re.IGNORECASE,
        )
        if cap_match:
            gate["cap"] = float(cap_match.group(1).replace(",", ""))

        # Arabic: "غرامة ... 0.1% ... عن كل يوم" / "بحد أقصى 10% من قيمة العقد"
        ar_cap = re.search(r"(?:بحد اقصي|بحد اقصى|حد اقصي|الحد الاقصي|لا\s*(?:تتجاوز|تزيد|تتعدي))[^%\d]{0,40}(\d+(?:\.\d+)?)\s*%", norm)
        if ar_cap:
            gate["cap_pct"] = float(ar_cap.group(1))
        ar_rate = re.search(r"(\d+(?:\.\d+)?)\s*%[^.\n]{0,60}?(?:عن كل|لكل|في اليوم|يوميا|عن كل يوم)", norm) or \
            re.search(r"(?:عن كل|لكل)\s+(?:يوم|اسبوع)[^%\d]{0,40}(\d+(?:\.\d+)?)\s*%", norm)
        if ar_rate:
            gate["rate_pct"] = float(ar_rate.group(1))
        pct_contract = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:of the contract|من قيمة العقد|من قيمه العقد)", norm, re.IGNORECASE)
        if pct_contract and "cap_pct" not in gate:
            gate["cap_pct"] = float(pct_contract.group(1))

        sar = re.search(r"(\d[\d,]*(?:\.\d+)?)\s*(?:ريال|ر\.س|sar|sr)(?:\s*(?:/|لكل|عن كل)\s*([^\s.,،]+(?:\s+[^\s.,،]+)?))?", norm, re.IGNORECASE)
        if sar and "rate" not in gate:
            gate["amount_sar"] = float(sar.group(1).replace(",", ""))
            if sar.group(2):
                gate["per_unit"] = sar.group(2).strip()

        if not any(k in gate for k in ("rate", "cap", "rate_pct", "cap_pct", "amount_sar")):
            gate["note"] = "Penalty mechanism present without numeric threshold."
        return gate

    @staticmethod
    def _extract_personnel_requirements(clause_text: str) -> List[Dict[str, str]]:
        norm = normalize_ar(clause_text)
        lowered = norm.lower()
        arabic_hit = _PERSONNEL_AR.search(lowered) and RfpClauseParser._is_requirement(clause_text)
        if not (any(kw in lowered for kw in PERSONNEL_KEYWORDS) or arabic_hit):
            return []
        requirements: List[Dict[str, str]] = []
        exp_match = re.search(r"(\d+)\s*\+?\s*years?\s+of\s+experience", norm, re.IGNORECASE)
        if exp_match:
            requirements.append(
                {"type": "experience", "requirement": f"{exp_match.group(1)}+ years of experience"}
            )
        else:
            ar_exp = re.search(r"(?:خبره|خبرة)[^.\n]{0,40}?(\d+)\s*(?:سنه|سنة|سنوات|عاما|اعوام|عام)", norm) or \
                re.search(r"(\d+)\s*(?:سنه|سنة|سنوات|عاما|اعوام|عام)[^.\n]{0,20}?(?:خبره|خبرة)", norm)
            if ar_exp:
                requirements.append({"type": "experience", "requirement": f"{ar_exp.group(1)}+ سنوات خبرة / years of experience"})
        cert_match = re.search(r"(?:certified|licensed|registered)\s+([\w\s\-]+?)(?=\.|;|,|\band\b)", clause_text, re.IGNORECASE)
        if cert_match:
            requirements.append({"type": "certification", "requirement": cert_match.group(1).strip().title()})
        if not requirements:
            requirements.append({"type": "general", "requirement": "Key personnel qualification provision."})
        return requirements

    @staticmethod
    def parse_text(raw_text: str) -> Dict[str, Any]:
        """Parse raw RFP text into structured, strictness-segmented clauses."""
        clauses: List[Dict[str, Any]] = []
        sbc_count = 0
        penalties: List[Dict[str, Any]] = []

        cleaned = _clean_extraction_noise(fix_presentation_forms(raw_text)) if raw_text else raw_text
        for idx, clause_text in enumerate(RfpClauseParser._split_clauses(cleaned), start=1):
            standards = RfpClauseParser._extract_sbc_standards(clause_text)
            penalty_gate = RfpClauseParser._extract_penalty_threshold(clause_text)
            personnel = RfpClauseParser._extract_personnel_requirements(clause_text)

            if standards:
                sbc_count += len(standards)
            if penalty_gate.get("detected"):
                penalties.append({"clause_id": idx, **penalty_gate})

            clauses.append(
                {
                    CLAUSE_ID: idx,
                    CLAUSE_REF: f"RFP-C{idx}",
                    CLAUSE_TEXT: clause_text,
                    STRICTNESS: RfpClauseParser._classify_strictness(clause_text),
                    "is_requirement": RfpClauseParser._is_requirement(clause_text),
                    SECTION: RfpClauseParser._detect_section(clause_text),
                    "sbc_standards": standards,
                    "referenced_standards": RfpClauseParser._extract_referenced_standards(clause_text),
                    "personnel_requirements": personnel,
                    "penalty_gate": penalty_gate,
                }
            )

        return {
            "clauses": clauses,
            "segment_summary": RfpClauseParser._segment_summary(clauses),
            "compliance_gates": {
                "sbc_standards": sorted({s for c in clauses for s in c["sbc_standards"]}),
                "sbc_citations_total": sbc_count,
                "referenced_standards": sorted({s for c in clauses for s in c["referenced_standards"]}),
                "requirement_count": sum(1 for c in clauses if c["is_requirement"]),
                "personnel_requirements_total": sum(len(c["personnel_requirements"]) for c in clauses),
                "penalty_thresholds": penalties,
                "critical_gate_count": sum(1 for c in clauses if c["sbc_standards"] or c["penalty_gate"].get("detected") or c["personnel_requirements"]),
            },
        }

    @staticmethod
    def _detect_section(clause_text: str) -> str:
        lowered = normalize_ar(clause_text.lower())
        if "scope of work" in lowered or "scope" in lowered or re.search(_ar("نطاق العمل", "نطاق الاعمال"), lowered):
            return "Scope of Work"
        if "payment" in lowered or "commercial" in lowered or "bond" in lowered or "insurance" in lowered or \
                re.search(_ar("الدفعات", "سداد", "ضمان", "الضمان", "تامين", "التامين", "غرامة", "الغرامات", "مستخلص"), lowered):
            return "Commercial"
        if "submittal" in lowered or "submission" in lowered or "report" in lowered or \
                re.search(_ar("تقديم", "المستندات", "تقرير", "التقارير", "ارفاق"), lowered):
            return "Submittals"
        if "technical" in lowered or "specification" in lowered or "material" in lowered or \
                re.search(_ar("المواصفات", "مواصفات", "المواد", "الاختبارات", "معايير"), lowered):
            return "Technical"
        return "General"

    @staticmethod
    def _segment_summary(clauses: List[Dict[str, Any]]) -> Dict[str, int]:
        summary: Dict[str, int] = {}
        for clause in clauses:
            strictness = clause[STRICTNESS]
            summary[strictness] = summary.get(strictness, 0) + 1
        return summary

    @staticmethod
    def parse_pdf(pdf_path: str) -> Dict[str, Any]:
        """Parse an RFP PDF by extracting text then delegating to parse_text."""
        text = extract_text_from_pdf(pdf_path)
        return RfpClauseParser.parse_text(text)
