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
