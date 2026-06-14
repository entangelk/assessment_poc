<!-- .ko mirror created on finalize (publication_plan §7b) -->

<p align="center">
  <a href="./report.md"><img src="https://img.shields.io/badge/Language-EN-111111?style=for-the-badge" alt="English"></a>
  <a href="./report.ko.md"><img src="https://img.shields.io/badge/Language-KO-6B7280?style=for-the-badge" alt="한국어"></a>
</p>
<p align="center"><sub>Switch language / 언어 전환</sub></p>

# Assessment Harness PoC Results Report

Date: 2026-06-14 KST
Targets: `examples/deskhive_assignment`, `examples/pulse_assignment`
Artifacts: the repeated-run outputs are kept under `work/poc_report_runs/run{1,2,3}/...`.

## Conclusion

Both samples under `examples/` run cleanly through the project's current validation flow. Running the same official workflow three times, both samples reproduced the same finding distribution, and Rule 0 reference integrity diagnostics were 0 in every repetition.

This result matches the PoC's purpose of "evaluating the assessment design itself." `check` does not directly pass/fail a candidate — it produces `provisional_findings`, and because of the safe default final-review draft, `gate` stops at `pending_review`. In other words, the current result is not a failure but a sign that "design risks needing human review were reliably surfaced."

That said, this run is not a live LLM extraction. It is an offline wiring/grounding validation using the `deterministic_extraction` runner and the `mock_fixture` semantic verifier. Per the project's documentation, the real SDK runner is still deferred scope.

## Validation method

For each sample, the flow below was repeated three times.

```bash
PYTHONPATH=src python3 -m assessment_harness.cli extract \
  --spec examples/<sample>/spec.md \
  --rubric examples/<sample>/rubric.md \
  --runner deterministic_extraction \
  --runs 3 \
  --policy config/policy.yaml \
  --out-dir work/poc_report_runs/runN/<sample>/runs

PYTHONPATH=src python3 -m assessment_harness.cli compact ...
PYTHONPATH=src python3 -m assessment_harness.cli verify ...
PYTHONPATH=src python3 -m assessment_harness.cli check ...
PYTHONPATH=src python3 -m assessment_harness.cli report ...
PYTHONPATH=src python3 -m assessment_harness.cli review ...
PYTHONPATH=src python3 -m assessment_harness.cli gate ...
PYTHONPATH=src python3 -m assessment_harness.cli materialize-review ...
```

Additional checks:

- `PYTHONPATH=src python3 -m assessment_harness.cli schema --command check --output json`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider`
- DeskHive: `python3 scripts/show_symptoms.py`
- Pulse: confirm `go version`

## Three-repetition results

### DeskHive

| Run | extract | check | high | medium | info | findings | Rule 0 diagnostics | gate |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 1 | success, valid_run_count=3 | provisional_findings | 3 | 11 | 0 | 14 | 0 | pending_review, pending=14 |
| 2 | success, valid_run_count=3 | provisional_findings | 3 | 11 | 0 | 14 | 0 | pending_review, pending=14 |
| 3 | success, valid_run_count=3 | provisional_findings | 3 | 11 | 0 | 14 | 0 | pending_review, pending=14 |

The finding-type distribution was identical across all three runs.

| Type | Count | Interpretation |
|---|---:|---|
| `unconfirmed_trace_coverage` | 7 | Normal provisional coverage warning, since Phase 0 semantic status is not yet human-accepted |
| `possible_orphan_scored_rubric_item` | 1 | A deliberately planted signal: R5's trace quote does not match the spec verbatim |
| `uncovered_must_spec_item` | 1 | The AI usage log is a must spec but has no scored rubric coverage |
| `optionality_mismatch` | 1 | An optional dashboard panel is captured by a 10-point scored rubric |
| `double_scored_spec` | 1 | The CTO report is traced by both scored and bonus rubrics |
| `bonus_grades_mandatory_only` | 2 | A bonus rubric rewards already-required work |
| `mandatory_spec_bonus_only_traced` | 1 | A must spec is covered by bonus only |

Direct reproduction of the DeskHive codebase also matched the README/spec. `scripts/show_symptoms.py` reproduced B1 `inf`, B2 not reflecting a 6-day freeze, B3 summing free+paid passes, B4 KST month-boundary mismatch, and B5 always recommending `H1`.

### Pulse

| Run | extract | check | high | medium | info | findings | Rule 0 diagnostics | gate |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 1 | success, valid_run_count=3 | provisional_findings | 2 | 7 | 1 | 10 | 0 | pending_review, pending=10 |
| 2 | success, valid_run_count=3 | provisional_findings | 2 | 7 | 1 | 10 | 0 | pending_review, pending=10 |
| 3 | success, valid_run_count=3 | provisional_findings | 2 | 7 | 1 | 10 | 0 | pending_review, pending=10 |

The finding-type distribution was identical across all three runs.

| Type | Count | Interpretation |
|---|---:|---|
| `unconfirmed_trace_coverage` | 6 | Normal provisional coverage warning, since Phase 0 semantic status is not yet human-accepted |
| `possible_orphan_scored_rubric_item` | 1 | R4 requires a nonzero exit on a malformed line, conflicting with the spec's skip-and-continue |
| `optionality_mismatch` | 1 | Optional windowing is captured by a 15-point scored rubric |
| `orphan_bonus_rubric_item` | 1 | The Prometheus bonus is not in the spec and is recorded as informational only |
| `uncovered_must_spec_item` | 1 | The malformed-input "must not crash" stays at qualitative-only coverage |

The Pulse reference solution broadly matches the documented core requirements. However, the current environment has no Go toolchain, so `go test ./...` and `go run` could not be executed. `README.md` and `notes.md` already state this limitation, so the documentation and the state are consistent — but one must not claim "Go reference solution execution verified."

## Do the results match the intent

Yes.

DeskHive is designed so that a complex maintenance assignment touches Rule 1, Rule 2, Rule 3, L1, L5, and L6, and the actual results reproduced that distribution stably. R5 non-verbatim trace, R8 optional scored item, RB1 must-but-bonus-only, and R7/RB2 double scoring all appeared as the expected findings.

Pulse is designed to exhibit different branches than DeskHive across a different language / different assignment type, and the results came out that way. In particular, the `orphan_bonus_rubric_item` informational branch and the qualitative-only Rule 2 boundary were confirmed as signals distinct from DeskHive.

It also matters that Rule 0 diagnostics were 0 in every run. That is, the findings did not arise from broken source grounding or schema/reference issues; they arose as by-design review points on valid compacted artifacts.

## Risks and caveats found

1. **This is not live SDK runner validation.**
   The current `deterministic_extraction` is an offline stand-in that derives candidates from the rubric's `Traceable spec quote` hints. This report is a reproducibility validation of the samples and the harness pipeline, not a quality validation of an actual LLM runner.

2. **The semantic verifier is a conservative mock.**
   This run's `semantic_verification_count` is 0 and the report carries no semantic verification proposals. So it is normal that `unconfirmed_trace_coverage` remains.

3. **There may be a small wording inconsistency in DeskHive's docs.**
   The candidate spec requires a finite number for B1, but the codebase business rules mention a possible `null` as the representation for the no-usage case. Treating the spec as canonical, the issue is small, but for a public sample it is better to align the wording to reduce candidate/evaluator confusion.

4. **The Pulse reference solution could not be execution-verified in this environment.**
   `go version` failed with `/bin/bash: line 1: go: command not found`. In an environment with Go installed, re-confirm `go test ./...`, `go run . testdata/events.csv`, and `go run . --json testdata/events.csv`.

5. **More tests on the Pulse public CLI surface would help.**
   The code and test data broadly match the spec, but public surfaces such as file-vs-stdin equivalence, the stderr skipped-count, whether the JSON output matches `testdata/expected.json`, and the text output shape are not strongly locked by the current tests.

6. **The review queue paths must be interpreted distinctly.**
   `check --review-queue-out` produces 2 lint-safeguard queue entries for DeskHive, but the unified Phase 2 `compact`/`verify` queue is empty on this clean run. As the current README warns, the design does not write the Phase 0 check queue directly into the unified queue path.

## Final assessment

`examples/` is set up appropriately as PoC demo samples. The official workflow, repeated three times, produced identical results, and the finding distribution matches the design signals the sample documents intended.

In a report/portfolio context, the following phrasing is safe.

> The examples validate the deterministic harness workflow and demonstrate stable assessment-design findings across two different assignment archetypes. They do not yet validate live LLM extraction quality; real SDK runners remain future work.
