"""Adapts a parsed Primavera P6 XER into the inputs of the DCMA and Monte Carlo engines.

Only data present in the file is used. P6 stores durations/floats/lags in hours;
they are converted to days with ``HOURS_PER_DAY`` (the P6 default 8h calendar).
"""

from typing import Any, Dict, List, Optional

import pandas as pd

from app.parsers.xer_parser import XERParser

HOURS_PER_DAY = 8.0
# Three-point spread applied to the *scheduled* duration of each critical activity.
# The XER holds one duration per task, so uncertainty is an explicit assumption.
OPTIMISTIC_FACTOR = 0.8
PESSIMISTIC_FACTOR = 1.5
MAX_CHAIN_FALLBACK = 10

_HARD_CONSTRAINTS = {
    "CS_MANDSTART": "Must Start On",
    "CS_MSO": "Must Start On",
    "CS_MANDFIN": "Must Finish On",
    "CS_MEO": "Must Finish On",
}
_EXCLUDED_TASK_TYPES = {"TT_WBS", "TT_LOE"}


def _num(value: Any) -> Optional[float]:
    try:
        text = str(value).strip()
        return float(text) if text else None
    except (TypeError, ValueError):
        return None


def _col(df: pd.DataFrame, *names: str) -> Optional[str]:
    return next((n for n in names if n in df.columns), None)


def load_schedule(path: str) -> Dict[str, pd.DataFrame]:
    parser = XERParser(path)
    return parser.parse()


def build_activities(tables: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
    """Return DCMA activity dicts (id, predecessors, successors, lag, total_float, constraint_type, ...)."""
    tasks = tables.get("TASK")
    if tasks is None or tasks.empty or "task_id" not in tasks.columns:
        return []

    preds = tables.get("TASKPRED", pd.DataFrame())
    succ_col = _col(preds, "succ_task_id", "task_id") if not preds.empty else None
    pred_col = _col(preds, "pred_task_id") if not preds.empty else None
    lag_col = _col(preds, "lag_hr_cnt") if not preds.empty else None

    predecessors: Dict[str, List[str]] = {}
    successors: Dict[str, List[str]] = {}
    min_lag: Dict[str, float] = {}
    if succ_col and pred_col:
        for _, rel in preds.iterrows():
            p, s = str(rel[pred_col]), str(rel[succ_col])
            predecessors.setdefault(s, []).append(p)
            successors.setdefault(p, []).append(s)
            lag = _num(rel[lag_col]) if lag_col else None
            if lag is not None:
                min_lag[s] = min(min_lag.get(s, lag), lag)

    float_col = _col(tasks, "total_float_hr_cnt")
    type_col = _col(tasks, "task_type")
    status_col = _col(tasks, "status_code")
    cstr_col = _col(tasks, "cstr_type")
    dur_col = _col(tasks, "remain_drtn_hr_cnt", "target_drtn_hr_cnt")
    name_col = _col(tasks, "task_name")

    activities: List[Dict[str, Any]] = []
    for _, row in tasks.iterrows():
        if type_col and str(row[type_col]) in _EXCLUDED_TASK_TYPES:
            continue
        if status_col and str(row[status_col]) == "TK_Complete":
            continue
        tid = str(row["task_id"])
        flt = _num(row[float_col]) if float_col else None
        dur = _num(row[dur_col]) if dur_col else None
        activities.append(
            {
                "id": tid,
                "name": str(row[name_col]) if name_col else tid,
                "predecessors": predecessors.get(tid, []),
                "successors": successors.get(tid, []),
                "lag": (min_lag.get(tid, 0.0)) / HOURS_PER_DAY,
                "total_float": (flt / HOURS_PER_DAY) if flt is not None else 0.0,
                "has_float": flt is not None,
                "duration_days": (dur / HOURS_PER_DAY) if dur is not None else None,
                "constraint_type": _HARD_CONSTRAINTS.get(str(row[cstr_col]), "As Soon As Possible") if cstr_col else "As Soon As Possible",
            }
        )
    return activities


def build_critical_chain(activities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Three-point inputs for the critical activities (float <= 0), else the longest ones."""
    timed = [a for a in activities if a.get("duration_days")]
    critical = [a for a in timed if a["has_float"] and a["total_float"] <= 0]
    basis = "critical_path_float<=0"
    chain = critical
    if not chain:
        chain = sorted(timed, key=lambda a: a["duration_days"], reverse=True)[:MAX_CHAIN_FALLBACK]
        basis = f"longest_{MAX_CHAIN_FALLBACK}_activities (no zero-float tasks in XER)"
    return {
        "basis": basis,
        "activities": [
            {
                "name": a["name"],
                "optimistic": a["duration_days"] * OPTIMISTIC_FACTOR,
                "most_likely": a["duration_days"],
                "pessimistic": a["duration_days"] * PESSIMISTIC_FACTOR,
            }
            for a in chain
        ],
    }
