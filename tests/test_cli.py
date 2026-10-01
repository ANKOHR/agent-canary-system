import json
import time
from agent_canary_system.cli import main
from agent_canary_system.fixtures import generate

def setup(tmp_path):
    generate(tmp_path / "input")
    return ["--state", str(tmp_path / "result.json")]

def test_run_completes_on_fixture(tmp_path, capsys):
    args = setup(tmp_path)
    start = time.perf_counter()
    assert main(args + ["run", "--input", str(tmp_path / "input")]) == 0
    assert main(args + ["report", "--format", "md"]) == 0
    assert time.perf_counter() - start < 5
    assert "SYNTHETIC fixtures" in capsys.readouterr().out

def test_empty_input_renders_without_traceback(tmp_path, capsys):
    assert main(["--state", str(tmp_path / "result.json"), "run", "--input", str(tmp_path)]) == 0
    assert main(["--state", str(tmp_path / "result.json"), "report"]) == 0
    assert "NO_EVIDENCE" in capsys.readouterr().out

def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path / "workflows.json").write_text('{\n"bad": }')
    assert main(["run", "--input", str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert "ParseError" in error and "workflows.json: line 2" in error

def test_determinism_byte_identical(tmp_path):
    args = setup(tmp_path)
    assert main(args + ["run", "--input", str(tmp_path / "input")]) == 0
    first = (tmp_path / "result.json").read_bytes()
    assert main(args + ["run", "--input", str(tmp_path / "input")]) == 0
    assert (tmp_path / "result.json").read_bytes() == first

def test_cli_smoke_all_subcommands(tmp_path, capsys):
    args = setup(tmp_path)
    assert main(args + ["fixtures", "--out", str(tmp_path / "other")]) == 0
    assert main(args + ["plan", "--input", str(tmp_path / "input")]) == 0
    assert main(args + ["gate", "--input", str(tmp_path / "input")]) == 3
    assert main(args + ["run", "--input", str(tmp_path / "input")]) == 0
    for format in ("md", "json"):
        assert main(args + ["report", "--format", format]) == 0
    assert "\u2014" not in capsys.readouterr().out

def test_missing_and_schema_errors(tmp_path, capsys):
    assert main(["run", "--input", str(tmp_path / "absent")]) == 2
    assert "MissingInput" in capsys.readouterr().err
    (tmp_path / "workflows.json").write_text('{}')
    assert main(["run", "--input", str(tmp_path)]) == 2
    assert "SchemaError" in capsys.readouterr().err


def test_help_all_subcommands():
    import pytest
    for command in ("fixtures", "run", "report", "plan", "gate"):
        with pytest.raises(SystemExit) as error:
            main([command, "--help"])
        assert error.value.code == 0


def test_gate_pass_and_no_evidence(tmp_path, capsys):
    from agent_canary_system.fixtures import dataset
    data = dataset(5)
    data["workflows"][0]["candidate_ms"] = 100
    (tmp_path / "workflows.json").write_text(json.dumps(data))
    assert main(["gate", "--input", str(tmp_path)]) == 0
    data["fraction"] = 0
    (tmp_path / "workflows.json").write_text(json.dumps(data))
    assert main(["gate", "--input", str(tmp_path)]) == 3


def test_report_write_failure_named_error(tmp_path, capsys):
    args = setup(tmp_path)
    assert main(args + ["run", "--input", str(tmp_path / "input")]) == 0
    assert main(args + ["report", "--out", str(tmp_path / "input")]) == 2
    assert "FileError" in capsys.readouterr().err
    assert sorted(p.name for p in (tmp_path / "input").iterdir()) == ["LABEL.md", "expectations.json", "tiny", "workflows.json"]


def test_duplicate_json_fields_rejected(tmp_path, capsys):
    (tmp_path / "workflows.json").write_text('{"synthetic": true, "synthetic": false}')
    assert main(["run", "--input", str(tmp_path)]) == 2
    assert "duplicate JSON field" in capsys.readouterr().err


def test_report_observations_and_source_digest(tmp_path):
    import hashlib
    args = setup(tmp_path)
    assert main(args + ["run", "--input", str(tmp_path / "input")]) == 0
    result = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    assert len(result["observations"]) == result["canary_workflows"] == 40
    source = (tmp_path / "input" / "workflows.json").read_bytes()
    assert result["source_sha256"] == hashlib.sha256(source).hexdigest()


def test_malformed_result_named_error(tmp_path, capsys):
    path = tmp_path / "result.json"
    path.write_text('{\n"bad": }')
    assert main(["--state", str(path), "report"]) == 2
    assert "result.json: line 2" in capsys.readouterr().err
