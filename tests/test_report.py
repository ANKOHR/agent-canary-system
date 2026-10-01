import json
from agent_canary_system.core import evaluate
from agent_canary_system.fixtures import dataset
from agent_canary_system.report import render, atomic_write
import pytest

def test_report_matches_ground_truth_exact():
    result = json.loads(render(evaluate(dataset()), "json"))
    assert result["regression_workflows"] == 12
    assert result["success_regressions"] == 8
    assert result["latency_regressions"] == 4

def test_report_zero_false_positives():
    result = json.loads(render(evaluate(dataset()), "json"))
    assert {f["id"] for f in result["findings"]} == {f"wf-{i:03}" for i in (1,5,10,11,15,20,21,25,30,31,35,40)}

@pytest.mark.parametrize("format", ["md", "json"])
def test_report_carries_provenance_banner(format):
    assert "SYNTHETIC fixtures" in render(evaluate(dataset()), format)
    data = dataset()
    data["synthetic"] = False
    assert "REAL user-entered records" in render(evaluate(data), format)

def test_hypothetical_figures_labelled():
    output = render(evaluate(dataset()))
    assert "hypothetical" in output and "unmeasured" in output

def test_no_em_dashes_in_outputs():
    for format in ("md", "json"):
        assert "\u2014" not in render(evaluate(dataset()), format)

def test_write_failure_leaves_no_partial_files(tmp_path):
    destination = tmp_path / "directory"
    destination.mkdir()
    with pytest.raises(OSError):
        atomic_write(destination, "report")
    assert list(tmp_path.iterdir()) == [destination]
