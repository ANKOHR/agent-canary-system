import pytest
from agent_canary_system.core import evaluate, SchemaError
from agent_canary_system.fixtures import dataset

def test_fixture_ground_truth_matches_hand_computed():
    result = evaluate(dataset())
    assert (result["total_workflows"], result["canary_workflows"], result["held_back_workflows"]) == (200, 40, 160)
    assert (result["regression_workflows"], result["success_regressions"], result["latency_regressions"]) == (12, 8, 4)

@pytest.mark.parametrize("field,value", [("baseline_ms", -1), ("candidate_ms", 10 ** 1000), ("candidate_ms", float("nan")), ("candidate_ms", float("inf")), ("baseline_ok", 1), ("recorded_on", "2026-10-01"), ("name", "x" * 10001), ("id", "bad\u2014id")])
def test_rejects_adversarial_values(field, value):
    data = dataset()
    data["workflows"][0][field] = value
    with pytest.raises(SchemaError, match=field):
        evaluate(data)

def test_duplicate_ids():
    data = dataset()
    data["workflows"][1]["id"] = data["workflows"][0]["id"]
    with pytest.raises(SchemaError, match="duplicate"):
        evaluate(data)

def test_handles_unicode_and_long_inputs():
    data = dataset()
    data["workflows"][0]["name"] = "日本語 café C:\\Users\\Henry " + "x" * 9000
    assert evaluate(data)["regression_workflows"] == 12

def test_corrupted_ground_truth_changes_computation():
    data = dataset()
    data["workflows"][0]["candidate_ms"] = 100
    assert evaluate(data)["regression_workflows"] == 11

def test_boundary_and_overlapping_reasons():
    data = dataset(5)
    data["workflows"][0].update(candidate_ms=120, candidate_ok=False)
    result = evaluate(data)
    assert result["regression_workflows"] == 1
    assert result["latency_regressions"] == 0
    data["workflows"][0]["candidate_ms"] = 121
    result = evaluate(data)
    assert result["regression_workflows"] == 1
    assert result["latency_regressions"] == 1

@pytest.mark.parametrize("fraction", [-1, 2, True])
def test_invalid_policy(fraction):
    data = dataset()
    data["fraction"] = fraction
    with pytest.raises(SchemaError):
        evaluate(data)


def test_decimal_threshold_and_fraction_are_exact():
    data = dataset(100)
    data["fraction"] = 0.29
    data["latency_tolerance"] = 0.1
    data["workflows"][0].update(baseline_ms=100, candidate_ms=110)
    result = evaluate(data)
    assert result["canary_workflows"] == 29
    assert "wf-001" not in {f["id"] for f in result["findings"]}
    data["workflows"][0]["candidate_ms"] = 110.00000000000001
    assert "wf-001" in {f["id"] for f in evaluate(data)["findings"]}


@pytest.mark.parametrize("field", ["as_of", "recorded_on"])
def test_compact_dates_rejected(field):
    data = dataset()
    target = data if field == "as_of" else data["workflows"][0]
    target[field] = "20260930"
    with pytest.raises(SchemaError, match=field):
        evaluate(data)
