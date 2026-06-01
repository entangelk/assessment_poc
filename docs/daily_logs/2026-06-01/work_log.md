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

## Phase 2 Initial `compact` CLI Orchestration

### Goals

- Put a thin CLI layer around the compacting helper without introducing real SDK runners or `extract` / `verify`.
- Close the previously deferred standalone `id_map.yaml` wrapper and invalid-run review_queue composition surfaces.

### Completed work

- Added `compact` to `src/assessment_harness/cli.py`.
  - Inputs: plan-canonical `--runs-dir` (reads `*/candidates.yaml` and `*.candidates.yaml` in sorted order) or low-level `--candidates` explicit files, `--policy`, `--out-dir`, optional `--review-queue-in`, optional `--review-queue-out`.
  - Outputs: `spec_items.yaml`, `rubric_items.yaml`, `trace_links.yaml`, wrapper-shaped `id_map.yaml`, and `review_queue.json`.
  - Envelope: `status=success`, exit `0`, and informational paths/counts (`valid_run_count`, `excluded_run_count`, `review_queue_count`, output paths).
- Added schema self-discovery for `schema --command compact`.
- Added CLI contract regressions.
  - Happy path locks canonical YAML output, standalone `id_map` wrapper validation, and remapped trace IDs.
  - `--runs-dir` path locks the plan §8 command shape; simultaneous `--runs-dir` + `--candidates` is rejected.
  - Mixed/non-validated run path locks exclusion from compacted artifacts, appended `invalid_run` review_queue entry, preservation of a pre-existing queue entry/top-level metadata from `--review-queue-in`, and no duplicate append when the same `invalid_run` entry already exists.
  - Grounded smoke locks that `compact` output can feed the existing `check` flow.
- Updated README, HANDOFF, and CHANGELOG to mark initial `compact` CLI orchestration as live while keeping `extract`, `verify`, real SDK runners, and full E2E pending.

### Issues found

- Problem: README still described `compact` as fully unimplemented.
  Cause: publication docs are drafts, but public implementation-status facts still need to move with development.
  Resolution: updated README to describe `compact` as partially implemented and keep the plan-canonical `--runs-dir` input form.
  Outcome: README no longer contradicts the CLI surface.
- Problem: follow-up review found the first CLI slice silently implemented `--candidates` while plan §8 specified `compact --runs-dir work/runs`.
  Cause: `extract` is not implemented yet, so explicit candidate files were practical for the first CLI tests, but the plan-canonical signature was not supported.
  Resolution: added `--runs-dir` support and made `--candidates` an explicit low-level alternate input; passing both is invalid.
  Outcome: implementation and README now accept the plan §8 command shape without removing the practical interim file-list path.
- Problem: review_queue composition had low-risk drift/duplication hazards.
  Cause: CLI had a local valid-run predicate, copied only `review_queue` from incoming queue documents, and appended deterministic `invalid_run_{index}` entries without checking existing IDs.
  Resolution: CLI now reuses `validated_candidate_run_id`, preserves incoming queue top-level metadata, and skips `invalid_run` entries whose `entry_id` already exists.
  Outcome: envelope counts track helper eligibility, queue metadata survives, and repeated compaction with a previous queue does not duplicate the same invalid-run entry.

### Decisions

- **CLI slice boundary:** `compact` now accepts plan-canonical run directories via `--runs-dir` and retains `--candidates` as a low-level explicit artifact input. It does not run agents or perform `extract` / `verify`.
- **Review queue composition:** `compact` preserves incoming review_queue entries when `--review-queue-in` is provided and appends its own `invalid_run` entries. This closes the Phase 2 "do not overwrite lint safeguard entries" concern for the compacting slice.
- **Owner confirmation on C1:** support both input modes, but keep plan §8's `--runs-dir` flow as the official contract. `--candidates` remains a practical low-level/manual input path, not the primary documented pipeline.

### Next steps

1. Implement `extract` or mock-runner-driven orchestration that produces candidate artifacts for `compact`.
2. Implement `verify` / semantic-verification queue entries.
3. Recompute publication-facing evaluation tables after the next pipeline slice stabilizes.

### Verification

- `python3 -m py_compile src/assessment_harness/cli.py src/assessment_harness/compacting.py`
- `python3 -m pytest tests/test_cli_output_contract.py::test_schema_command_returns_compact_contract tests/test_cli_output_contract.py::test_compact_cli_writes_canonical_yaml_and_id_map_wrapper tests/test_cli_output_contract.py::test_compact_cli_preserves_existing_queue_and_records_invalid_run -q` → 3 passed.
- `python3 -m pytest tests/test_cli_output_contract.py::test_compact_cli_accepts_plan_canonical_runs_dir tests/test_cli_output_contract.py::test_compact_cli_preserves_existing_queue_and_records_invalid_run tests/test_cli_output_contract.py::test_compact_cli_does_not_duplicate_existing_invalid_run_entry tests/test_cli_output_contract.py::test_compact_cli_rejects_runs_dir_and_candidates_together -q` → 4 passed.
- `python3 -m pytest tests/test_cli_output_contract.py tests/test_compacting.py tests/test_models.py -q` → 84 passed.
- `python3 -m pytest tests/test_cli_output_contract.py::test_compact_output_feeds_existing_check_flow -q` → 1 passed.
- `python3 -m pytest -q` → full suite passed.
- `python3 -m pytest --collect-only -q` → 214 tests collected: agent-runner 27, CLI 55, compacting 7, fixtures 8, models 22, rules 95.

## Phase 2 Initial `extract` CLI Orchestration (`mock_fixture`)

### Goals

- Add the smallest `extract` producer that can feed the plan-canonical `compact --runs-dir` path.
- Keep real SDK runner work deferred until a real sample is ready, per Owner direction.

### Completed work

- Added `extract` to `src/assessment_harness/cli.py` for `--runner mock_fixture`.
  - Inputs: `--spec`, `--rubric`, `--runner mock_fixture`, `--fixture-dir`, `--runs`, optional `--source-manifest`, optional `--policy`, and `--out-dir`.
  - Output layout: `run_###/candidates.yaml`, `run_###/agent_trace.audit.jsonl`, and `run_###/agent_trace.raw.jsonl`.
  - Behavior: replays fixture artifacts through `MockFixtureRunner`, rewrites run IDs per pass, normalizes candidates, and runs deep candidate Rule 0 so clean fixture runs become `validated`.
- Added schema self-discovery for `schema --command extract`.
- Added CLI regressions for extract.
  - Locks `mock_fixture` candidate/trace output, candidate schema validity, audit trace schema validity, per-run provenance, and default fixture `source_manifest.yaml` discovery.
  - Locks invalid-run isolation with `reference_integrity`: invalid candidate status is preserved, `valid_run_count=0`, `invalid_run_count=1`, and run-local `integrity_diagnostics.json` is written.
  - Locks extract write-before-validate parity with compact: generated candidates, audit trace events, and run-local integrity diagnostics are schema-validated before write.
  - Locks `extract -> compact --runs-dir` compatibility.
  - Locks unsupported runner rejection so `claude_sdk` remains explicitly deferred rather than silently stubbed.
  - Locks the plan run-count boundary (`1..7`).
- Updated README, HANDOFF, CHANGELOG, and case study status text to mark mock-only `extract` as initially live while keeping `verify`, real SDK runners, and production snapshot generation pending.

### Issues found

- Problem: the first implementation made `--source-manifest` required for `extract`, while plan §8's official `extract` command does not include that flag.
  Cause: mock fixture deep-validation needs a source snapshot, and the existing fixture already carries `source_manifest.yaml`.
  Resolution: made `--source-manifest` optional; when omitted for `mock_fixture`, `extract` reads `source_manifest.yaml` from `--fixture-dir`.
  Outcome: the mock path can validate candidates without changing the plan-canonical command shape.
- Problem: follow-up review found the invalid-run branch was functional but lacked a regression, and its first debug artifact name (`integrity_errors.json`) did not match the plan's `integrity_diagnostics.json` vocabulary.
  Cause: the happy-path slice focused on producing compactable runs and only surfaced invalid runs through counts.
  Resolution: added a `reference_integrity` extract regression and changed the run-local failure artifact to schema-valid `integrity_diagnostics.json`.
  Outcome: failure isolation is now locked and uses the canonical diagnostics name.
- Problem: follow-up review noted `_with_extract_run_id` would overwrite real SDK runner provenance once non-mock runners exist.
  Cause: deterministic mock replay needs synthetic per-pass run IDs, but the first helper was not explicitly mock-scoped.
  Resolution: renamed and scoped the rewrite to `MockFixtureRunner` only.
  Outcome: future real runners can preserve their own run IDs.
- Problem: final follow-up review noted extract wrote candidates/trace/diagnostics without the validate-before-write parity already used by `compact`.
  Cause: tests validated output after write, but the CLI did not fail loud before writing malformed generated artifacts.
  Resolution: added pre-write validation for generated candidates, audit trace events, and integrity diagnostics, plus a malformed mock fixture regression.
  Outcome: extract now matches compact's fail-loud output discipline.

### Decisions

- **Owner direction:** implement `mock_fixture` extract first and defer real SDK runner work until a real sample is ready.
- **CLI slice boundary:** `extract` currently proves orchestration with the existing mock runner only. It does not implement SDK credentials, framework tools, source-snapshot generation from arbitrary assignment files, runner failure recovery, or semantic `verify`.

### Next steps

1. Implement `verify` / semantic-verification queue entries.
2. Add real SDK runner support when a runnable sample assignment is ready.
3. Recompute publication-facing evaluation tables after the next pipeline slice stabilizes.

### Verification

- `python3 -m py_compile src/assessment_harness/cli.py`
- `python3 -m pytest tests/test_cli_output_contract.py::test_schema_command_returns_extract_contract tests/test_cli_output_contract.py::test_extract_mock_fixture_writes_validated_candidate_runs tests/test_cli_output_contract.py::test_extract_mock_fixture_output_feeds_compact_runs_dir tests/test_cli_output_contract.py::test_extract_mock_fixture_isolates_invalid_run_with_diagnostics tests/test_cli_output_contract.py::test_extract_validates_generated_candidates_before_write tests/test_cli_output_contract.py::test_extract_mock_fixture_rejects_unknown_runner tests/test_cli_output_contract.py::test_extract_rejects_runs_outside_plan_limit -q` → 7 passed.
- `python3 -m pytest tests/test_cli_output_contract.py tests/test_agent_runner_contract.py tests/test_compacting.py tests/test_models.py -q` → 118 passed.
- `python3 -m pytest -q` → full suite passed.
- `python3 -m pytest --collect-only -q` → 221 tests collected: agent-runner 27, CLI 62, compacting 7, fixtures 8, models 22, rules 95.
