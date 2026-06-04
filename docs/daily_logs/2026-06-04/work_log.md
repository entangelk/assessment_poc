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

## Plan v1.31 Review Materialization Contract

### Goals

- Close the canonical contract gap for trace-link override/status materialization before implementation.
- Keep `gate` verdict-only and avoid making it write artifact files.
- Define a surgical initial `materialize-review` scope that can be implemented next without guessing public behavior.

### Completed work

- Updated `docs/implementation_plan_assessment_harness_poc_v1.md` to v1.31.
  - Key change: added §5.6.1 `Review Materialization`.
  - Key change: defined `materialize-review` as a separate command that reads final review + compacted artifacts and writes reviewed artifacts to a new output directory.
  - Key change: fixed trace-link materialization keys at `target_key: {trace_link_id}`, resolved through `id_map.yaml` `entity_type: trace_link` entries.
  - Key change: defined trace-link action mapping: `accept -> human_accepted`, `override -> human_overridden + human_override source`, `hold -> no artifact change`, `rerun_requested -> rerun_requested`.
  - Key change: defined review_queue action mapping: `accept`/`override -> resolved`, `hold -> held`, `rerun_requested -> rerun_pending`.
  - Effect: the next implementation slice can add `materialize-review` without deciding command shape, key shape, or status mapping ad hoc.
- Updated `HANDOFF.md`, `README.md`, `docs/evaluation.md`, and `CHANGELOG.md`.
  - Effect: the canonical plan version and next implementation task now point to v1.31 and `materialize-review`.

### Issues found

- Problem: final review examples used trace-link keys shaped like `{rubric_id, spec_ids}` while compacting already treats trace links as canonical relationship artifacts with `id_map.entity_type: trace_link`.
  Cause: earlier examples predated the later trace-link canonical ID lineage work.
  Resolution: v1.31 changes trace-link final-review materialization examples and contract to use `{trace_link_id}`.
  Outcome: materialization can join by canonical lineage rather than relation fields that may become ambiguous when identity_basis changes.
- Problem: the plan said `override` should add `kind: human_override` provenance but did not define which command writes that provenance.
  Cause: `review` drafts decisions and `gate` returns verdicts, but neither should mutate compacted artifacts.
  Resolution: v1.31 assigns artifact writing to `materialize-review`.
  Outcome: `gate` remains verdict-only, and reviewed artifact generation is explicit.

### Decisions

- **Command separation:** `gate` must not materialize review decisions. `materialize-review` owns reviewed artifact output.
- **No in-place mutation:** `materialize-review` writes to `--out-dir`; compacted inputs remain immutable review evidence.
- **Trace-link key:** materialization uses canonical `trace_link_id` via `id_map.yaml`, not `{rubric_id, spec_ids}`.
- **Override scope:** `override` materialization is for typo/omission fixes. Semantic reinterpretation should use `rerun_requested` and a new run.

### Next steps

1. Implement `materialize-review` per plan v1.31, including schema self-discovery and CLI output contract tests.
2. Add regressions for trace-link accept/override/hold/rerun_requested, review_queue status mapping, missing/ambiguous id_map joins, and no in-place mutation.
3. Re-run focused CLI tests and the full suite after implementation.

### Verification

- Documentation-only contract update.
- `git diff --check` → clean.
