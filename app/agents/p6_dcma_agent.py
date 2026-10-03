import os
from typing import Any, Dict

from app.agents.errors import InsufficientInputError
from app.parsers.dcma_engine import DCMAEngine
from app.parsers.monte_carlo_engine import MonteCarloEngine
from app.parsers.xer_schedule_adapter import (
    HOURS_PER_DAY,
    OPTIMISTIC_FACTOR,
    PESSIMISTIC_FACTOR,
    build_activities,
    build_critical_chain,
    load_schedule,
)

MC_ITERATIONS = 5000


def p6_dcma_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """DCMA integrity checks + Monte Carlo duration risk over the *uploaded* XER schedule.

    State keys consumed: schedule_file (path to a Primavera P6 .xer).
    State keys produced: p6_output { dcma_results, monte_carlo, schedule_summary }.
    Raises InsufficientInputError when the schedule is missing/unreadable — no demo network.
    """
    path = state.get("schedule_file") or ""
    if not path or not os.path.isfile(path):
        raise InsufficientInputError("لا يوجد ملف جدول زمني (XER) صالح للتحليل. / No readable XER schedule file.")

    activities = build_activities(load_schedule(path))
    if not activities:
        raise InsufficientInputError("ملف XER لا يحتوي أنشطة قابلة للتحليل. / The XER file has no analysable activities.")

    dcma_results = DCMAEngine.evaluate_14_point(activities)

    chain = build_critical_chain(activities)
    if not chain["activities"]:
        raise InsufficientInputError(
            "أنشطة XER بلا مدد (remain/target_drtn_hr_cnt) — لا يمكن إجراء محاكاة مونت كارلو. "
            "/ XER activities carry no durations; Monte Carlo cannot run."
        )
    mc_results = MonteCarloEngine.run_simulation(chain["activities"], iterations=MC_ITERATIONS)

    return {
        "p6_output": {
            "dcma_results": dcma_results,
            "monte_carlo": mc_results,
            "schedule_summary": {
                "source_file": os.path.basename(path),
                "activities_analysed": len(activities),
                "critical_chain_basis": chain["basis"],
                "critical_chain_activities": len(chain["activities"]),
                "assumptions": {
                    "hours_per_day": HOURS_PER_DAY,
                    "optimistic_factor": OPTIMISTIC_FACTOR,
                    "pessimistic_factor": PESSIMISTIC_FACTOR,
                    "iterations": MC_ITERATIONS,
                },
            },
        }
    }
