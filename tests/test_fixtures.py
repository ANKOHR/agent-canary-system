import json
from agent_canary_system.fixtures import generate
from agent_canary_system.core import evaluate

def test_fixtures_labelled_synthetic(tmp_path):
    generate(tmp_path)
    for path in tmp_path.rglob("*.json"):
        assert json.loads(path.read_text(encoding="utf-8"))["synthetic"] is True
    assert "<!-- SYNTHETIC fixture -->" in (tmp_path / "LABEL.md").read_text()

def test_expectations_are_independent(tmp_path):
    generate(tmp_path)
    expectations = json.loads((tmp_path / "expectations.json").read_text())
    result = evaluate(json.loads((tmp_path / "workflows.json").read_text()))
    for key in ("total_workflows", "canary_workflows", "held_back_workflows", "regression_workflows", "success_regressions", "latency_regressions", "gate"):
        assert result[key] == expectations[key]
    assert [f["id"] for f in result["findings"]] == expectations["regression_ids"]
