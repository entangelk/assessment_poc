# Work Log - 2026-05-29

## Candidate Artifact Schema Foundation

### Goals

- Continue from the v1.23 audit trace foundation into the smallest Phase 2 contract slice that does not require unresolved runner, identity-basis, compacting, or failure-recovery decisions.
- Register the candidate artifact schema named in the plan so later candidate-to-trace cross-reference and run integrity checks have a stable validation target.

### Completed work

- Promoted the plan to v1.24.
  - Files changed: `docs/implementation_plan_assessment_harness_poc_v1.md`.
  - Key changes: added a v1.24 changelog entry for `candidates.schema.json` as the Phase 2 candidate artifact contract foundation.
  - Effect: candidate schema registration is now described by the canonical implementation plan rather than being an implementation-only surface.
- Added and registered `candidates.schema.json`.
  - Files changed: `schemas/candidates.schema.json`, `src/assessment_harness/schemas.py`.
  - Key changes: validates top-level `spec_item_candidates`, `rubric_item_candidates`, and `trace_link_candidates`; each candidate requires `candidate_id`, `proposed_item`, `agent_runner`, `agent_run_id`, and `integrity_status`; `integrity_status` is limited to the plan §5.4 enum.
  - Effect: future runner outputs can be validated before run integrity checks and compacting, while invalid candidates remain outside deterministic assessment inputs.
- Added schema regressions.
  - Files changed: `tests/test_models.py`.
  - Key changes: the Phase 2 schema registration test now validates a plan-shaped candidate document; negative tests reject missing `agent_run_id`, invalid `integrity_status`, and invalid embedded `proposed_item` shapes across spec/rubric/trace candidates.
  - Effect: candidate provenance, integrity-status drift, and under-strict `proposed_item` structure acceptance are now locked by focused tests.
- Updated current-state documentation.
  - Files changed: `README.md`, `HANDOFF.md`, `CHANGELOG.md`, this work log.
  - Key changes: bumped current plan references to v1.24, updated schema count to fourteen, and recorded candidate artifacts as a live Phase 2 schema foundation.
  - Effect: next workers can build candidate-to-trace checks or runner normalization against an explicit registered schema.

### Issues found

- Problem: plan §5.4 and the module list named candidate artifacts and `candidates.schema.json`, but the repository schema registry did not expose a candidate validation surface.
  Cause: earlier Phase 2 slices deliberately stopped at runner protocol, semantic verification, ID lineage, and audit trace contracts.
  Resolution: added the schema without implementing `extract`, `compact`, `verify`, or failure recovery behavior.
  Outcome: candidate artifact shape is now testable while unresolved Phase 2 policy choices remain deferred.
- Problem: independent verification found that the initial regression matrix did not lock the embedded `proposed_item` structure even though the schema itself rejected invalid shapes.
  Cause: the first test slice covered a valid candidate document, missing `agent_run_id`, and invalid `integrity_status`, but not the `allOf` / `$ref` wiring for the proposed item payload.
  Resolution: added parametrized regressions for invalid spec item payloads, a non-object payload, rubric item missing required fields, trace link enum violation, and a trace-link-shaped payload in a spec candidate slot; tightened the missing `agent_run_id` assertion to pin the error source.
  Outcome: the conditional-pass blocking gap is closed by tests rather than treated as a future risk.

### Decisions

- This slice deliberately keeps candidate artifacts separate from compacted `spec_items`, `rubric_items`, and `trace_links`. Candidate documents are pre-compacting run outputs and must not become deterministic rule inputs directly.
- The schema requires all three candidate arrays, even when a given run emits an empty category, so orchestrator outputs have a stable envelope for later checks.
- Candidate-to-audit-trace cross-reference is still deferred until runner output normalization and run integrity checks exist.

### Next steps

1. Add candidate-to-audit-trace cross-reference checks once runner output normalization exists.
2. Add run integrity handling for schema-invalid or runner-blocked candidates before implementing compacting.
3. Defer `compact` until identity-basis behavior is chosen or explicitly bounded.

### Verification

- Focused model/schema tests: `python3 -m pytest tests/test_models.py -q` passed (21 tests).
- Syntax check: `python3 -m py_compile src/assessment_harness/schemas.py` passed.
- Full suite: `python3 -m pytest -q` passed (176 tests).
- Canonical Docker suite: `docker compose run --rm test -q` passed.
- Collection check: `python3 -m pytest --collect-only -q` reports 4 agent-runner contract, 48 CLI contract, 8 fixture, 21 model, and 95 rule tests.
- Diff hygiene: `git diff --check` passed.

## Candidate Audit Trace Attribution Helper

### Goals

- Continue Phase 2 contract work without entering `extract`, real SDK runner, compacting, identity-basis, or runner failure-recovery policy.
- Implement the plan §10.2 boundary that every candidate `agent_run_id` must be present in the run's audit trace.

### Completed work

- Promoted the plan to v1.25.
  - Files changed: `docs/implementation_plan_assessment_harness_poc_v1.md`.
  - Key changes: recorded `validate_candidate_audit_trace` as a helper-level implementation of candidate/audit trace attribution, explicitly leaving `extract`, compacting, real runners, and recovery policy for later slices.
  - Effect: the helper is tied to the canonical contract rather than becoming an implementation-only validation rule.
- Added the candidate/audit trace validation helper.
  - Files changed: `src/assessment_harness/agent_runners/validation.py`, `src/assessment_harness/agent_runners/__init__.py`.
  - Key changes: validates the candidate artifact schema, validates every audit trace event schema, and checks that candidate `agent_run_id` values in all three candidate arrays have matching audit trace `run_id`s.
  - Effect: future runner normalization and run integrity checks can reuse one tested attribution boundary.
- Added focused runner contract regressions.
  - Files changed: `tests/test_agent_runner_contract.py`.
  - Key changes: tests lock matching-run success, missing trace attribution, candidate schema error surfacing, invalid audit trace event surfacing, and cross-reference checks for spec/rubric/trace candidate sections.
  - Effect: under-strict attribution checks and section-specific blind spots now fail focused tests.
- Updated current-state documentation.
  - Files changed: `README.md`, `HANDOFF.md`, `CHANGELOG.md`, this work log.
  - Key changes: bumped current plan references to v1.25 and recorded candidate audit-trace attribution as live helper-level Phase 2 infrastructure.
  - Effect: next workers can continue into runner output normalization or run integrity handling with the attribution helper already documented.

### Issues found

- Problem: plan §10.2 required every candidate `agent_run_id` to exist in audit trace, but the repository only had independent schemas for candidates and audit trace events.
  Cause: the previous slice intentionally stopped at schema registration and did not connect the two artifact surfaces.
  Resolution: added a helper that validates both surfaces and checks run ID attribution without deciding how real runners emit or recover artifacts.
  Outcome: missing audit trace attribution is now a focused test failure.

### Decisions

- The helper returns a list of human-readable errors, matching the existing schema helper style, rather than raising exceptions or emitting CLI envelopes.
- This slice does not require a finish event for each candidate run ID. The current contract only says the candidate run ID must appear in audit trace; finish-reason recovery behavior remains a later runner-failure slice.

### Next steps

1. Add runner output normalization that can produce candidate artifacts for this helper to consume.
2. Add runner failure/recovery cases for `blocked_by_runner_error`, max-turns, and tool errors.
3. Defer compacting until identity-basis behavior is chosen or explicitly bounded.

### Verification

- Focused runner contract tests: `python3 -m pytest tests/test_agent_runner_contract.py -q` passed (11 tests).
- Syntax check: `python3 -m py_compile src/assessment_harness/agent_runners/base.py src/assessment_harness/agent_runners/mock.py src/assessment_harness/agent_runners/validation.py src/assessment_harness/agent_runners/__init__.py` passed.
- Full suite: `python3 -m pytest -q` passed (183 tests).
- Canonical Docker suite: `docker compose run --rm test -q` passed.
- Collection check: `python3 -m pytest --collect-only -q` reports 11 agent-runner contract, 48 CLI contract, 8 fixture, 21 model, and 95 rule tests.
- Diff hygiene: `git diff --check` passed.

## Runner Artifact Normalization Helper

### Goals

- Continue Phase 2 runner contract work with a small normalization surface that does not implement `extract`, a real SDK runner, compacting, identity-basis, or runner failure recovery.
- Convert the existing mock runner's fixture-shaped artifacts into candidate schema artifacts so the candidate schema and audit-trace attribution helper can be exercised together.

### Completed work

- Promoted the plan to v1.26.
  - Files changed: `docs/implementation_plan_assessment_harness_poc_v1.md`.
  - Key changes: recorded `normalize_result_candidates` as a helper-level runner artifact normalization slice and explicitly left real `extract`, SDK runner, compacting, and recovery policy out of scope.
  - Effect: candidate normalization is now a documented Phase 2 contract surface, not an implicit test helper.
- Added runner artifact normalization.
  - Files changed: `src/assessment_harness/agent_runners/normalization.py`, `src/assessment_harness/agent_runners/__init__.py`.
  - Key changes: converts `AgentRunResult.artifacts` entries from `spec_items`, `rubric_items`, and `trace_links` into `spec_item_candidates`, `rubric_item_candidates`, and `trace_link_candidates`; assigns deterministic run-local candidate IDs (`SC*`, `RC*`, `TC*`); attaches `agent_runner`, `agent_run_id`, and default `integrity_status: pending_check`.
  - Effect: runner outputs can be validated as pre-compacting candidate artifacts before any run integrity or compacting logic is introduced.
- Added normalization regressions.
  - Files changed: `tests/test_agent_runner_contract.py`.
  - Key changes: the mock runner output now normalizes to a `candidates.schema.json`-valid document, passes candidate/audit trace attribution, preserves runner provenance, starts at `pending_check`, and strips compacting-only fields (`support`, `identity_basis`, `variants`, trace provenance/review fields) from `proposed_item`.
  - Effect: fixture replay cannot accidentally masquerade compacted artifacts as pre-compacting candidates.
- Updated current-state documentation.
  - Files changed: `README.md`, `HANDOFF.md`, `CHANGELOG.md`, this work log.
  - Key changes: bumped current plan references to v1.26 and recorded runner artifact normalization as live helper-level Phase 2 infrastructure.
  - Effect: next workers can build run integrity checks on candidate-shaped runner outputs rather than compacted fixture artifacts.

### Issues found

- Problem: after v1.25, the attribution helper existed but the mock runner still exposed only fixture-shaped `spec_items` / `rubric_items` / `trace_links` artifacts.
  Cause: earlier slices intentionally stopped at schema registration and cross-artifact validation, leaving normalization out of scope.
  Resolution: added a helper that converts existing runner result artifacts into candidate documents while keeping real runner/orchestrator behavior deferred.
  Outcome: mock runner contract tests now exercise candidate schema validation and audit-trace attribution on normalized runner output.
- Problem: fixture-shaped artifacts may already carry compacting fields such as `support`, `identity_basis`, and `variants`.
  Cause: grounded fixtures currently represent compacted Phase 0 inputs, not raw runner candidates.
  Resolution: normalization strips compacting-only fields before placing an item under `proposed_item`.
  Outcome: pre-compacting candidate artifacts stay distinct from compacted artifacts.
- Problem: the initial stripping regression explicitly checked spec and trace payloads but did not make the rubric branch visible.
  Cause: all three sections share `_normalize_items`, so rubric behavior was covered indirectly but not named in the boundary matrix.
  Resolution: parametrized the stripping regression across spec/rubric/trace candidate sections.
  Outcome: compacting-only field stripping is now visibly locked for all normalized candidate categories.
- Problem: `_normalize_items` silently converted missing or malformed artifact sections into empty candidate arrays.
  Cause: defensive guards were added before a malformed runner-output recovery contract existed.
  Resolution: removed the guards and let malformed artifact shape fail at the normalization boundary instead of becoming a valid empty candidate document.
  Outcome: the helper no longer hides malformed runner output behind successful empty normalization.

### Decisions

- Candidate IDs are deterministic run-local IDs using `SC*`, `RC*`, and `TC*` prefixes. They are only normalization output and do not claim canonical ID lineage.
- Normalization assumes the runner result has the expected fixture-shaped artifact sections. Schema validation and run integrity handling for malformed real runner output remain later slices; this helper should not silently turn malformed artifacts into empty valid candidate documents.

### Next steps

1. Add run integrity handling that consumes normalized candidate artifacts and distinguishes schema violation from validated candidates.
2. Add runner failure/recovery cases for `blocked_by_runner_error`, max-turns, and tool errors.
3. Defer compacting until identity-basis behavior is chosen or explicitly bounded.

### Verification

- Focused runner contract tests: `python3 -m pytest tests/test_agent_runner_contract.py -q` passed (15 tests).
- Syntax check: `python3 -m py_compile src/assessment_harness/agent_runners/base.py src/assessment_harness/agent_runners/mock.py src/assessment_harness/agent_runners/normalization.py src/assessment_harness/agent_runners/validation.py src/assessment_harness/agent_runners/__init__.py` passed.
- Full suite: `python3 -m pytest -q` passed (187 tests).
- Canonical Docker suite: `docker compose run --rm test -q` passed.
- Collection check: `python3 -m pytest --collect-only -q` reports 15 agent-runner contract, 48 CLI contract, 8 fixture, 21 model, and 95 rule tests.
- Diff hygiene: `git diff --check` passed.

## Normalized Candidate Run Integrity Helper / Staged Model Reconciliation

### Goals

- Continue Phase 2 run-isolation work without implementing deep Rule 0 candidate validation, runner failure recovery, invalid-run review queue entries, compacting, or real runners.
- Classify normalized candidate artifacts before deep candidate Rule 0 validation without over-claiming final `validated` status.
- Reconcile the contract so structural validation and compacting eligibility are separate stages.

### Completed work

- Promoted the plan to v1.27, then reconciled the status vocabulary in v1.28.
  - Files changed: `docs/implementation_plan_assessment_harness_poc_v1.md`.
  - Key changes: recorded `classify_candidate_run_integrity` as a helper-level structural classifier; added staged `integrity_status` semantics where `structurally_validated` means schema + audit attribution passed, while `validated` remains reserved for later deep candidate Rule 0 success and compacting eligibility; added `trace_attribution_error` so audit trace attribution failures do not reuse `invalid_reference`.
  - Effect: candidate run integrity classification is now a documented Phase 2 contract surface without weakening the meaning of `validated`.
- Added normalized candidate run integrity classification.
  - Files changed: `src/assessment_harness/agent_runners/integrity.py`, `src/assessment_harness/agent_runners/__init__.py`.
  - Key changes: returns a frozen `CandidateRunIntegrityResult` with run-level `integrity_status`, candidate copies, and errors; marks clean structural candidate/audit trace inputs as `structurally_validated`; classifies candidate or audit trace schema errors as `schema_violation`; classifies missing audit trace run attribution as `trace_attribution_error`.
  - Effect: later deep candidate Rule 0 validation can promote only truly clean runs to `validated`, while structural and attribution failures keep machine-readable reasons.
- Added focused run integrity regressions.
  - Files changed: `tests/test_agent_runner_contract.py`.
  - Key changes: tests lock clean structural-run `structurally_validated` behavior, no mutation of original normalized candidates, candidate schema error classification, audit trace schema error classification, trace attribution `trace_attribution_error`, schema-valid attribution-error output, and the reproduced dangling internal reference case staying below `validated`.
  - Effect: schema errors, trace attribution errors, and deferred deep Rule 0 checks cannot collapse into one undifferentiated failure state.
- Updated current-state documentation.
  - Files changed: `README.md`, `HANDOFF.md`, `CHANGELOG.md`, this work log.
  - Key changes: bumped current plan references to v1.28 and recorded staged candidate run integrity classification as live helper-level Phase 2 infrastructure.
  - Effect: next workers can add deeper candidate Rule 0 checks or invalid-run queue entries on top of a small tested classifier.

### Issues found

- Problem: normalized candidates could be schema-valid and audit-trace-attributed, but there was no helper that actually promoted them out of `pending_check`.
  Cause: v1.26 stopped at normalization and cross-artifact validation.
  Resolution: added `classify_candidate_run_integrity` to produce `structurally_validated` copies when schema + audit attribution succeeds.
  Outcome: clean normalized runs now have an explicit structural state without claiming deep Rule 0 success.
- Problem: candidate schema errors and missing audit trace run attribution both surfaced as generic validation errors.
  Cause: `validate_candidate_audit_trace` intentionally returns a flat error list.
  Resolution: classified `candidates:` and `audit_trace/` errors as `schema_violation`, and pure attribution errors as `trace_attribution_error`.
  Outcome: early run isolation can distinguish malformed output from missing trace attribution without overloading `invalid_reference`.
- Problem: independent verification showed that v1.27 over-claimed `validated`, even though deep candidate Rule 0 checks for internal dangling references and quote mismatches were still deferred.
  Cause: the helper treated "schema + audit attribution passed" as if it meant "all Rule 0 passed".
  Resolution: added staged status semantics, changed clean structural runs to `structurally_validated`, kept `validated` reserved for deep Rule 0 success, and added a regression using dangling internal references to prove the classifier no longer emits `validated`.
  Outcome: compacting can continue to rely on `validated` as the only safe status once deep Rule 0 exists.

### Decisions

- The helper does not mutate the input candidate document. It returns a copy with updated `integrity_status` so callers can retain the original normalized artifact if needed.
- `validated` remains a terminal deep Rule 0 success status and compacting gate. The structural classifier must not emit it.
- Missing audit trace run attribution is classified as `trace_attribution_error`, not `schema_violation` or `invalid_reference`, because the candidate and trace documents can both be schema-valid while the run attribution is broken. `invalid_reference` is reserved for candidate-internal dangling references.
- This slice deliberately does not create `review_queue` `invalid_run` entries. Queue composition remains deferred until invalid-run retention/review policy is implemented.

### Next steps

1. Add deeper candidate Rule 0 integrity checks that promote `structurally_validated` runs to `validated` or isolate them as `invalid_reference` / `quote_mismatch`.
2. Add invalid-run review_queue entries once retention/review policy is ready.
3. Add runner failure/recovery cases for `blocked_by_runner_error`, max-turns, and tool errors.
4. Defer compacting until identity-basis behavior is chosen or explicitly bounded.

### Verification

- Focused runner contract tests: `python3 -m pytest tests/test_agent_runner_contract.py -q` passed (20 tests).
- Syntax check: `python3 -m py_compile src/assessment_harness/agent_runners/base.py src/assessment_harness/agent_runners/mock.py src/assessment_harness/agent_runners/normalization.py src/assessment_harness/agent_runners/validation.py src/assessment_harness/agent_runners/integrity.py src/assessment_harness/agent_runners/__init__.py` passed.
- Full suite: `python3 -m pytest -q` passed (192 tests).
- Canonical Docker suite: `docker compose run --rm test -q` passed.
- Collection check: `python3 -m pytest --collect-only -q` reports 20 agent-runner contract, 48 CLI contract, 8 fixture, 21 model, and 95 rule tests.
- Diff hygiene: `git diff --check` passed.
