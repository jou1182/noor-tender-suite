import re

from app.parsers.rfp_clause_parser import RfpClauseParser, normalize_ar

HEADER = "المملكة العربية السعودية\nأمانة المنطقة الشرقية\nClassification: Public - عام\n"


def _pages(*bodies):
    """Simulate PDF extraction: a running header + page marker on every page."""
    return "\f".join(f"{HEADER}رقم الصفحة\n{i + 1} من {len(bodies)}\n{b}" for i, b in enumerate(bodies))


RFP = _pages(
    "الفهرس\nتعريفات ........................................ 4\nالغرامات ........................ 9\n",
    "القسم الأول: نطاق العمل\n"
    "• يجب على المقاول تنفيذ الأعمال وفقاً للمواصفات المعتمدة.\n"
    "• علىالمقاول تقديم خطة السلامة قبل بدء الأعمال.\n"
    "• تتم المراجعة الدورية للموقع.\n",
    "القسم الثاني: الغرامات\n"
    "• غرامة التأخير ٠٫٥٪ عن كل يوم بحد أقصى ١٠٪ من قيمة العقد.\n"
    "• في حالة فرد الأسفلت على شقوق غير معالجة غرامة 500 ريال / متر طولي.\n"
    "• على المقاول توفير مهندس مدني لا تقل خبرته عن خبرة 10 سنوات.\n"
    "• يطبق ASTM D 6927 و AASHTO T 166 على خلطات الأسفلت.\n",
    "• يجبر الموظف على الإجازة.\n",
)


def _parse():
    return RfpClauseParser.parse_text(RFP)


def _find(parsed, fragment):
    return next(c for c in parsed["clauses"] if fragment in c["text"])


def test_page_boilerplate_and_toc_are_removed():
    text = " ".join(c["text"] for c in _parse()["clauses"])
    assert "أمانة المنطقة الشرقية" not in text
    assert "Classification" not in text
    assert "........" not in text
    assert not re.search(r"\d+ من \d+", text)


def test_arabic_modals_make_requirements_and_ignore_longer_words():
    parsed = _parse()
    assert _find(parsed, "يجب على المقاول")["is_requirement"]
    assert _find(parsed, "خطة السلامة")["is_requirement"]          # glued "علىالمقاول"
    assert not _find(parsed, "المراجعة الدورية")["is_requirement"]
    assert not _find(parsed, "يجبر الموظف")["is_requirement"]      # يجبر != يجب


def test_bullets_become_separate_clauses_with_arabic_strictness():
    parsed = _parse()
    assert _find(parsed, "يجب على المقاول")["strictness"] == "Technical Specification"
    assert _find(parsed, "خطة السلامة")["strictness"] == "Submittal Requirements"
    assert _find(parsed, "غرامة التأخير")["strictness"] == "Commercial/Legal"
    assert parsed["compliance_gates"]["requirement_count"] == 3


def test_penalty_gates_percent_cap_and_money_per_unit():
    parsed = _parse()
    late = _find(parsed, "غرامة التأخير")["penalty_gate"]
    assert late["detected"] and late["cap_pct"] == 10.0 and late["rate_pct"] == 0.5
    fixed = _find(parsed, "500 ريال")["penalty_gate"]
    assert fixed["amount_sar"] == 500.0 and "متر" in fixed["per_unit"]


def test_personnel_experience_in_years_and_referenced_standards():
    parsed = _parse()
    pers = _find(parsed, "مهندس مدني")["personnel_requirements"]
    assert any(r["type"] == "experience" and "10" in r["requirement"] for r in pers)
    assert parsed["compliance_gates"]["referenced_standards"] == ["AASHTO T 166", "ASTM D 6927"]


def test_non_requirement_text_is_not_flagged_personnel():
    parsed = RfpClauseParser.parse_text("القسم الأول\n• تعريفات: الفني هو الشخص المسؤول عن الفحص.\n")
    assert parsed["compliance_gates"]["personnel_requirements_total"] == 0


def test_normalize_ar():
    assert normalize_ar("٠١٢") == "012"
    assert normalize_ar("أإآ") == "ااا"


def test_english_behaviour_unchanged():
    p = RfpClauseParser.parse_text(
        "Clause 1: All works shall comply with SBC 304 for concrete.\n"
        "Clause 2: Liquidated damages capped at 10% of the contract value."
    )
    assert p["compliance_gates"]["sbc_standards"] == ["304"]
    assert p["clauses"][0]["is_requirement"] and p["clauses"][0]["strictness"] == "Mandatory"
    assert p["compliance_gates"]["penalty_thresholds"][0]["detected"]


def test_presentation_forms_are_repaired_before_parsing():
    from app.parsers.arabic_text import fix_presentation_forms

    shaped = "ﻳﺠﺐ ﻋﻠﻰ ﺍﻟﻤﻘﺎﻭﻝ ﺗﻘﺪﻳﻢ ﺧﻄﺔ ﺍﻟﺴﻼﻣﺔ"
    assert fix_presentation_forms(shaped) == "يجب على المقاول تقديم خطة السلامة"
    assert fix_presentation_forms("clean text") == "clean text"
    parsed = RfpClauseParser.parse_text("• " + shaped + " قبل البدء.")
    assert parsed["clauses"][0]["is_requirement"]
    assert "المقاول" in parsed["clauses"][0]["text"]


def test_oversized_unnumbered_segment_is_split_into_sentences():
    para = "\n".join(f"يجب على المقاول الالتزام بالشرط رقم {i} من هذه الوثيقة بالكامل." for i in range(60))
    parsed = RfpClauseParser.parse_text(para)
    assert len(parsed["clauses"]) > 10
    assert all(len(c["text"]) <= 1500 for c in parsed["clauses"])
    assert all(c["is_requirement"] for c in parsed["clauses"])


def test_rfp_agent_merges_new_gate_fields_across_documents(tmp_path):
    from app.agents.client_rfp_agent import client_rfp_agent

    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_text("• يجب على المقاول تقديم خطة السلامة.\n• يطبق ASTM D 6927 على الخلطات.\n", encoding="utf-8")
    b.write_text("• علىالمقاول توفير مهندس خبرة 10 سنوات.\n", encoding="utf-8")
    gates = client_rfp_agent({"rfp_documents": [str(a), str(b)]})["rfp_output"]["compliance_gates"]
    assert gates["requirement_count"] == 2
    assert gates["referenced_standards"] == ["ASTM D 6927"]
