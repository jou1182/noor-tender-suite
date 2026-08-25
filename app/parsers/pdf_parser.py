"""
Technical Specifications PDF Parser.

Extracts text and structured specification sections from PDF documents using
``pypdf`` (fast text pull) with ``pdfplumber`` (table-aware) as the preferred
backend when available.

Outputs:

  - ``extract_text_from_pdf(path)``      — plain text (dependency-free fallback)
  - ``extract_spec_sections(path)``      — structural section chunks
  - ``extract_structural_specs(path)``   — typed concrete/steel parameters
                                            (f'c, exposure, steel grade, cover)
"""

import re
from typing import Any, Dict, List

# --- Dependency-free fallback (kept for RFP parser + minimal environments) ---
import zlib


def _decode_stream(stream: bytes) -> bytes:
    match = re.search(rb"stream\r?\n(.*?)\r?\nendstream", stream, re.DOTALL)
    if not match:
        return stream
    payload = match.group(1)
    # Decompress when FlateDecode is declared OR the payload carries a zlib header.
    if b"FlateDecode" in stream or (payload and payload[:1] == b"\x78"):
        try:
            return zlib.decompress(payload)
        except zlib.error:
            return stream
    return stream


def _unescape_pdf_string(raw: bytes) -> str:
    string_part = raw[raw.find(b"(") + 1 : raw.rfind(b")")] if b"(" in raw else raw
    string_part = string_part.replace(rb"\(", b"(").replace(rb"\)", b")").replace(rb"\\", b"\\")
    try:
        return string_part.decode("latin-1", errors="replace")
    except Exception:
        return ""


def _extract_text_tokens(data: bytes) -> List[str]:
    tokens: List[str] = []
    pattern = re.compile(rb"\((?:\\.|[^()\\])*\)\s*(?:Tj|')|\[(?:[^\[\]]*)\]\s*TJ")
    for match in pattern.finditer(data):
        tokens.append(_unescape_pdf_string(match.group(0)))
    return tokens


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract plain text from a PDF file. Returns '' when unsupported."""
    try:
        with open(pdf_path, "rb") as handle:
            content = handle.read()
    except OSError:
        return ""

    if not content.startswith(b"%PDF"):
        return ""

    pages: List[str] = []
    for obj_match in re.finditer(rb"(\d+)\s+(\d+)\s+obj(.*?)endobj", content, re.DOTALL):
        obj = obj_match.group(3)
        has_stream = bool(re.search(rb"stream\r?\n.*?endstream", obj, re.DOTALL))
        decoded = _decode_stream(obj)
        tokens = _extract_text_tokens(decoded)
        if tokens:
            pages.append(" ".join(tokens))
        elif has_stream:
            # Fallback: streams holding raw/plain text without PDF text operators.
            raw_text = None
            for encoding in ("utf-8", "cp1256", "latin-1"):
                try:
                    candidate = decoded.decode(encoding, errors="replace")
                except Exception:  # noqa: BLE001
                    continue
                printable = sum(1 for ch in candidate if ch.isprintable()) / max(1, len(candidate))
                if candidate.strip() and printable > 0.6:
                    raw_text = candidate
                    break
            if raw_text:
                pages.append(raw_text)
    return "\n".join(pages)


# --- pypdf / pdfplumber backends (preferred) ---


def _pypdf_text(pdf_path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _pdfplumber_tables(pdf_path: str) -> List[List[List[str]]]:
    """Extract raw tables (list of pages, each a list of rows of cells)."""
    import pdfplumber

    tables: List[List[List[str]]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                tables.append([[cell or "" for cell in row] for row in table])
    return tables


def extract_rich_text(pdf_path: str) -> str:
    """Extract text preferring pypdf, falling back to the minimal extractor."""
    try:
        text = _pypdf_text(pdf_path)
        if text and text.strip():
            return text
    except Exception:
        pass
    return extract_text_from_pdf(pdf_path)


# --- Section chunking (rule-based) ---


def _split_sections(text: str) -> List[Dict[str, str]]:
    """
    Chunk spec text into structural sections by heading-like markers:
    numbered headings (e.g. "3.2 Concrete", "Section 5"), ALL-CAPS headings,
    and known keyword headings.
    """
    if not text or not text.strip():
        return []

    heading_re = re.compile(
        r"^\s*(?:"
        r"(?:\d{1,2}(?:\.\d{1,2}){0,2}\s+[A-Z][\w\s\-/()&]*)"   # 3.2 Concrete ...
        r"|(?:Section\s+\d+\s*[:.\-]?\s*[A-Z][\w\s\-/()&]*)"      # Section 5 — ...
        r"|[A-Z][A-Z\s\-/()&]{4,}:?$"                             # CONCRETE WORK:
        r")"
    )

    sections: List[Dict[str, str]] = []
    current: Dict[str, str] | None = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if heading_re.match(line):
            if current:
                sections.append(current)
            current = {"heading": line, "content": ""}
        else:
            if current is None:
                current = {"heading": "Document", "content": ""}
            current["content"] += line + " "

    if current:
        sections.append(current)

    for section in sections:
        section["content"] = section["content"].strip()
    return sections


def extract_spec_sections(pdf_path: str) -> List[Dict[str, str]]:
    """Extract structural spec sections (heading + content chunks)."""
    text = extract_rich_text(pdf_path)
    return _split_sections(text)


# --- Structural parameter extraction (deterministic pattern matching) ---


def _extract_fc(text: str) -> float | None:
    """Concrete grade f'c in MPa — e.g. 'f'c = 35 MPa', 'C35', '35 N/mm²'."""
    match = re.search(r"f['′]?c\s*(?:=|:|=~)?\s*(\d+(?:\.\d+)?)\s*(?:MPa|N/mm2|N/mm²)", text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    match = re.search(r"\bC(\d{2})\b", text)
    if match:
        return float(match.group(1))
    return None


def _extract_wc(text: str) -> float | None:
    """Water/cement ratio — e.g. 'w/c 0.40', 'w/c ratio 0.4'."""
    match = re.search(r"\bw/?c\s*(?:ratio)?\s*(?:=|:|=~)?\s*0?\.(\d+)", text, re.IGNORECASE)
    if match:
        return float("0." + match.group(1))
    return None


def _extract_exposure(text: str) -> str | None:
    """Exposure class — S1..S4 (SBC 304 Table 4.3.1) or descriptive keyword."""
    match = re.search(r"\b(?:Exposure\s+)?(Class\s+)?(S[1-4])\b", text, re.IGNORECASE)
    if match:
        return match.group(2).upper()
    lowered = text.lower()
    if "severe" in lowered or "aggressive" in lowered:
        return "S3"
    if "moderate" in lowered:
        return "S2"
    if "marine" in lowered or "sulfate" in lowered or "sulphate" in lowered:
        return "S3"
    return None


def _extract_steel_grade(text: str) -> float | None:
    """Rebar yield strength fy in MPa — 'Grade 60', 'fy 420 MPa', '420 MPa'."""
    match = re.search(r"\bfy\s*(?:=|:)?\s*(\d{3})\s*MPa", text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    match = re.search(r"\bGrade\s*(60|80)\b", text, re.IGNORECASE)
    if match:
        return 420.0 if match.group(1) == "60" else 550.0
    return None


def _extract_cover(text: str) -> float | None:
    """Minimum concrete cover in mm — 'cover 40 mm', 'cover shall be 50 mm'."""
    match = re.search(r"\b(?:clear\s+)?cover\s*(?:=|:|\s+shall\s+be\s+|\s+is\s+)?\s*(\d+(?:\.\d+)?)\s*mm", text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    match = re.search(r"\b(\d+(?:\.\d+)?)\s*mm\s+(?:clear\s+)?cover", text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def _extract_placement(text: str) -> str | None:
    """Placement context — cast against earth / interior / exterior / submerged."""
    lowered = text.lower()
    if "cast against earth" in lowered or "against earth" in lowered or "on grade" in lowered:
        return "CAST_AGAINST_EARTH"
    if "continuously submerged" in lowered or "submerged" in lowered:
        return "CONTINUOUSLY_SUBMERGED"
    if "interior" in lowered:
        return "INTERIOR"
    if "exterior" in lowered:
        return "EXTERIOR"
    return None


def extract_structural_specs(pdf_path: str) -> Dict[str, Any]:
    """
    Extract structural specification parameters from a technical-specs PDF.

    Returns a dict with keys: fc_mpa, wc, exposure_class, fy_mpa,
    cover_depth_mm, placement_context, source_sections (matched chunks).
    """
    text = extract_rich_text(pdf_path)
    return {
        "fc_mpa": _extract_fc(text),
        "wc": _extract_wc(text),
        "exposure_class": _extract_exposure(text),
        "fy_mpa": _extract_steel_grade(text),
        "cover_depth_mm": _extract_cover(text),
        "placement_context": _extract_placement(text),
        "source_sections": _split_sections(text),
    }
