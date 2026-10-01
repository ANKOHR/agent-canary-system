# Local build evidence

Measured on 2026-10-01, CPU-only Windows Python 3.12.10. Installed acs entry point executed fixtures, run and report successfully in 0.668 seconds total (wall time, including three process launches). The report contains the SYNTHETIC provenance banner. This is local test runtime, not a saved-time claim or production benchmark.

pytest: 40 tests passed. Hand-computed fixture: 200 total, 40 canary, 160 held back, 8 success regressions, 4 latency regressions, 12 distinct regressions. All 12 planted IDs found; zero false positives. The corrupted-input test changes a recorded duration and reduces the computed findings to 11. Repeated runs produce byte-identical persisted output. Empty inputs give NO_EVIDENCE with zero counts.

Adversarial checks cover malformed JSON with file and line, missing input, schema drift, negative and oversized durations, NaN and infinity, invalid booleans, future dates against an explicit cutoff, duplicate IDs, long Unicode strings, Windows paths, strict threshold equality, overlapping reasons, and failed atomic report writes.

Real-use sample: not yet collected. Accuracy on real data, actual use frequency, saved time, buyer demand and revenue are unmeasured. The two-week verdict is pending and must be recorded from real-use evidence per README.

Numeric boundary improvement: a 100-record input at fraction 0.29 now selects exactly 29 workflows. Decimal comparisons preserve equality at a 10 percent latency tolerance; the next representable supplied duration is detected. Source hashes and selected observations make findings reproducible from the report snapshot. Duplicate JSON keys and noncanonical dates are rejected. These changes were motivated by concrete ambiguity and floating-point boundary cases, not real-use evidence.
