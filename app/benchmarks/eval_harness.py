"""
Model Evaluation Harness.

Loads golden ground-truth test cases (BOQ parsing, SBC-304 durability, FIDIC
liability), queries target model endpoints concurrently (cloud + local
Ollama/LM Studio), and scores structural accuracy (exact numeric match on SBC
limits), extraction F1, inference latency (TTFT), and throughput (tokens/sec).
"""

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional

from app.schemas.eval_benchmark import (
    BenchmarkTestCase,
    ComparativeLeaderboard,
    ModelPerformanceRecord,
)

# A model "client" is a callable(prompt) -> {"content": str, "usage": {...}}
ModelClient = Callable[[str], Dict[str, Any]]


def load_golden_cases() -> List[BenchmarkTestCase]:
    """Built-in golden test cases across the three task domains."""
    return [
        BenchmarkTestCase(
            case_id="SBC-1",
            task_type="SBC_304",
            prompt="What is the minimum f'c for S2 exposure class concrete per SBC 304?",
            expected_output="31",
            numeric_checks=[{"field": "min_fc", "expected": 31.0}],
        ),
        BenchmarkTestCase(
            case_id="SBC-2",
            task_type="SBC_304",
            prompt="What is the maximum w/c ratio for S3 severe exposure?",
            expected_output="0.40",
            numeric_checks=[{"field": "max_wc", "expected": 0.40}],
        ),
        BenchmarkTestCase(
            case_id="SBC-3",
            task_type="SBC_304",
            prompt="Minimum clear cover for exterior columns (SBC 304 Sec 7.7)?",
            expected_output="40",
            numeric_checks=[{"field": "min_cover", "expected": 40.0}],
        ),
        BenchmarkTestCase(
            case_id="BOQ-1",
            task_type="BOQ_EXTRACTION",
            prompt="Extract from 'Item 2.1 Ready-mix Concrete 35MPa, qty 1000 m3 @ 350 SAR' the qty and unit rate.",
            expected_output="1000,350",
        ),
        BenchmarkTestCase(
            case_id="FIDIC-1",
            task_type="FIDIC_RISK",
            prompt="Under FIDIC Red Book, what is the standard LD cap percentage?",
            expected_output="10",
        ),
    ]


def _extract_numeric(text: str) -> List[float]:
    """Pull all float numbers from model output for numeric comparison."""
    return [float(m) for m in re.findall(r"-?\d+(?:\.\d+)?", text)]


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def score_case(case: BenchmarkTestCase, output_text: str) -> Dict[str, float]:
    """
    Score one model output against a golden case.

    Returns dict with: exact_match (1.0 if expected string contained),
    numeric_match (fraction of numeric checks satisfied), f1 (token F1).
    """
    exact = 1.0 if case.expected_output.lower() in output_text.lower() else 0.0

    numeric_ok = 0
    for check in case.numeric_checks:
        expected = float(check["expected"])
        if any(abs(v - expected) < 1e-6 for v in _extract_numeric(output_text)):
            numeric_ok += 1
    numeric_match = numeric_ok / len(case.numeric_checks) if case.numeric_checks else 1.0

    # Token F1 between expected and output.
    exp_tokens = set(_tokenize(case.expected_output))
    out_tokens = set(_tokenize(output_text))
    if not exp_tokens:
        f1 = 1.0
    else:
        overlap = exp_tokens & out_tokens
        precision = len(overlap) / len(out_tokens) if out_tokens else 0.0
        recall = len(overlap) / len(exp_tokens)
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {"exact_match": exact, "numeric_match": numeric_match, "f1": f1}


class ModelEvaluationHarness:
    """Concurrent model benchmark runner."""

    def __init__(self, cases: Optional[List[BenchmarkTestCase]] = None) -> None:
        self.cases = cases if cases is not None else load_golden_cases()

    def evaluate_client(
        self, model_name: str, provider: str, endpoint: str, client: ModelClient
    ) -> ModelPerformanceRecord:
        """Run all golden cases against a client and aggregate scores."""
        total_exact = 0.0
        total_numeric = 0.0
        total_f1 = 0.0
        latencies: List[float] = []
        total_tokens = 0
        passed = 0

        for case in self.cases:
            start = time.perf_counter()
            response = client(case.prompt)
            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)

            output = response.get("content", "")
            usage = response.get("usage", {}) or {}
            total_tokens += int(usage.get("total_tokens", usage.get("completion_tokens", 0)) or 0)

            scores = score_case(case, output)
            total_exact += scores["exact_match"]
            total_numeric += scores["numeric_match"]
            total_f1 += scores["f1"]
            if scores["exact_match"] == 1.0:
                passed += 1

        n = len(self.cases)
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        total_seconds = (sum(latencies) / 1000.0) if latencies else 0.0

        return ModelPerformanceRecord(
            model_name=model_name,
            provider=provider,
            endpoint=endpoint,
            accuracy=round(total_exact / n * 100, 2) if n else 0.0,
            f1_score=round(total_f1 / n, 4) if n else 0.0,
            numeric_exact_match=round(total_numeric / n * 100, 2) if n else 0.0,
            avg_latency_ms=round(avg_latency, 2),
            tokens_per_second=round(total_tokens / total_seconds, 2) if total_seconds else 0.0,
            cost_per_1k_tokens_usd=0.0,
            total_cases=n,
            passed_cases=passed,
        )

    def run_parallel(
        self, targets: List[Dict[str, Any]], max_workers: int = 4
    ) -> ComparativeLeaderboard:
        """Evaluate multiple model clients concurrently."""
        records: List[ModelPerformanceRecord] = []

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(
                    self.evaluate_client,
                    t["model_name"],
                    t.get("provider", "cloud"),
                    t.get("endpoint", ""),
                    t["client"],
                ): t["model_name"]
                for t in targets
            }
            for future in as_completed(futures):
                try:
                    records.append(future.result())
                except Exception as exc:
                    records.append(
                        ModelPerformanceRecord(
                            model_name=futures[future],
                            provider="error",
                            endpoint="",
                            accuracy=0.0,
                            avg_latency_ms=0.0,
                            total_cases=len(self.cases),
                            passed_cases=0,
                        )
                    )

        records.sort(key=lambda r: r.accuracy, reverse=True)
        best_accuracy = records[0].model_name if records else ""
        best_cost_effective = (
            max(records, key=lambda r: r.accuracy / max(r.cost_per_1k_tokens_usd, 1e-6)).model_name
            if records
            else ""
        )
        return ComparativeLeaderboard(
            records=records,
            best_accuracy_model=best_accuracy,
            best_cost_effective_model=best_cost_effective,
            generated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
