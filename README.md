# Agent Canary System

A CPU-only Python CLI for deterministic canary cohort planning and gates based on recorded baseline and candidate outcomes. It writes a rollout plan for a fraction of workflows first. An operator or external runner must execute that plan and record outcomes; this tool does not deploy changes itself or infer effects on held-back workflows.

## Hypothesis and acceptance

Explicit local inputs and pure, tested rules can make a trustworthy canary planning tool. Acceptance: all planted cases found, zero false positives, exact reconciled counts on 200 synthetic records, report and demo under 5 seconds, green adversarial tests. The fixture validates computation, not production effectiveness.

## Quickstart

Python 3.10+ and setuptools are required. No runtime dependencies, network calls, language-model calls, GPU workloads, databases, or random generators are used.

```powershell
python -m pip install --no-index --no-deps --no-build-isolation -e .
acs fixtures --out demo
acs run --input demo
acs report --format md
python -m pytest -q
```

If pip reports that the Scripts directory is not on PATH, use `python -m agent_canary_system.cli` in place of `acs`, or add that directory to PATH.

The generated `demo/tiny/workflows.json` has five records for the smallest demo: `acs run --input demo/tiny`. The default result file is `.acs/result.json`. Use `acs --state path/result.json run --input demo` and the same global option when reporting.

## Subcommands

| Command | Example | Result |
| --- | --- | --- |
| fixtures | `acs fixtures --out demo` | Labelled 200-record fixture, expectations and five-record sample |
| run | `acs run --input demo` | Validate, compute and atomically persist results |
| report | `acs report --format json --out report.json` | Render persisted result with provenance |
| plan | `acs plan --input demo` | Print selected IDs with provenance |
| gate | `acs gate --input demo` | Print recorded-results gate; PASS exits 0, HOLD or NO_EVIDENCE exits 3 |

Each command supports `--help`. Validation or file errors exit 2. Argument usage errors exit 2. Run computes successfully even if its gate is HOLD. Report reads the persisted snapshot, so rerun after changing input.

## Input reference

An input directory contains exactly one recognized input, `workflows.json`, encoded as UTF-8. Other files are not used as workflow data. JSON is the supported ingestion format; CSV and YAML must be converted explicitly. An entirely empty directory gives zero counts and NO_EVIDENCE. A nonempty directory without workflows.json is a named missing-input error.

```json
{
  "synthetic": false,
  "as_of": "2026-09-30",
  "fraction": 0.2,
  "max_regressions": 0,
  "latency_tolerance": 0.2,
  "workflows": [
    {
      "id": "workflow-001",
      "name": "Henry enters the actual workflow name here",
      "recorded_on": "2026-09-30",
      "baseline_ok": true,
      "candidate_ok": true,
      "baseline_ms": 100,
      "candidate_ms": 100
    }
  ]
}
```

The numbers above are illustrative schema examples, not measured results. Replace every record with Henry's own measurements before marking synthetic false. That flag is a user declaration, not independent verification. Real trial results are recorded locally and are not shipped.

All displayed fields are required; unknown fields fail validation. IDs must be unique. IDs and names accept Unicode and Windows paths, 1 to 10000 characters, excluding the em dash character. Up to 100000 records are accepted. Dates use ISO YYYY-MM-DD; recorded_on must not exceed the explicit as_of date. The tool does not consult the wall clock. Set as_of honestly to the observation cutoff; dates beyond that cutoff fail.

Durations are recorded milliseconds in [0, 1000000000], finite and nonnegative. Booleans must be actual JSON booleans. fraction is in [0,1]; latency_tolerance is in [0,10]; max_regressions is an integer in [0,1000000]. Negative amounts, nonfinite numbers, extreme strings, duplicates and schema drift are rejected, never dropped. There are no money fields, and attempted extra fields fail.

## Rules and traceability

Sort IDs lexicographically by Unicode code point and select the first floor(N * fraction). No randomness or seed is used. This is reproducible but can bias the cohort when IDs cluster by workflow type. Choose IDs and fraction deliberately; this is not random statistical sampling. Fewer than one selected record gives NO_EVIDENCE, never PASS.

Within that cohort, flag success_regression when baseline_ok is true and candidate_ok is false. Flag latency_regression when candidate_ms is strictly greater than baseline_ms * (1 + latency_tolerance). Equality passes. Both reasons can apply to a single workflow, counted once in regression_workflows. HOLD when the number of distinct regressed workflows exceeds max_regressions; otherwise PASS. PASS only describes supplied recorded observations, not a guarantee that broader rollout is safe. Outcomes for held-back workflows are not evaluated.

Reports include selected IDs, selected input observations, reason lists, policy, date cutoff, input path and SHA-256 of the source bytes. Total = canary + held back. Reason counts can overlap and need not sum to distinct regressions. Decimal arithmetic over the supplied numeric representations defines threshold and cohort-size behavior; no estimates or rounded percentages are produced.

## Architecture

```text
workflows.json -> cli.read_input -> core.validate -> core.plan -> core.evaluate
                                                       |            |
                                                       |            v
                                                       |       .acs/result.json
                                                       |            |
                                                       v            v
                                                   plan output   report.render -> stdout or atomic file
fixtures.generate -> labelled inputs and independent hand-computed expectations
```

Core has no file I/O. CLI owns parsing and persistence. Report owns stable rendering and atomic writes. Same input, source path and policy give byte-identical outputs, independent of wall clock. No timestamps or measured runtime are injected into reports.

## Honesty boundary and fixture labelling

This tool computes only from explicit inputs. It does not discover or predict failures. Synthetic reports say SYNTHETIC fixtures. Real reports say REAL user-entered records (not independently verified). No time or money saved is claimed: those figures are unmeasured, and projections would be hypothetical. The realistic path is Henry entering real observations by hand. No real-use accuracy or revenue has yet been measured.

Every fixture JSON carries synthetic: true. JSON cannot contain header comments; the accompanying LABEL.md carries a SYNTHETIC header comment, and the fixture module explicitly labels its synthetic role. The expectation derivation is independent of evaluate: 40 selected IDs; 8 multiples of five fail success, and 4 IDs ending in 1 regress latency. These sets are disjoint, giving 12 findings. The five-record sample is hand-written and uses the same rules.

## Failure modes

Bad JSON reports ParseError with filename and line. Duplicate JSON fields fail as document-level ambiguity, labelled line 1, rather than silently overwriting data. Invalid UTF-8 reports ParseError with filename and line 1 (the decoder does not provide a JSON line). SchemaError identifies the file and offending field. Missing input and missing result errors provide usage hints. File errors are named, exit nonzero, and atomic writes clean up temporary files if replacement fails. Existing report files survive failed writes. Generated fixture sets consist of several atomic files; a failed generation can leave previously completed files and can be rerun. Persisted results are trusted local artifacts, not signed attestations.

## Evidence-based improvement and verdict

For two weeks after the first real use, record run dates and manually compare selected IDs, reasons and counts to a hand-checked sample. Primary metric: erroneous workflow decisions / checked workflow decisions. Keep the sample and calculations locally. If error rate exceeds 10 percent, fix the most frequent cause or kill with a written reason. If no actual use occurs in that window, record that finding and kill. A zero-sized sample is unmeasured, not 0 percent error.

Verdict: pending the two-week real-use evidence window. This is not an expand, integrate, commercialise, maintain or kill verdict based on invented evidence. At the review, record a reason and choose expand for daily use or revenue, integrate for heavy sibling overlap, commercialise for an actual willing buyer, maintain as portfolio evidence if criteria pass with occasional use, or kill if unused or acceptance cannot be met. See EVIDENCE.md for local build evidence and LESSONS.md for operating rules.

Publishing is handled separately. This build makes no external network calls.
