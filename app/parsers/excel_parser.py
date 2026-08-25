"""
Excel BOQ Parser.

Extracts bill-of-quantities line items from ``.xlsx`` workbooks using
``openpyxl``/``pandas`` with a dynamic header-detection heuristic:

  - Locates the header row containing [Item No, Description, Unit, Quantity,
    Unit Rate, Total Amount] by fuzzy keyword matching (case/space tolerant).
  - Handles merged header cells and multi-sheet workbooks.
  - Excludes summary / total / subtotal rows (e.g. "Grand Total", "TOTAL",
    "Subtotal", "BALANCE CARRIED").
  - Returns a normalized ``List[Dict[str, Any]]``.
"""

from typing import Any, Dict, List, Optional

import pandas as pd

# Canonical target column -> accepted header aliases (lowercased, spaces removed).
HEADER_ALIASES: Dict[str, List[str]] = {
    "item_no": ["itemno", "item", "no", "item #", "itemid", "ref", "code"],
    "description": ["description", "itemdescription", "particulars", "itemdescriptionandparticulars", "details", "workitem", "itemdescription/details"],
    "unit": ["unit", "uom", "measurementunit", "measure", "units"],
    "qty": ["quantity", "qty", "quantity.", "totalqty", "amountqty", "qty."],
    "unit_rate": ["unitrate", "rate", "unitprice", "price", "price/unit", "rate(usd)", "unitcost", "rateperunit", "priceperunit"],
    "total_amount": ["totalamount", "amount", "total", "amount(sar)", "totalcost", "cost", "extension", "total(amount)"],
}

# Row markers that indicate summary/total rows to exclude.
SUMMARY_KEYWORDS = (
    "total", "subtotal", "grand total", "balance carried", "carried forward",
    "carried to", "b/f", "c/f", "summary", "carried over",
)


def _norm(value: Any) -> str:
    """Normalize a cell value for keyword matching."""
    if value is None:
        return ""
    return str(value).strip().lower().replace(" ", "").replace("_", "").replace("-", "")


def _norm_header(value: Any) -> str:
    """Normalize a header cell for alias matching."""
    if value is None:
        return ""
    return str(value).strip().lower().replace(" ", "")


def detect_header_row(sheet) -> int:
    """
    Scan the first 20 rows of a worksheet for the header row matching the most
    BOQ column aliases. Returns the 0-indexed row, or -1 if none found.
    """
    best_row = -1
    best_score = 0
    for row_idx in range(min(20, sheet.max_row)):
        row_values = [sheet.cell(row=row_idx + 1, column=col).value for col in range(1, sheet.max_column + 1)]
        normalized = [_norm_header(v) for v in row_values]
        score = 0
        for canonical, aliases in HEADER_ALIASES.items():
            if any(alias in normalized for alias in aliases):
                score += 1
        if score > best_score:
            best_score = score
            best_row = row_idx
    return best_row if best_score >= 3 else -1


def _build_column_map(sheet, header_row: int) -> Dict[str, int]:
    """Map canonical column names to 1-indexed sheet columns."""
    col_map: Dict[str, int] = {}
    for col in range(1, sheet.max_column + 1):
        value = _norm_header(sheet.cell(row=header_row + 1, column=col).value)
        if not value:
            continue
        for canonical, aliases in HEADER_ALIASES.items():
            if value in aliases and canonical not in col_map:
                col_map[canonical] = col
                break

    # A standalone "Item" header (often merged over the description span) is the
    # description column when no explicit description header exists. In read-only
    # mode merged metadata is unavailable, so description is inferred as the column
    # immediately following the item_no column when its header cell is empty.
    if "description" not in col_map:
        item_col = col_map.get("item_no")
        if item_col is not None:
            item_header = _norm_header(sheet.cell(row=header_row + 1, column=item_col).value)
            next_col = item_col + 1
            if item_header in ("item", "itemno") and next_col <= sheet.max_column:
                next_header = _norm_header(sheet.cell(row=header_row + 1, column=next_col).value)
                if not next_header:
                    col_map["description"] = next_col
        if "description" not in col_map:
            for col in range(1, sheet.max_column + 1):
                if _norm_header(sheet.cell(row=header_row + 1, column=col).value) == "item":
                    col_map["description"] = col
                    break
    return col_map


def _is_summary_row(values: List[Any]) -> bool:
    """True if a data row looks like a summary/total/subtotal row."""
    joined = " ".join(_norm(v) for v in values)
    return any(kw in joined for kw in SUMMARY_KEYWORDS)


def _parse_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = str(value).replace(",", "").replace(" ", "").replace("SAR", "").replace("USD", "")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def extract_boq_from_workbook(workbook_path: str) -> List[Dict[str, Any]]:
    """Extract normalized BOQ line items from an .xlsx workbook (all sheets)."""
    sheets = pd.ExcelFile(workbook_path).sheet_names
    items: List[Dict[str, Any]] = []
    for sheet_name in sheets:
        items.extend(extract_boq_from_sheet(workbook_path, sheet_name))
    return items


def extract_boq_from_sheet(workbook_path: str, sheet_name: str) -> List[Dict[str, Any]]:
    """
    Extract normalized BOQ line items from a single worksheet.

    Returns a list of dicts with keys:
      item_no, description, unit, qty, unit_rate, total_amount, sheet
    """
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("openpyxl is required for Excel BOQ parsing") from exc

    wb = load_workbook(workbook_path, read_only=True, data_only=True)
    try:
        sheet = wb[sheet_name]
        header_row = detect_header_row(sheet)
        if header_row < 0:
            return []

        col_map = _build_column_map(sheet, header_row)
        if "description" not in col_map:
            return []

        rows: List[Dict[str, Any]] = []
        for row_idx in range(header_row + 2, sheet.max_row + 1):
            values = [sheet.cell(row=row_idx, column=col).value for col in range(1, sheet.max_column + 1)]
            if _is_summary_row(values):
                continue
            desc = values[col_map["description"] - 1] if col_map["description"] - 1 < len(values) else None
            if desc is None or _norm(desc) == "":
                continue

            def get(canonical: str):
                col = col_map.get(canonical)
                if col is None or col - 1 >= len(values):
                    return None
                return values[col - 1]

            qty = _parse_float(get("qty"))
            unit_rate = _parse_float(get("unit_rate"))
            total_amount = _parse_float(get("total_amount"))
            # Fallback: derive total from qty * unit_rate when a total column is missing.
            if get("total_amount") is None and qty and unit_rate:
                total_amount = round(qty * unit_rate, 2)

            rows.append(
                {
                    "item_no": str(get("item_no") or "").strip(),
                    "description": str(desc).strip(),
                    "unit": str(get("unit") or "").strip(),
                    "qty": qty,
                    "unit_rate": unit_rate,
                    "total_amount": total_amount,
                    "sheet": sheet_name,
                }
            )
        return rows
    finally:
        wb.close()


def extract_boq_from_buffer(buffer: bytes) -> List[Dict[str, Any]]:
    """Extract BOQ line items from an in-memory .xlsx buffer."""
    import io

    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(buffer), read_only=True, data_only=True)
    items: List[Dict[str, Any]] = []
    try:
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            header_row = detect_header_row(sheet)
            if header_row < 0:
                continue
            col_map = _build_column_map(sheet, header_row)
            if "description" not in col_map:
                continue
            for row_idx in range(header_row + 2, sheet.max_row + 1):
                values = [sheet.cell(row=row_idx, column=col).value for col in range(1, sheet.max_column + 1)]
                if _is_summary_row(values):
                    continue
                desc = values[col_map["description"] - 1] if col_map["description"] - 1 < len(values) else None
                if desc is None or _norm(desc) == "":
                    continue

                def get(canonical: str):
                    col = col_map.get(canonical)
                    if col is None or col - 1 >= len(values):
                        return None
                    return values[col - 1]

                qty = _parse_float(get("qty"))
                unit_rate = _parse_float(get("unit_rate"))
                total_amount = _parse_float(get("total_amount"))
                if get("total_amount") is None and qty and unit_rate:
                    total_amount = round(qty * unit_rate, 2)

                items.append(
                    {
                        "item_no": str(get("item_no") or "").strip(),
                        "description": str(desc).strip(),
                        "unit": str(get("unit") or "").strip(),
                        "qty": qty,
                        "unit_rate": unit_rate,
                        "total_amount": total_amount,
                        "sheet": sheet_name,
                    }
                )
    finally:
        wb.close()
    return items
