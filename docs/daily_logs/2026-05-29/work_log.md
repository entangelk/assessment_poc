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
