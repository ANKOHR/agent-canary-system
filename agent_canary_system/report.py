"""Stable reports and atomic local file writes."""
import json
import os
import tempfile
from pathlib import Path

def json_text(value):
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"

def render(result, format="md"):
    if format == "json":
        return json_text(result)
    lines = ["# Agent Canary System", "", f"Data provenance: {result['provenance']}", "", result["measurement_boundary"], "", f"Gate: **{result['gate']}**", "", "| Computed count | Value |", "| --- | ---: |"]
    for key in ("total_workflows", "canary_workflows", "held_back_workflows", "regression_workflows", "success_regressions", "latency_regressions"):
        lines.append(f"| {key} | {result[key]} |")
    lines += ["", "Full trace and policy (record IDs are JSON escaped):", "", "```json", json_text(result).rstrip(), "```", ""]
    return "\n".join(lines)

def atomic_write(path, text):
    path = Path(path)
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as handle:
            temporary = handle.name
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)
