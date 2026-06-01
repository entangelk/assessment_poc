# Work Log - 2026-06-01

## Publication Mirror Boundary + Phase 2 Resume

### Goals

- Correct the publication-plan handoff so bilingual mirroring does not start from a false assumption that showcase documents are stable.
- Record the Owner's direction to resume Phase 2 implementation work before final publication mirroring.

### Completed work

- Updated `docs/publication_plan_v1.md` §7b to remove the split between "moving" and "stabilizing" documents.
  - Key change: all docs are mirrored only once, after product development and publication copy both freeze.
  - Effect: avoids translating publication drafts that may still change as Phase 2 work changes README, evaluation, case study, or decision framing.
- Updated `HANDOFF.md` publication notes.
  - Key change: publication docs are now explicitly described as drafted, not frozen.
  - Key change: `docs/daily_logs/2026-06-01/work_log.md` is the baseline for later publication-doc delta review; a final mirror pass should inspect document changes from this log forward before translating.

### Issues found

- Problem: prior handoff wording called `decisions.md` "frozen" and described newly-authored showcase docs as if they could be mirrored before the rest of development was complete.
  Cause: the publication pass treated some documents as stable because they had been drafted, while the project itself still has Phase 2 work pending.
  Resolution: changed the mirroring rule to one final all-doc mirror pass and recorded a concrete baseline date for future delta review.
  Outcome: publication translation is deferred until it can reflect the final project state without repeated rework.

### Decisions

- **Owner decision (2026-06-01): all bilingual mirroring waits until everything is complete.** Even showcase documents drafted on 2026-05-31 are not stable while development continues. The final mirror pass should use this work log as the baseline and review changes from here forward before translating.
- **Owner direction (2026-06-01): resume Phase 2 work next.** Publication docs remain as drafts until the implementation catches up; final mirroring and visibility flip stay at the end.

### Next steps

1. Resume Phase 2 implementation from the current helper foundation.
2. Choose the next smallest Phase 2 slice that does not require unresolved external credentials: likely compacting/id-map groundwork or mock-runner-driven CLI orchestration.
3. Keep publication docs in sync only when implementation changes affect a stated public fact; defer KO/EN mirror generation until final freeze.

### Verification

- Documentation-only change for the publication mirror boundary.
- Confirmed the changed publication-boundary files were limited to publication/handoff/work-log documentation before Phase 2 implementation began.

## Phase 2 Compacting Schema / Helper Foundation

### Goals

- Resume Phase 2 with the smallest slice that does not require external SDK credentials or unresolved tool side-effect policy.
- Add a deterministic compacting helper that preserves the project's core compacting invariant: union-based, no automatic acceptance/exclusion of valid candidates, with support/variants/id lineage visible for human review.

### Completed work

- Added `schemas/compacting.schema.json` and registered it in `src/assessment_harness/schemas.py`.
  - Key change: compacted artifacts now have a schema surface covering `spec_items`, `rubric_items`, `trace_links`, and `id_map`.
  - Effect: Phase 2 compacting output can be validated directly instead of only validating its separate component files.
- Added `src/assessment_harness/compacting.py`.
  - Key change: `compact_validated_candidates(candidate_runs, policy)` compacts only fully `validated` runs, groups candidates by configured `policy.compacting.identity_basis`, preserves `support`, `identity_basis`, and all original proposals in `variants`, and emits canonical `id_map` entries.
  - Key change: trace links are remapped from run-local spec/rubric IDs to canonical compacted IDs before trace-link identity is computed.
  - Key change: `support.total_valid_runs` is the count of fully validated input runs, including runs that do not contain a given compacted identity.
  - Key change: trace-link remap failures now raise `CompactingInputError` instead of silently dropping the trace link.
  - Effect: the helper now locks the core union compacting behavior without introducing the `compact` CLI command, real SDK runners, review queue composition, or runner recovery policy.
- Added `tests/test_compacting.py`.
  - Covered single-run preservation, multi-run union/id_map lineage, mixed-status run exclusion, denominator behavior for item support, raw variant preservation after normalized identity matching, evidence quote spec-id remapping, unmapped trace-reference rejection, and distinct-identity splitting.
- Updated `HANDOFF.md`, `CHANGELOG.md`, and package docstring to reflect that this is helper-level Phase 2 compacting foundation only.
- Added `docs/verifications/2026-06-01/phase2_compacting_helper_feedback.md` for the Owner-requested check of the external AI review findings.
- Removed the unused `id_map_document` `$defs` entry from `schemas/compacting.schema.json` after a follow-up cleanup note. The standalone wrapper contract is already covered by `id_map.schema.json` plus the compacting test that validates `{"id_map": compacted["id_map"]}`.

### Issues found

- Problem: the first `compacting.schema.json` draft used cross-file `$ref`s such as `spec_items.schema.json#/$defs/spec_item`.
  Cause: the local schema helper does not preload a resolver store for repo-local schema IDs, so `jsonschema` attempted to resolve `https://assessment-harness/...` over the network.
  Resolution: rewrote `compacting.schema.json` with local `$defs` for the compacting envelope and provenance fields.
  Outcome: schema validation stays offline and matches the repository's current schema-loading style.
- Problem: independent review found the first helper treated `integrity_status` as an entry-level compacting gate even though the plan describes compacting as consuming valid runs.
  Cause: candidate schema stores `integrity_status` on entries, and the first helper filtered entries directly instead of reconciling that storage detail with the run-level contract.
  Resolution: the helper now first identifies fully validated runs; if any candidate entry in a candidate-run artifact is non-validated or malformed, that run is excluded as a unit.
  Outcome: mixed-status runs cannot be partially consumed.
- Problem: independent review found `support.total_valid_runs` was inferred from runs that had at least one compacted candidate, not all valid runs.
  Cause: the denominator reused the entry-filtering helper.
  Resolution: `total_valid_runs` now counts all fully validated input runs, while `found_in_runs` records only runs that proposed that compacted identity.
  Outcome: low-support style decisions will not be distorted by denominator undercounting in this helper.
- Problem: independent review found untested boundary behavior around raw variants, evidence quote remapping, and unmapped trace references.
  Cause: the first tests covered only identical raw candidates and happy-path trace remapping.
  Resolution: added explicit regressions for normalized-same/raw-different variants, evidence quote `spec_id` remapping, and unmapped trace reference rejection.
  Outcome: those boundaries are locked at the helper level.
- Problem: follow-up review found an orphan `id_map_document` definition in `compacting.schema.json`.
  Cause: the compacting schema originally carried a local wrapper def while the actual standalone wrapper validation uses `id_map.schema.json`.
  Resolution: removed the unused definition.
  Outcome: schema surface is smaller and avoids implying a second wrapper contract.

### Decisions

- **Implementation slice boundary:** compacting begins as a pure helper plus schema, not a CLI command. Rationale: it verifies the deterministic core contract while avoiding unresolved external-runner concerns.
- **Compacting eligibility:** only fully `validated` runs are compacted. Non-validated or mixed-status runs are excluded from compacted artifacts in this helper; later orchestration/review_queue work will decide how to surface excluded-run review entries.
- **Standalone id_map output:** the compacted bundle stores `id_map` as an array property, while the standalone `id_map.schema.json` requires an `{id_map: [...]}` wrapper. Future `compact` CLI work must wrap this array when writing `id_map.yaml`; the current helper test validates that wrapper shape explicitly.

### Next steps

1. Add `compact` CLI orchestration around the helper: read one or more validated candidate-run artifacts, load policy, write compacted `spec_items.yaml` / `rubric_items.yaml` / `trace_links.yaml` / `id_map.yaml` or a compacted bundle.
2. Define how invalid/excluded candidate runs enter `review_queue` without overwriting existing Phase 0 lint safeguard entries.
3. After CLI orchestration exists, add a smoke proving compacted output can feed existing `check` and produce the same deterministic findings as manual compacted YAML.

### Verification

- `python3 -m py_compile src/assessment_harness/compacting.py src/assessment_harness/schemas.py`
- `python3 -m pytest tests/test_compacting.py tests/test_models.py::test_phase_two_contract_schemas_are_registered_and_validate_plan_examples -q` → 8 passed.
- `python3 -m pytest tests/test_agent_runner_contract.py tests/test_models.py tests/test_compacting.py -q` → 53 passed.
- `python3 -m pytest -q` → full suite passed.
- `python3 -m pytest --collect-only -q` → 207 tests collected: agent-runner 27, CLI 48, compacting 7, fixtures 8, models 22, rules 95.
