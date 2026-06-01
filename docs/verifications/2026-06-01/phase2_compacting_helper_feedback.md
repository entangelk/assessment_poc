# Verification - Phase 2 Compacting Helper Feedback

## Subject metadata

- Date: 2026-06-01
- Requester: Owner
- Verifier: Codex
- Target slice/artifact: Phase 2 compacting schema/helper foundation in working tree
- Canonical spec reference: `docs/implementation_plan_assessment_harness_poc_v1.md` v1.30, scoped to §4 compacting/review_queue, §5.0 canonical ID, §9 Phase 2, and §10.2 compacting contract checks
- Source of work being verified: working tree, uncommitted

## Scope

- External review findings F2, F3, F4/F5, F7, F8.
- Compacting helper behavior in `src/assessment_harness/compacting.py`.
- Compacting/id_map schema surfaces in `schemas/compacting.schema.json` and `schemas/id_map.schema.json`.
- Regression tests in `tests/test_compacting.py`.
- Handoff/work-log/changelog status claims.

## Methodology

- Read scoped contract clauses:
  - `nl -ba docs/implementation_plan_assessment_harness_poc_v1.md | sed -n '136,148p;194,205p;1135,1156p;1207,1211p'`
- Read implementation/test/schema surfaces:
  - `nl -ba src/assessment_harness/compacting.py | sed -n '27,340p'`
  - `nl -ba tests/test_compacting.py | sed -n '1,260p'`
  - `nl -ba schemas/compacting.schema.json | sed -n '1,180p'`
- Ran verification:
  - `python3 -m py_compile src/assessment_harness/compacting.py src/assessment_harness/schemas.py`
  - `python3 -m pytest tests/test_compacting.py tests/test_models.py::test_phase_two_contract_schemas_are_registered_and_validate_plan_examples -q`
  - `python3 -m pytest -q`
  - `python3 -m pytest --collect-only -q`

## Findings

### F2 - Run-level compacting eligibility

External finding upheld. The contract says invalid runs are excluded from compacting, not individual entries only: plan §4 says all candidates except those from invalid runs remain reviewable (`docs/implementation_plan_assessment_harness_poc_v1.md:143`), and Phase 2 criteria say Rule 0-failed runs are excluded (`docs/implementation_plan_assessment_harness_poc_v1.md:1151`).

Resolution: helper now computes fully validated run IDs first (`src/assessment_harness/compacting.py:95-126`) and only iterates candidates whose `agent_run_id` belongs to that run set (`src/assessment_harness/compacting.py:198-220`). Mixed-status regression is locked in `tests/test_compacting.py:182-194`.

### F3 - `support.total_valid_runs` denominator

External finding upheld. Support is intended to report which run found an entity while preserving compacting evidence (`docs/implementation_plan_assessment_harness_poc_v1.md:143`), so the denominator must be valid runs, not matching-candidate runs.

Resolution: `total_valid_runs` now uses the fully validated run set (`src/assessment_harness/compacting.py:247-260`). The over-strict/under-strict boundary is covered by a two-run distinct-identity case where the first item has `total_valid_runs=2` but `found_in_runs=["run_1"]` (`tests/test_compacting.py:197-220`).

### F7 - Boundary locks

External finding upheld.

- Raw variants after normalized identity matching are now covered (`tests/test_compacting.py:223-245`).
- Evidence quote `spec_id` remap is now asserted (`tests/test_compacting.py:102-108`).
- Unmapped trace references now raise `CompactingInputError` (`src/assessment_harness/compacting.py:282-312`) and are covered (`tests/test_compacting.py:248-255`).

Note: the review's one-word `"the"` example would require a looser semantic identity algorithm than the current configured `source+section+normalized_text`; this slice only locks the implemented whitespace/case normalization behavior.

### F4/F5 - Trace provenance and id_map wrapper

Partially upheld.

- Trace links now materialize `sources`, `reviewed_by`, and `reviewed_at` (`src/assessment_harness/compacting.py:260-267`), and the compacting schema requires those fields for compacted trace links (`schemas/compacting.schema.json:64-101`).
- The compacted bundle intentionally stores `id_map` as an array property (`schemas/compacting.schema.json:21-24`), while standalone `id_map.schema.json` remains wrapper-shaped. The current helper test validates the future CLI wrapper shape with `validate("id_map", {"id_map": compacted["id_map"]})` (`tests/test_compacting.py:128-130`). CLI output file layout remains pending, not closed by this slice.

### F8 - Handoff citation

External finding upheld. HANDOFF now cites current plan v1.30 §5.0 / §9 for compacting, not historical v1.4 / unrelated §10.2 (`HANDOFF.md:29`).

## Issues / Risks

- `compact` CLI orchestration is still pending, so standalone file layout for `id_map.yaml` is not yet exercised end-to-end.
- Excluded invalid/mixed runs are not yet written to `review_queue`; plan §4 requires review_queue preservation for excluded candidates, and this remains the next orchestration slice rather than helper behavior.

## Verdict

Conditional pass after follow-up fixes.

Load-bearing reasons: F2, F3, and F7 were valid and have regression coverage; F4 trace provenance is fixed; F5 standalone id_map layout is documented and partially guarded but awaits CLI implementation; F8 is corrected.

## Outstanding items

- Working tree remains uncommitted.
- Next implementation slice should add `compact` CLI orchestration and review_queue composition for excluded candidate runs.

## Reproduction

```bash
python3 -m py_compile src/assessment_harness/compacting.py src/assessment_harness/schemas.py
python3 -m pytest tests/test_compacting.py tests/test_models.py::test_phase_two_contract_schemas_are_registered_and_validate_plan_examples -q
python3 -m pytest -q
python3 -m pytest --collect-only -q
```
