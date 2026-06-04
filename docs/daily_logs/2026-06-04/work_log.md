# Work Log - 2026-06-04

## Publication Evaluation Snapshot Refresh

### Goals

- Read the current handoff and latest daily log to identify the next feasible task.
- Recompute the publication-facing evaluation snapshot from real test and smoke output.
- Keep publication docs honest while avoiding premature implementation of underspecified trace-link/status materialization.

### Completed work

- Updated `docs/evaluation.md`.
  - Key change: refreshed the dated moving snapshot from 2026-05-31 to 2026-06-04.
  - Key change: updated the full-suite count from `200 passed` to `248 passed`.
  - Key change: added the `tests/test_compacting.py` row and updated CLI contract coverage from 48 to 89 tests.
  - Effect: the publication evidence page now reflects the current Phase 2 CLI surface (`extract`, `compact`, `verify`, semantic-verification consumption, and review_queue final-review handling).
- Updated `HANDOFF.md`.
  - Key change: refreshed the Step 3 evaluation summary and verification count to the 2026-06-04 snapshot.
  - Effect: the next worker sees current test counts and no longer inherits the older 200/244-test summaries.
- Updated `docs/case_study.md`.
  - Key change: changed the next-step wording to say the evaluation should be recomputed once more at publication freeze.
  - Effect: the case study no longer implies the already-refreshed evaluation snapshot is still the immediate next task.

### Issues found

- Problem: the top remaining implementation task in `HANDOFF.md` mentions trace-link override/status materialization, but the canonical plan does not yet define a concrete command/output contract for that materialization.
  Cause: plan §5.6 states that `override` records `kind: human_override` provenance, while current CLI surfaces only draft/final gate decisions; the materialization workflow is still broader than a surgical next slice.
  Resolution: deferred implementation and used the next verifiable task: recomputing publication evaluation tables from real output.
  Outcome: no speculative command or contract was introduced.

### Decisions

- **Implementation boundary:** do not implement trace-link/status materialization until the owner or canonical plan defines the command/output surface. This avoids turning a vague follow-up into a public interface by accident.
- **Publication snapshot handling:** `docs/evaluation.md` remains a moving snapshot. The 2026-06-04 refresh is current evidence, but it should still be recomputed at the final publication freeze.

### Next steps

1. Owner/spec decision: define the trace-link override/status materialization command and output contract before implementation.
2. Add real SDK runner support when a runnable sample assignment and credential path are ready.
3. Recompute `docs/evaluation.md` again at publication freeze, then perform the deferred bilingual mirrors.

### Verification

- `PYTHONPATH=src python3 -m pytest --collect-only -q` → 248 tests collected: agent-runner 27, CLI 89, compacting 7, fixtures 8, models 22, rules 95.
- `PYTHONPATH=src python3 -m pytest -q` → full suite passed (`248 passed` by collection count).
- Fixture smoke runs with `PYTHONPATH=src python3 -m assessment_harness.cli --output json check ...`:
  - `clean_assignment` → `provisional_findings`, exit `0`, `(high=0, medium=2, informational=0)`, `review_queue_count=0`.
  - `orphan_scored_rubric` → `provisional_findings`, exit `0`, `(high=1, medium=1, informational=1)`, `review_queue_count=0`.
  - `uncovered_must_spec` → `provisional_findings`, exit `0`, `(high=1, medium=5, informational=0)`, `review_queue_count=1`.
  - `optionality_mismatch` → `provisional_findings`, exit `0`, `(high=2, medium=1, informational=0)`, `review_queue_count=0`.
  - `bonus_misuse` → `provisional_findings`, exit `0`, `(high=1, medium=5, informational=1)`, `review_queue_count=2`.
  - `reference_integrity` → `invalid_input`, exit `2`, `high_integrity_count=9`.
- Input guard smoke runs:
  - no `--source-manifest` with policy present → `invalid_input`, exit `2`, `provide_source_manifest`.
  - no `--policy` with manifest present → `invalid_input`, exit `2`, `provide_policy`.
  - both omitted → `invalid_input`, exit `2`, `provide_source_manifest`.
