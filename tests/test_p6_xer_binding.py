import pytest

from app.agents.errors import InsufficientInputError
from app.agents.p6_dcma_agent import p6_dcma_agent
from app.parsers.xer_schedule_adapter import build_activities, load_schedule


def _metric(out, name):
    return next(m for m in out["p6_output"]["dcma_results"]["metrics"] if name in m["check"])


def test_adapter_maps_xer_to_dcma_activities(xer_file):
    acts = {a["id"]: a for a in build_activities(load_schedule(xer_file))}
    assert set(acts) == {"1", "2", "3", "4", "5"}  # completed task excluded
    assert acts["3"]["lag"] == -2.0
    assert acts["4"]["total_float"] == 60.0
    assert acts["4"]["constraint_type"] == "Must Finish On"
    assert acts["5"]["predecessors"] == [] and acts["5"]["successors"] == []


def test_dcma_reflects_the_real_file(xer_file):
    out = p6_dcma_agent({"schedule_file": xer_file})
    assert _metric(out, "Logic")["value_pct"] == pytest.approx(20.0)      # 1 of 5 orphaned
    assert _metric(out, "Negative Lags")["value_pct"] == pytest.approx(20.0)
    assert _metric(out, "High Float")["value_pct"] == pytest.approx(20.0)
    assert _metric(out, "Hard Constraints")["value_pct"] == pytest.approx(20.0)
    assert out["p6_output"]["dcma_results"]["overall_status"] == "FAILED"


def test_monte_carlo_uses_critical_chain_durations(xer_file):
    out = p6_dcma_agent({"schedule_file": xer_file})["p6_output"]
    summary = out["schedule_summary"]
    assert summary["critical_chain_activities"] == 3  # tasks 1,2,3 have zero float
    # scheduled chain = (240+480+960)/8 = 210 days; P50 must sit between 0.8x and 1.5x of it
    assert 210 * 0.8 < out["monte_carlo"]["p50_days"] < 210 * 1.5
    assert out["monte_carlo"]["p50_days"] <= out["monte_carlo"]["p80_days"] <= out["monte_carlo"]["p90_days"]


@pytest.mark.parametrize("state", [{}, {"schedule_file": ""}, {"schedule_file": "/no/such.xer"}])
def test_missing_schedule_fails_loudly(state):
    with pytest.raises(InsufficientInputError):
        p6_dcma_agent(state)


def test_schedule_without_durations_cannot_simulate(tmp_path):
    f = tmp_path / "s.xer"
    f.write_text("%T\tTASK\n%F\ttask_id\ttask_name\n%R\t1\tA\n%R\t2\tB\n", encoding="utf-8")
    with pytest.raises(InsufficientInputError):
        p6_dcma_agent({"schedule_file": str(f)})
