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

---

## Initial Review Draft Writer

### Goals

- Continue from the accepted `gate` slice into the next workflow step: `review`.
- Keep scope narrow and safe: generate a final-review draft, but do not make final human decisions automatically.
- Reuse the v1.17 minimal finding-key contract so review records do not copy finding payloads.

### Completed Work

- Promoted the plan to v1.18.
  - Files changed: `docs/implementation_plan_assessment_harness_poc_v1.md`.
  - Key changes: defined Phase 0 `review` as a draft writer; required `--findings`, `--out-dir`, and `--reviewer`; documented that every generated finding decision starts as `hold`; documented that draft records gate to `pending_review` when findings exist.
  - Effect: the review command has a canonical contract before being used as part of the workflow.
- Implemented `assessment-harness review`.
  - Files changed: `src/assessment_harness/cli.py`.
  - Key changes: reads and validates `findings.json`; converts each known finding to a minimal canonical `target_key`; writes `<out-dir>/review.yaml`; records optional input paths; exposes `schema --command review`.
  - Effect: users no longer need to hand-author the initial final review record just to begin review.
- Added regression coverage.
  - Files changed: `tests/test_cli_output_contract.py`, `tests/test_fixtures.py`.
  - Key changes: locked `schema --command review`, synthetic review draft generation, empty-findings success through gate, unknown finding rejection, and an end-to-end `orphan_scored_rubric` check → review draft → gate pending path.
  - Effect: review draft behavior is tied to both the public CLI envelope and grounded fixture outputs.
- Updated current-state docs.
  - Files changed: `README.md`, `HANDOFF.md`, `CHANGELOG.md`, this work log.
  - Key changes: documented `--reviewer`, review draft semantics, and the current package surface including `review`.
  - Effect: handoff now points to richer human decision input / trace override materialization rather than the basic review draft writer.

### Issues Found

- Problem: auto-generating `accept` decisions would make the tool a judge rather than a review recorder.
  Cause: `review` sits between provisional findings and external `gate`, so the temptation is to "complete" decisions automatically.
  Resolution: generated decisions are always `hold`; humans must edit the draft to `accept`, `override`, or `rerun_requested`.
  Outcome: the first review slice is useful without collapsing the human-review boundary.
- Problem: relative `findings_path` inside `review.yaml` could break when `gate` resolves paths relative to the review file.
  Cause: `gate` deliberately resolves relative paths from the final-review file's directory.
  Resolution: `review` writes absolute input paths.
  Outcome: a generated review draft can be passed to `gate` from any working directory.

### Decisions

- `review` is a draft writer, not an interactive or automatic final-review UI.
- `--reviewer` is required so the generated record has explicit audit metadata.
- Unknown finding types are invalid for review draft generation because `gate` would not know a canonical minimal key for them.

### Next Steps

1. Run focused/full/Docker verification for the v1.18 review slice.
2. Independently verify review draft generation before publication.
3. Later review work can add richer human decision input or trace-link override materialization.

### Verification

- Focused review/gate contract suite: `python3 -m pytest tests/test_cli_output_contract.py -q` passed (37 tests).
- Focused review/gate + fixture suite: `python3 -m pytest tests/test_cli_output_contract.py tests/test_fixtures.py -q` passed (45 tests).
- Full suite: `python3 -m pytest -q` passed (152 tests).
- Canonical Docker suite: `docker compose run --rm test -q` passed.
- Collection check: `python3 -m pytest --collect-only -q` reports 37 CLI contract, 8 fixture, 12 model, and 95 rule tests.
- Review schema smoke: `PYTHONPATH=src python3 -m assessment_harness.cli --output json schema --command review` returns `status=success` and exposes `review_path`, `decision_count`, and `input_error`.

---

## Review Draft Safety Guard Follow-Up

### Goals

- Address the independent review of the v1.18 `review` draft writer without weakening the human-review boundary.
- Add the missing regression for known finding types with absent canonical key fields.
- Decide and implement the safest default for invalid findings status and existing draft overwrites.

### Completed Work

- Promoted the plan to v1.19.
  - Files changed: `docs/implementation_plan_assessment_harness_poc_v1.md`.
  - Key changes: documented that `review` accepts only `findings.status=success` or `provisional_findings`; documented that `gate` remains status-agnostic; documented that existing `<out-dir>/review.yaml` is not overwritten unless `--force` is passed; recorded that timestamped/versioned draft management is deferred.
  - Effect: the status/overwrite behavior is now a contract, not an implementation guess.
- Hardened the `review` command.
  - Files changed: `src/assessment_harness/cli.py`.
  - Key changes: added a findings status guard before draft generation; added overwrite refusal with explicit `--force`; kept generated decisions at `hold` and target keys minimal.
  - Effect: Rule 0 invalid outputs with empty findings cannot be converted into a draft that later gates as success, and human-edited drafts are not silently erased.
- Expanded review regressions.
  - Files changed: `tests/test_cli_output_contract.py`.
  - Key changes: added the missing known-type/missing-key-field invalid-input regression; added status-guard regression; expanded the status guard to reject `invalid_input`, `internal_error`, and missing status inputs; added no-overwrite and force-overwrite regressions.
  - Effect: under-strict status acceptance and accidental overwrite are now locked, while explicit regeneration remains possible.
- Updated current-state docs.
  - Files changed: `README.md`, `HANDOFF.md`, `CHANGELOG.md`, this work log.
  - Key changes: documented plan v1.19, review status guard, overwrite guard, and the deferred timestamp/versioning boundary.
  - Effect: next workers can continue with richer review/version management without rediscovering this policy.

### Issues Found

- Problem: the v1.18 review test matrix did not lock the known finding type + missing canonical key field branch.
  Cause: unknown finding type was covered, but optional schema fields made the missing-key path separately reachable.
  Resolution: added a regression using `optionality_mismatch` without `rubric_id`; `review` returns `invalid_input`/exit `2` with `missing gate key field`.
  Outcome: the branch named in the final-review mapping contract is now protected.
- Problem: `review` previously accepted `findings.status=invalid_input` if the file matched schema shape and had an empty findings list.
  Cause: the first draft writer focused on findings array conversion and did not gate the producing command status.
  Resolution: `review` now rejects any findings status except `success` and `provisional_findings`.
  Outcome: invalid Rule 0 input cannot be laundered through an empty draft into a successful gate result.
- Problem: the first status-guard regression only sampled `invalid_input`, so a future blocklist-style refactor could still let `internal_error` through.
  Cause: the implementation was a whitelist, but the regression did not prove that shape.
  Resolution: parametrized the status rejection test over `invalid_input`, `internal_error`, and status omission. The omission case is rejected by schema before the whitelist guard, while `internal_error` directly locks the whitelist behavior.
  Outcome: changing the guard to reject only `invalid_input` now fails the CLI contract suite.
- Problem: re-running `review` over the same output directory silently replaced `review.yaml`.
  Cause: the initial implementation treated draft generation as reproducible output, but final review drafts may be hand-edited artifacts.
  Resolution: default overwrite is forbidden; `--force` is required for intentional regeneration.
  Outcome: human edits are preserved by default.

### Decisions

- **Owner-guided decision (2026-05-28)**: put the findings-status safety guard in `review`, not `gate`. This prevents accidental invalid-input laundering at draft creation while preserving `gate` as a consumer of explicit final-review records for manual recovery and audit workflows.
- **Owner-guided decision (2026-05-28)**: default behavior is no overwrite for `review.yaml`. `--force` is the explicit escape hatch.
- Timestamped/versioned draft management is useful but deferred. For now, callers that need draft history should use distinct `--out-dir` values; adding automatic version files belongs in a separate policy slice.

### Next Steps

1. Ask for independent re-verification before publication.
2. Later review work can add richer human decision input and a deliberate draft-versioning policy.

### Verification

- Focused review/gate + fixture suite: `python3 -m pytest tests/test_cli_output_contract.py tests/test_fixtures.py -q` passed (51 tests).
- Full suite: `python3 -m pytest -q` passed (158 tests).
- Canonical Docker suite: `docker compose run --rm test -q` passed.
- Collection check: `python3 -m pytest --collect-only -q` reports 43 CLI contract, 8 fixture, 12 model, and 95 rule tests.
- Review schema smoke: `PYTHONPATH=src python3 -m assessment_harness.cli --output json schema --command review` returns `status=success` and exposes `review_path`, `decision_count`, and `input_error`.
- Gate schema smoke: `PYTHONPATH=src python3 -m assessment_harness.cli --output json schema --command gate` returns `status=success` and exposes `complete_final_review`, `fix_final_review`, and `revise_assessment`.
- Diff hygiene: `git diff --check` passed.
