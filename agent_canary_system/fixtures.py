"""Synthetic labelled ground truth, no randomness or illustrative measurements."""
from pathlib import Path
from .report import atomic_write, json_text

def dataset(count=200):
    rows = []
    for i in range(1, count + 1):
        rows.append({"id": f"wf-{i:03}", "name": f"Synthetic workflow {i}", "recorded_on": "2026-09-30", "baseline_ok": True, "candidate_ok": i % 5 != 0, "baseline_ms": 100, "candidate_ms": 150 if i % 10 == 1 else 100})
    return {"synthetic": True, "as_of": "2026-09-30", "fraction": 0.2, "max_regressions": 0, "latency_tolerance": 0.2, "workflows": rows}

def generate(out):
    out = Path(out)
    atomic_write(out / "workflows.json", json_text(dataset()))
    atomic_write(out / "expectations.json", json_text({"synthetic": True, "total_workflows": 200, "canary_workflows": 40, "held_back_workflows": 160, "regression_workflows": 12, "success_regressions": 8, "latency_regressions": 4, "gate": "HOLD", "regression_ids": [f"wf-{i:03}" for i in (1,5,10,11,15,20,21,25,30,31,35,40)], "derivation": "First 40 IDs selected. Multiples of 5: 8 failures. IDs 1,11,21,31: 4 latency regressions. Sets disjoint; union 12."}))
    atomic_write(out / "LABEL.md", "<!-- SYNTHETIC fixture -->\n# SYNTHETIC data\nAll records and expectations are synthetic. JSON carries synthetic: true; JSON does not allow header comments.\n")
    # Hand-written smallest example: one selected latency regression.
    tiny = {"synthetic": True, "as_of": "2026-09-30", "fraction": 0.2,
            "max_regressions": 0, "latency_tolerance": 0.2, "workflows": [
        {"id": "wf-001", "name": "Synthetic intake", "recorded_on": "2026-09-30", "baseline_ok": True, "candidate_ok": True, "baseline_ms": 100, "candidate_ms": 150},
        {"id": "wf-002", "name": "Synthetic routing", "recorded_on": "2026-09-30", "baseline_ok": True, "candidate_ok": True, "baseline_ms": 100, "candidate_ms": 100},
        {"id": "wf-003", "name": "Synthetic review", "recorded_on": "2026-09-30", "baseline_ok": True, "candidate_ok": True, "baseline_ms": 100, "candidate_ms": 100},
        {"id": "wf-004", "name": "Synthetic archive", "recorded_on": "2026-09-30", "baseline_ok": True, "candidate_ok": True, "baseline_ms": 100, "candidate_ms": 100},
        {"id": "wf-005", "name": "Synthetic delivery", "recorded_on": "2026-09-30", "baseline_ok": True, "candidate_ok": False, "baseline_ms": 100, "candidate_ms": 100},
    ]}
    atomic_write(out / "tiny" / "workflows.json", json_text(tiny))
