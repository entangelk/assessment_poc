# Work Log - 2026-06-04

## Publication Evaluation Snapshot Refresh

### Goals

- Read the current handoff and latest daily log to identify the next feasible task.
- Recompute the publication-facing evaluation snapshot from real test and smoke output.
- Keep publication docs honest while avoiding premature implementation of underspecified trace-link/status materialization.

### Completed work

- Updated `docs/evaluation.md`.
  - Key change: refreshed the dated moving snapshot from 2026-05-31 to 2026-06-04.
  - Key change: updated the full-suite count from `200 passed`; the final same-day snapshot is `268 passed` after the later `materialize-review` guard follow-up and summary-schema stabilization.
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

- `PYTHONPATH=src python3 -m pytest --collect-only -q` → initial refresh snapshot before `materialize-review`: 248 tests collected (agent-runner 27, CLI 89, compacting 7, fixtures 8, models 22, rules 95). Superseded later in this log by the 268-test snapshot after `materialize-review` guard follow-up and summary-schema stabilization.
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

## `materialize-review` Contract Guard Follow-up

### Goals

- Resolve the owner-identified ambiguity around spec/rubric materialization wording.
- Close the conditional verification gaps where existing `materialize-review` behavior was implemented but not locked by regression tests.
- Keep the public contract stable while adding only the missing guard coverage.

### Completed work

- Updated `docs/implementation_plan_assessment_harness_poc_v1.md`.
  - Key change: clarified that `spec_item` / `rubric_item` decisions do not produce a failure verdict (`invalid_input`) by themselves.
  - Key change: clarified that those deferred-scope decisions preserve input artifacts and are counted in `materialization_summary.json` as `unsupported_decision_count`.
  - Effect: the field name and prose no longer require the next worker to guess whether "판정" means a failure verdict or a summary tally.
- Added `materialize-review` regressions in `tests/test_cli_output_contract.py`.
  - Locks rejection of non-minimal trace keys such as `{rubric_id, spec_ids}`.
  - Locks rejection when one canonical `trace_link_id` maps to multiple trace links.
  - Locks spec/rubric decision preservation plus `unsupported_decision_count`.
  - Locks finding decisions as `gate`-only inputs that do not materialize artifacts.
  - Locks review_queue duplicate-entry, duplicate-decision, missing-entry, and no-queue-input guards.
- Updated `docs/evaluation.md`, `HANDOFF.md`, and `CHANGELOG.md`.
  - Effect: project status and measured test counts now reflect the 268-test suite and the closed materialization guard gaps.

### Issues found

- Problem: `materialize-review` had correct defensive code for several contract branches, but the tests did not trace every branch.
  Cause: the first implementation focused on the main action/status paths and only two trace-link invalid-input cases.
  Resolution: added eight focused CLI regressions for the previously untraced branches.
  Outcome: the conditional verification reason is addressed in the test suite rather than relying on smoke output or code reading.
- Problem: the contract phrase "지원하지 않는 materialization으로 판정하지 않는다" could be read as conflicting with `unsupported_decision_count`.
  Cause: the prose did not distinguish a failure verdict from a summary count.
  Resolution: applied the owner-selected minimal wording: no `invalid_input` verdict, preserve artifacts, count deferred spec/rubric decisions in `unsupported_decision_count`.
  Outcome: code behavior and canonical contract wording now align without changing the public field name.

### Decisions

- **Owner contract interpretation:** for `spec_item` / `rubric_item` final-review decisions, "not judged as unsupported materialization" means no failure verdict. The decisions are still counted in `unsupported_decision_count` because they are deferred-scope materialization work.
- **Scope discipline:** no runtime code change was needed; the follow-up only clarified the contract and added regression guards for existing behavior.

### Next steps

1. Add a `materialization_summary.schema.json` only if downstream tooling starts consuming the summary as a stable structured artifact.
2. Add real SDK runner support when sample assignment and credential path are ready.
3. Recompute `docs/evaluation.md` again at publication freeze, then perform the deferred bilingual mirrors.

### Verification

- `PYTHONPATH=src python3 -m pytest -q -k "materialize_review" tests/test_cli_output_contract.py` → 18 passed.
- `PYTHONPATH=src python3 -m pytest tests/test_cli_output_contract.py -q` → 107 passed.
- `PYTHONPATH=src python3 -m pytest --collect-only -q` → 266 tests collected: agent-runner 27, CLI 107, compacting 7, fixtures 8, models 22, rules 95.
- `PYTHONPATH=src python3 -m pytest -q` → full suite passed.

## `materialize-review` Trace Duplicate Decision Guard

### Goals

- Re-check the materialize-review boundary matrix after owner feedback.
- Close the remaining trace-link duplicate-decision guard that was accidentally conflated with the queue duplicate-decision guard.

### Completed work

- Added `test_materialize_review_rejects_duplicate_trace_link_decisions` in `tests/test_cli_output_contract.py`.
  - Key change: writes two `target_type: trace_link` decisions with the same `target_key: {trace_link_id: T1}`.
  - Effect: the `final review contains duplicate decisions for one trace link` invalid-input path is now directly pinned.
- Updated `docs/evaluation.md` and `HANDOFF.md`.
  - Effect: current measured counts now reflect 268 total tests and 109 CLI contract tests.

### Issues found

- Problem: the prior guard follow-up claimed duplicate decision coverage, but the added test exercised the review_queue duplicate-decision path only.
  Cause: the trace and queue paths use similar wording but different code paths.
  Resolution: added the missing trace-specific duplicate-decision regression and re-ran focused/CLI/full suites.
  Outcome: the matrix no longer has the remaining trace duplicate-decision empty cell.

### Decisions

- **No commit/push without owner request:** per owner instruction after the prior accidental push, this follow-up remains uncommitted until explicitly requested.

### Next steps

1. Commit/push only when the owner asks.
2. Add real SDK runner support when sample assignment and credential path are ready.

### Verification

- `PYTHONPATH=src python3 -m pytest -q -k "materialize_review" tests/test_cli_output_contract.py` → 19 passed.
- `PYTHONPATH=src python3 -m pytest tests/test_cli_output_contract.py -q` → 108 passed.
- `PYTHONPATH=src python3 -m pytest --collect-only -q` → 267 tests collected: agent-runner 27, CLI 108, compacting 7, fixtures 8, models 22, rules 95.
- `PYTHONPATH=src python3 -m pytest -q` → full suite passed.
- `python3 -m py_compile src/assessment_harness/cli.py src/assessment_harness/schemas.py`

## Materialization Summary Schema

### Goals

- Turn `materialization_summary.json` from a best-effort informational file into a schema-validated artifact.
- Keep the schema limited to the fields that `materialize-review` already emits.
- Avoid changing the public CLI envelope or materialization behavior.

### Completed work

- Added `schemas/materialization_summary.schema.json`.
  - Key change: requires `review_id`, the three decision counters, and `output_paths`.
  - Key change: accepts optional `source_paths`, including `source_paths.review_queue_path: null` when no review queue was materialized.
  - Effect: downstream agents can validate the materialization summary before consuming artifact paths and counts.
- Registered the schema in `src/assessment_harness/schemas.py`.
  - Effect: the existing `validate()` and loader helpers can discover the new schema by name.
- Updated `src/assessment_harness/cli.py`.
  - Key change: validates the generated summary before writing `materialization_summary.json`.
  - Effect: a future code change that breaks the summary contract fails loudly instead of writing a malformed artifact.
  - Follow-up fix: corrected the generated-summary schema-failure path to call `_materialize_invalid_input` and moved summary validation before all reviewed artifact writes.
- Updated tests.
  - `tests/test_models.py` now locks schema registration and a representative valid summary.
  - `tests/test_models.py` also locks that `source_paths` remains optional under the minimum summary contract.
  - `tests/test_cli_output_contract.py` now validates the summary produced by the end-to-end `materialize-review` path and forces the generated-summary schema-failure branch.
- Updated `HANDOFF.md` and `CHANGELOG.md`.
  - Effect: current project status now reflects sixteen JSON Schemas and the schema-validated materialization summary.

### Issues found

- Problem: `materialization_summary.json` was described as an output contract but had no schema registration or generated-artifact validation.
  Cause: the initial materialization slice kept the summary as a lightweight informational JSON file.
  Resolution: added a minimal schema and validated the generated summary before writing it.
  Outcome: the artifact remains backward-compatible while becoming machine-checkable.
- Problem: the generated-summary validation failure path called an undefined `_materialize_review_invalid_input`.
  Cause: typo against the existing `_materialize_invalid_input` helper, and the first tests only covered valid summaries.
  Resolution: fixed the helper call and added a monkeypatched regression that forces summary validation failure.
  Outcome: generated-summary schema failure now returns `invalid_input`/exit `2` instead of falling through to top-level `internal_error`.
- Problem: `source_paths` was required by the schema even though §5.6.1 only requires review ID, decision counts, and output paths as the minimum summary contract.
  Cause: the schema mirrored current implementation metadata rather than the contractual minimum.
  Resolution: kept `source_paths` supported but no longer required.
  Outcome: the schema is aligned with the minimal public contract while accepting today's richer summary.

### Decisions

- **Minimal schema:** keep `additionalProperties: true` and require only the fields listed in the §5.6.1 minimum contract. This preserves future metadata flexibility while pinning the current stable surface.
- **No envelope change:** the CLI envelope already reports the summary path and counts; this slice only validates the on-disk summary artifact.
- **Failure classification:** generated-summary schema failure returns `invalid_input`/exit `2` through the existing materialize-review error envelope so caller agents get a structured recovery path.

### Next steps

1. Add real SDK runner support when sample assignment and credential path are ready.
2. Recompute `docs/evaluation.md` again at publication freeze, then perform the deferred bilingual mirrors.

### Verification

- `PYTHONPATH=src python3 -m pytest tests/test_models.py -q` → 22 passed.
- `PYTHONPATH=src python3 -m pytest -q -k "materialize_review" tests/test_cli_output_contract.py` → 20 passed.
- `PYTHONPATH=src python3 -m pytest tests/test_cli_output_contract.py -q` → 109 passed.
- `PYTHONPATH=src python3 -m pytest --collect-only -q` → 268 tests collected: agent-runner 27, CLI 109, compacting 7, fixtures 8, models 22, rules 95.
- `PYTHONPATH=src python3 -m pytest -q` → full suite passed.
- `python3 -m py_compile src/assessment_harness/cli.py src/assessment_harness/schemas.py`
