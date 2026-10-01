"""CLI boundary: local input, named errors, persisted deterministic results."""
import argparse
import json
import sys
import hashlib
from pathlib import Path
from .core import SchemaError, evaluate, plan
from .fixtures import dataset, generate
from .report import atomic_write, json_text, render

class InputError(ValueError):
    pass


def unique_object(pairs):
    """Reject ambiguous JSON instead of silently overwriting supplied values."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field " + ascii(key))
        result[key] = value
    return result

def read_input(directory):
    directory = Path(directory)
    if not directory.is_dir():
        raise InputError(f"MissingInput: {directory}; use acs fixtures --out demo")
    path = directory / "workflows.json"
    if not path.exists():
        if any(directory.iterdir()):
            raise InputError(f"MissingInput: {path}; expected workflows.json")
        empty = dataset(0)
        empty["synthetic"] = False
        return empty
    try:
        source = path.read_text(encoding="utf-8")
        data = json.loads(source, object_pairs_hook=unique_object)
    except json.JSONDecodeError as exc:
        raise InputError(f"ParseError: {path}: line {exc.lineno}: {exc.msg}") from exc
    except UnicodeError as exc:
        raise InputError(f"ParseError: {path}: line 1: invalid UTF-8") from exc
    except ValueError as exc:
        raise InputError(f"ParseError: {path}: line 1 (document-level ambiguity): {exc}") from exc
    try:
        plan(data)
    except SchemaError as exc:
        raise InputError(f"SchemaError: {path}: {exc}") from exc
    return data

def parser():
    p = argparse.ArgumentParser(description="Local canary plans and recorded-result gates. No deployment execution.")
    p.add_argument("--state", default=".acs/result.json", help="Result file, default .acs/result.json")
    sub = p.add_subparsers(dest="command", required=True)
    f = sub.add_parser("fixtures", help="Generate labelled synthetic inputs", epilog="Example: acs fixtures --out demo")
    f.add_argument("--out", required=True)
    for name, help_text in (("run", "Compute and persist canary results"), ("plan", "Print deterministic canary cohort"), ("gate", "Evaluate recorded candidate results; HOLD exits 3")):
        s = sub.add_parser(name, help=help_text, description=help_text, epilog=f"Example: acs {name} --input demo")
        s.add_argument("--input", required=True)
    r = sub.add_parser("report", help="Render persisted results with provenance", epilog="Example: acs report --format md")
    r.add_argument("--format", choices=("md", "json"), default="md")
    r.add_argument("--out", help="Optional atomic report output file")
    return p

def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "fixtures":
            generate(args.out)
            print(f"SYNTHETIC fixtures written to {args.out}")
        elif args.command in ("run", "plan", "gate"):
            data = read_input(args.input)
            result = evaluate(data)
            if not data["workflows"]:
                result["provenance"] = "EMPTY input: no recorded outcomes; synthetic=" + str(data["synthetic"]).lower()
            if args.command == "plan":
                print(json_text({"provenance": result["provenance"], "selected_ids": plan(data), "measurement_boundary": result["measurement_boundary"]}), end="")
            elif args.command == "run":
                result["source"] = str(Path(args.input) / "workflows.json")
                source_path = Path(args.input) / "workflows.json"
                result["source_sha256"] = hashlib.sha256(source_path.read_bytes()).hexdigest() if source_path.exists() else None
                atomic_write(args.state, json_text(result))
                print(f"{result['provenance']}: computed {result['total_workflows']} workflows; gate {result['gate']}. No deployment executed.")
            else:
                print(render(result), end="")
                return 0 if result["gate"] == "PASS" else 3
        else:
            path = Path(args.state)
            if not path.is_file():
                raise InputError(f"MissingResult: {path}; run acs run --input demo first")
            try:
                result = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
            except json.JSONDecodeError as exc:
                raise InputError(f"ParseError: {path}: line {exc.lineno}: {exc.msg}") from exc
            except (UnicodeError, ValueError) as exc:
                raise InputError(f"ParseError: {path}: line 1: {exc}") from exc
            output = render(result, args.format)
            if args.out:
                atomic_write(args.out, output)
            else:
                print(output, end="")
        return 0
    except (InputError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"{type(exc).__name__ if not isinstance(exc, OSError) else 'FileError'}: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
