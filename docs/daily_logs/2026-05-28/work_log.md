# Work Log - 2026-05-28

## Initial Gate / Final Review Finding Mapping

### Goals

- Start the next contracted area after Rule 0-3 and lint L1/L5/L6: `gate`.
- Resolve the final-review-to-finding mapping before implementation so review records do not copy excessive finding payload data.
- Add the smallest useful vertical slice: final review schema, `gate` command, public CLI contract tests, and fixture-level gate regression.

### Completed Work

- Promoted the canonical plan to v1.16.
  - Files changed: `docs/implementation_plan_assessment_harness_poc_v1.md`.
  - Key changes: added `target_type: finding`; defined per-finding minimal `target_key` fields; excluded `message`, `evidence`, title/description/text, and other explanatory payload from matching keys; documented missing/stale/duplicate decision behavior; documented Rule 1 promotion and confirmed blocking scope.
  - Effect: `gate` can match final review decisions to findings without bloating review records or depending on unstable explanatory text.
- Added the final review schema and initial `gate` command.
  - Files changed: `schemas/final_review.schema.json`, `src/assessment_harness/schemas.py`, `src/assessment_harness/cli.py`.
  - Key changes: registered `final_review`; added `gate --final-review`; loaded the referenced `findings.json`; matched `target_type: finding` decisions by canonical minimal keys; returned `pending_review`, `success`, `fail`, or `invalid_input`; exposed `schema --command gate`.
  - Effect: caller agents now have a machine-readable external verdict stage after human final review.
- Added contract and fixture regressions.
  - Files changed: `tests/test_cli_output_contract.py`, `tests/test_fixtures.py`.
  - Key changes: locked `gate` schema introspection, pending behavior, Rule 1 promotion to confirmed blocking, override dismissal, nonblocking confirmed Rule 2 behavior, stale decision rejection, strict rejection of non-minimal finding `target_key` payload copies, and an end-to-end `orphan_scored_rubric` check → final review → gate path.
  - Effect: both under-strict and over-strict directions are covered for the new gate slice, including the "minimal key, no copied evidence" concern.
- Updated current-state documentation.
  - Files changed: `README.md`, `HANDOFF.md`, `CHANGELOG.md`, this work log.
  - Key changes: documented plan v1.16, initial `gate`, `final_review.schema.json`, gate output fields, and next work after this slice.
  - Effect: handoff now points to `review`/runner/queue composition work rather than treating all of `gate` as unimplemented.

### Issues Found

- Problem: final review examples previously showed `trace_link`, `spec_item`, and `review_queue_entry`, but did not define how a human review closes a provisional finding.
  Cause: `gate` had been deferred until after the final review contract existed, so finding-level mapping had not yet been specified.
  Resolution: added `target_type: finding` and a canonical key table in plan v1.16 before implementing code.
  Outcome: implementation follows a documented contract rather than inventing an implicit matching rule.
- Problem: a naive final review record could copy full finding payloads (`message`, `evidence`, rubric text, spec text) just to identify a finding.
  Cause: without a key table, the safest apparent matching input would be "copy everything".
  Resolution: limited `target_key` to generated identifiers only: `type` plus `rubric_id`, `spec_id`, or L1 paired rubric IDs as needed; `gate` now rejects non-identity fields such as copied `message`.
  Outcome: review records stay compact and robust against explanatory payload changes, and the code enforces the minimal-key contract rather than merely documenting it.
- Problem: accepted findings are not all blocking in the plan. Rule 2/L1/L5 can be confirmed as review outcomes but are not v0 external blocking verdicts.
  Cause: severity and blocking status are adjacent but not identical in the canonical plan.
  Resolution: limited `gate` exit `1` to confirmed `orphan_scored_rubric_item`, `optionality_mismatch`, and `mandatory_spec_bonus_only_traced`.
  Outcome: `gate` does not over-block medium confirmed Rule 2/L1/L5 findings.

### Decisions

- **Owner decision (proceed with mapping-first gate work)**: implement the final-review finding mapping after explicitly checking that keys do not carry excessive data.
- `target_type: finding` keys are matching keys only, not payload snapshots. Explanatory fields remain in `findings.json` and reports.
- Missing decisions and `hold`/`rerun_requested` return `pending_review`/exit `0`; stale or duplicate finding decisions return `invalid_input`/exit `2`.
- `accept` confirms a finding. For Rule 1 `possible_orphan_scored_rubric_item` and `unconfirmed_trace_coverage`, `accept` promotes to `orphan_scored_rubric_item` (`high`, `confirmed`). `override` dismisses the finding.

### Next Steps

1. Implement the `review` command that helps produce final review records rather than hand-authoring `final_review.yaml`.
2. Materialize trace-link override provenance (`sources.kind: human_override`) when review/gate work reaches trace artifact rewriting.
3. When Phase 2 compact/verifier queues land, implement queue composition before pointing `--review-queue-out` at a unified queue path.
4. Independently verify the v1.16 `gate` slice before publication.

### Verification

- Focused CLI + fixture suite: `python3 -m pytest tests/test_cli_output_contract.py tests/test_fixtures.py -q` passed (27 tests).
- Full suite: `python3 -m pytest -q` passed (134 tests).
- Canonical Docker suite: `docker compose run --rm test -q` passed.
- Collection check: `python3 -m pytest --collect-only -q` reports 20 CLI contract, 7 fixture, 12 model, and 95 rule tests.
- Gate schema smoke: `PYTHONPATH=src python3 -m assessment_harness.cli --output json schema --command gate` returns `status=success` and exposes `complete_final_review`, `fix_final_review`, and `revise_assessment`.
- Diff hygiene: `git diff --check` passed.

---

## Gate Conditional-Pass Follow-Up

### Goals

- Address the independent verification record `docs/verifications/2026-05-28_gate_initial_slice.md`.
- Convert the reported boundary-matrix empty cells into named regressions.
- Resolve the two minor design findings: unused `gate --policy` and spec-silent duplicate finding-key rejection.

### Completed Work

- Promoted the plan to v1.17.
  - Files changed: `docs/implementation_plan_assessment_harness_poc_v1.md`.
  - Key changes: explicitly made duplicate canonical finding keys in `findings.json` an `invalid_input`/exit `2` condition; added v1.17 changelog text for the verification follow-up; removed `--policy` from `gate` examples.
  - Effect: the code's duplicate-key guard is no longer a spec-silent behavior, and `gate` no longer advertises an unused policy input.
- Expanded `gate` regression coverage.
  - Files changed: `tests/test_cli_output_contract.py`.
  - Key changes: added named tests for direct blocking accepts (`optionality_mismatch`, `mandatory_spec_bonus_only_traced`), nonblocking L1/L5 accepts, `hold`/`rerun_requested`, duplicate decisions, missing key fields, unknown finding type, invalid final-review schema, missing findings file, invalid findings schema, and duplicate finding keys.
  - Effect: the independent verification's boundary-matrix empty cells are now locked by tests rather than only by manual smoke execution.
- Removed the unused `gate --policy` CLI argument.
  - Files changed: `src/assessment_harness/cli.py`, `README.md`, `docs/implementation_plan_assessment_harness_poc_v1.md`.
  - Key changes: `gate` now accepts only `--final-review` plus output formatting; examples match the actual parser.
  - Effect: the CLI no longer carries speculative policy plumbing.
- Updated current-state records.
  - Files changed: `README.md`, `HANDOFF.md`, `CHANGELOG.md`, this work log.
  - Key changes: marked current plan as v1.17 and documented that this slice closes the conditional-pass regression gaps.
  - Effect: next workers see the verification follow-up as completed rather than as a lingering caveat.

### Issues Found

- Problem: the initial `gate` implementation behaved correctly on branches the tests did not name.
  Cause: implementation smoke covered more branches than the committed regression matrix.
  Resolution: added explicit tests for each contract branch called out by the verification record.
  Outcome: removing `optionality_mismatch` or `mandatory_spec_bonus_only_traced` from the blocking set, or adding L1/L5 to it, now fails tests.
- Problem: `gate --policy` existed but `_cmd_gate` never read policy.
  Cause: the final workflow had historically shown `--policy` on gate before gate's actual responsibilities were narrowed to final-review consumption.
  Resolution: removed the argument and updated command examples.
  Outcome: no speculative CLI surface remains for policy in `gate`.
- Problem: duplicate canonical finding keys in `findings.json` were rejected by code but not named in the plan.
  Cause: the duplicate-key guard was added as defensive input validation during implementation.
  Resolution: documented duplicate finding keys as invalid gate input in plan v1.17.
  Outcome: spec and implementation now agree.

### Decisions

- The owner accepted the verification finding and directed reinforcement rather than treating the conditional pass as sufficient.
- Duplicate canonical finding keys are invalid gate input, because gate cannot map one review decision to two indistinguishable findings safely.
- `gate` remains policy-free for now. Policy belongs to earlier rule evaluation; `gate` consumes final review records and findings.

### Next Steps

1. Ask for or perform independent re-verification of the v1.17 gate follow-up before publication.
2. Continue with the `review` command after the gate slice is accepted.

### Verification

- Focused gate contract suite: `python3 -m pytest tests/test_cli_output_contract.py -q` passed (33 tests).
- Full suite: `python3 -m pytest -q` passed (147 tests).
- Canonical Docker suite: `docker compose run --rm test -q` passed.
- Collection check: `python3 -m pytest --collect-only -q` reports 33 CLI contract, 7 fixture, 12 model, and 95 rule tests.
