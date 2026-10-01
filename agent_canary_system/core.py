"""Pure rollout logic. Durations are recorded inputs, never predicted savings."""
import math
from datetime import date
from decimal import Decimal

class SchemaError(ValueError):
    """An explicit input contract violation."""

def fail(field, message):
    raise SchemaError(f"field {field}: {message}")

def number(value, field, low=0, high=1_000_000_000):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high or not math.isfinite(value):
        fail(field, f"expected finite number in [{low}, {high}]")

def validate(data):
    if not isinstance(data, dict):
        fail("root", "expected object")
    required = {"synthetic", "as_of", "fraction", "max_regressions", "latency_tolerance", "workflows"}
    if set(data) != required:
        fail("root", f"missing or unknown fields: {sorted(set(data) ^ required)}")
    if type(data["synthetic"]) is not bool:
        fail("synthetic", "expected boolean")
    try:
        as_of = date.fromisoformat(data["as_of"])
        if as_of.isoformat() != data["as_of"]:
            fail("as_of", "expected ISO date YYYY-MM-DD")
    except (ValueError, TypeError):
        fail("as_of", "expected ISO date YYYY-MM-DD")
    number(data["fraction"], "fraction", 0, 1)
    number(data["latency_tolerance"], "latency_tolerance", 0, 10)
    if type(data["max_regressions"]) is not int or not 0 <= data["max_regressions"] <= 1_000_000:
        fail("max_regressions", "expected nonnegative integer <= 1000000")
    if not isinstance(data["workflows"], list) or len(data["workflows"]) > 100000:
        fail("workflows", "expected list of at most 100000 records")
    seen = set()
    fields = {"id", "name", "recorded_on", "baseline_ok", "candidate_ok", "baseline_ms", "candidate_ms"}
    for i, row in enumerate(data["workflows"]):
        prefix = f"workflows[{i}]"
        if not isinstance(row, dict):
            fail(prefix, f"expected fields {sorted(fields)}")
        if set(row) != fields:
            fail(prefix, f"missing or unknown fields: {sorted(set(row) ^ fields)}")
        for key in ("id", "name"):
            if not isinstance(row[key], str) or not 1 <= len(row[key]) <= 10000 or "\u2014" in row[key]:
                fail(f"{prefix}.{key}", "expected 1..10000 characters without em dash")
        if row["id"] in seen:
            fail(f"{prefix}.id", "duplicate id")
        seen.add(row["id"])
        try:
            recorded = date.fromisoformat(row["recorded_on"])
            if recorded.isoformat() != row["recorded_on"]:
                fail(f"{prefix}.recorded_on", "expected ISO date YYYY-MM-DD")
        except (ValueError, TypeError):
            fail(f"{prefix}.recorded_on", "expected ISO date")
        if recorded > as_of:
            fail(f"{prefix}.recorded_on", "future relative to as_of")
        for key in ("baseline_ok", "candidate_ok"):
            if type(row[key]) is not bool:
                fail(f"{prefix}.{key}", "expected boolean")
        for key in ("baseline_ms", "candidate_ms"):
            number(row[key], f"{prefix}.{key}")
    return data

def plan(data):
    validate(data)
    ordered = sorted(data["workflows"], key=lambda row: row["id"])
    count = int(Decimal(len(ordered)) * Decimal(str(data["fraction"])))
    return [row["id"] for row in ordered[:count]]

def evaluate(data):
    selected = set(plan(data))
    rows = sorted((row for row in data["workflows"] if row["id"] in selected), key=lambda row: row["id"])
    findings = []
    for row in rows:
        reasons = []
        if row["baseline_ok"] and not row["candidate_ok"]:
            reasons.append("success_regression")
        threshold = Decimal(str(row["baseline_ms"])) * (1 + Decimal(str(data["latency_tolerance"])))
        if Decimal(str(row["candidate_ms"])) > threshold:
            reasons.append("latency_regression")
        if reasons:
            findings.append({"id": row["id"], "reasons": reasons})
    count = len(findings)
    return {
        "provenance": "SYNTHETIC fixtures" if data["synthetic"] else "REAL user-entered records (not independently verified)",
        "synthetic": data["synthetic"], "as_of": data["as_of"],
        "total_workflows": len(data["workflows"]), "canary_workflows": len(rows),
        "held_back_workflows": len(data["workflows"]) - len(rows),
        "selected_ids": sorted(selected), "regression_workflows": count,
        "observations": rows,
        "success_regressions": sum("success_regression" in f["reasons"] for f in findings),
        "latency_regressions": sum("latency_regression" in f["reasons"] for f in findings),
        "findings": findings,
        "gate": "NO_EVIDENCE" if not rows else "HOLD" if count > data["max_regressions"] else "PASS",
        "policy": {key: data[key] for key in ("fraction", "max_regressions", "latency_tolerance")},
        "measurement_boundary": "Computed from supplied recorded outcomes only; no deployment executed. Time or money saved: unmeasured, not reported. Any projected savings would be hypothetical.",
    }
