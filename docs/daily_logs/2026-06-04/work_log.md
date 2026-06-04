# Work Log - 2026-06-04

## Publication Evaluation Snapshot Refresh

### Goals

- Read the current handoff and latest daily log to identify the next feasible task.
- Recompute the publication-facing evaluation snapshot from real test and smoke output.
- Keep publication docs honest while avoiding premature implementation of underspecified trace-link/status materialization.

### Completed work

- Updated `docs/evaluation.md`.
  - Key change: refreshed the dated moving snapshot from 2026-05-31 to 2026-06-04.
  - Key change: updated the full-suite count from `200 passed`; the final same-day snapshot is `258 passed` after the later `materialize-review` implementation.
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

- `PYTHONPATH=src python3 -m pytest --collect-only -q` → initial refresh snapshot before `materialize-review`: 248 tests collected (agent-runner 27, CLI 89, compacting 7, fixtures 8, models 22, rules 95). Superseded later in this log by the 258-test snapshot after `materialize-review`.
- `PYTHONPATH=src python3 -m pytest -q` → full suite passed for the initial refresh snapshot.
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

## Initial `materialize-review` CLI Orchestration

### Goals

- Implement the v1.31 review materialization contract without changing `gate` semantics.
- Materialize reviewed artifacts in a new output directory while preserving compacted inputs unchanged.
- Lock trace-link and review_queue status mappings under CLI contract tests.

### Completed work

- Added `materialize-review` to `src/assessment_harness/cli.py`.
  - Inputs: `--final-review`, `--compacted-dir`, `--out-dir`, optional `--review-queue`, optional `--id-map`.
  - Outputs: reviewed `spec_items.yaml`, `rubric_items.yaml`, `trace_links.yaml`, optional `review_queue.json`, and `materialization_summary.json`.
  - Behavior: loads final review, compacted artifacts, id_map, and review_queue; applies trace-link decisions by canonical `trace_link_id`; applies review_queue decisions by `entry_id`; writes only to `--out-dir`.
- Added schema self-discovery for `schema --command materialize-review`.
  - Effect: caller agents can discover `materialize-review` informational fields and recovery actions through the existing contract surface.
- Added CLI regressions in `tests/test_cli_output_contract.py`.
  - Locks schema self-discovery for `materialize-review`.
  - Locks trace-link `override` materialization with `human_overridden`, `reviewed_by`, `reviewed_at`, shallow `override_payload` merge, and appended `kind: human_override` source.
  - Locks trace-link `accept` and `rerun_requested` status mapping.
  - Locks `hold` as a no-op for trace links.
  - Locks review_queue `accept`, `override`, `hold`, and `rerun_requested` status mapping.
  - Locks fail-loud behavior for missing id_map and unknown trace_link_id.
  - Locks that compacted input `trace_links.yaml` is not mutated in place.
- Updated `HANDOFF.md`, `README.md`, `docs/case_study.md`, and `CHANGELOG.md`.
  - Effect: project status now reflects that `materialize-review` is initially implemented.

### Issues found

- Problem: the first materialization tests used underspecified synthetic spec/rubric items.
  Cause: the helper omitted required `requirement_level`, `title`, and `source_ref` fields.
  Resolution: changed the test fixture helper to write schema-valid compacted spec/rubric inputs.
  Outcome: tests exercise materialization behavior rather than failing early on unrelated schema validation.

### Decisions

- **Implementation scope:** initial materialization supports trace links and review_queue entries only. `finding` decisions remain `gate` inputs; `spec_item`/`rubric_item` decisions are counted as unsupported materialization and the artifacts are copied unchanged.
- **Trace join:** trace-link decisions require `id_map.yaml`; order-based fallback is not used for materialization.
- **Output discipline:** reviewed artifacts are written to `--out-dir`; compacted input files are immutable evidence.

### Next steps

1. Run full test suite and collect counts after this implementation.
2. Consider a later `materialization_summary.schema.json` only if downstream tooling needs to consume the summary as a stable structured contract.
3. Add real SDK runner support when sample assignment and credential path are ready.

### Verification

- `PYTHONPATH=src python3 -m pytest -q -k "materialize_review" tests/test_cli_output_contract.py` → 10 passed.
- `python3 -m py_compile src/assessment_harness/cli.py`
- `PYTHONPATH=src python3 -m pytest tests/test_cli_output_contract.py -q` → CLI contract suite passed.
- `PYTHONPATH=src python3 -m pytest --collect-only -q` → 258 tests collected: agent-runner 27, CLI 99, compacting 7, fixtures 8, models 22, rules 95.
- `PYTHONPATH=src python3 -m pytest -q` → full suite passed.
