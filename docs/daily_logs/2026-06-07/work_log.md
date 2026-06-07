# Work Log - 2026-06-07

## Extract Source Snapshot and Runner Decisions

### Goals

- Read `HANDOFF.md` and the latest daily logs to identify the next safe task.
- Record the owner decisions needed before real SDK runner work.
- Adopt the tool side-effect policy without adding write/propose tools prematurely.
- Implement `extract` source snapshot auto-generation without changing the existing explicit `--source-manifest` path.

### Completed work

- Reviewed `HANDOFF.md`, `docs/daily_logs/2026-06-04/work_log.md`, and the latest verification records.
  - Key finding: the `materialize-review` and read-only framework tool residuals from 2026-06-04 were closed by follow-up work and independent re-verification.
  - Effect: there was no remaining verification-blocking defect from those slices.
- Added `docs/sdk_runner_decisions.md`.
  - Key change: records the pending real SDK runner decisions: first SDK surface, credential delivery, sample assignment, raw trace retention/redaction, runner limits, SDK tool registration, and live-output contract.
  - Effect: real SDK runner work can start later from a checklist instead of reopening the whole design space.
- Updated `docs/implementation_plan_assessment_harness_poc_v1.md` to v1.32.
  - Key change: records the owner decision to keep framework tools read-only and have runners collect proposed outputs before emitting candidate artifacts.
  - Key change: records the owner decision to defer publication mirrors until all work reaches publication freeze.
  - Key change: defines the `extract` source snapshot auto-generation contract.
  - Effect: the code change has a canonical contract instead of an implicit path convention.
- Implemented `extract` source snapshot auto-generation in `src/assessment_harness/cli.py`.
  - Key change: when `--source-manifest` is omitted, `extract` writes `source_snapshot/spec.md`, `source_snapshot/rubric.md`, and `source_snapshot/manifest.yaml` beside `--out-dir`.
  - Key change: the generated manifest uses `DOC_SPEC` and `DOC_RUBRIC`, includes sha256 hashes, and is validated before use.
  - Key change: explicit `--source-manifest` still takes precedence and suppresses auto-generation.
  - Effect: `extract --out-dir work/runs` now produces the source snapshot expected by later `verify --source-manifest work/source_snapshot/manifest.yaml`.
- Added focused CLI regressions in `tests/test_cli_output_contract.py`.
  - Key change: locks generated snapshot path, manifest schema validity, sha256 values, copied source contents, and explicit-manifest precedence.
  - Effect: future changes cannot silently fall back to fixture manifests or overwrite explicit manifest intent.
- Updated `HANDOFF.md`, `README.md`, `docs/evaluation.md`, and `CHANGELOG.md`.
  - Effect: project status, plan version, document map, changelog, and measured test counts reflect v1.32 and the 279-test suite.

### Issues found

- Problem: `extract` source snapshot generation was an intended direction but did not have a concrete path/output contract.
  Cause: previous plan text established that source manifests are mandatory for downstream grounding, but left production snapshot placement implicit.
  Resolution: defined the sibling `source_snapshot/` convention in plan v1.32 and implemented it.
  Outcome: the CLI now produces the manifest path later stages already expect.
- Problem: real SDK runner implementation still depends on owner decisions.
  Cause: credentials, sample assignment permission, raw trace retention/redaction, and runner limits affect security and publication scope.
  Resolution: documented the decision checklist in `docs/sdk_runner_decisions.md`.
  Outcome: no SDK credential or live-run behavior was guessed.

### Decisions

- **Tool side-effect policy:** keep framework tools read-only. Propose/write behavior must be runner-collected and emitted as candidate artifacts at run end, not written directly to candidate files.
- **Publication freeze:** bilingual mirrors and README EN/KO flip stay deferred until all planned development work reaches publication freeze.
- **Extract source snapshot:** path convention is implementation-owned, not a separate owner decision. Use sibling `source_snapshot/` beside `--out-dir`; explicit `--source-manifest` remains authoritative.
- **SDK runner:** defer implementation until credential delivery, runnable sample assignment, raw trace retention/redaction, and runner limits are decided.

### Next steps

1. Decide the real SDK runner checklist in `docs/sdk_runner_decisions.md`.
2. Implement the first live SDK runner only after sample assignment and credential delivery are available.
3. Implement runner-collected propose behavior only when the runner output shape is specified.
4. At publication freeze, recompute `docs/evaluation.md` again and perform the deferred bilingual mirrors.

### Verification

- `PYTHONPATH=src python3 -m pytest tests/test_cli_output_contract.py -q -k "extract"` -> 8 passed.
- `python3 -m py_compile src/assessment_harness/cli.py` -> passed.
- `PYTHONPATH=src python3 -m pytest tests/test_cli_output_contract.py -q` -> 110 passed.
- `PYTHONPATH=src python3 -m pytest --collect-only -q` -> 279 tests collected: agent-runner 27, CLI 110, compacting 7, fixtures 8, models 22, rules 95, tools 10.
- `PYTHONPATH=src python3 -m pytest -q` -> 279 passed.
- Fixture smoke runs for `docs/evaluation.md` were re-run and still match the table:
  - `clean_assignment` -> `provisional_findings`, exit `0`, `(high=0, medium=2, informational=0)`, `review_queue_count=0`.
  - `orphan_scored_rubric` -> `provisional_findings`, exit `0`, `(high=1, medium=1, informational=1)`, `review_queue_count=0`.
  - `uncovered_must_spec` -> `provisional_findings`, exit `0`, `(high=1, medium=5, informational=0)`, `review_queue_count=1`.
  - `optionality_mismatch` -> `provisional_findings`, exit `0`, `(high=2, medium=1, informational=0)`, `review_queue_count=0`.
  - `bonus_misuse` -> `provisional_findings`, exit `0`, `(high=1, medium=5, informational=1)`, `review_queue_count=2`.
  - `reference_integrity` -> `invalid_input`, exit `2`, `high_integrity_count=9`.
- Input guard smoke runs still match `docs/evaluation.md`: no `--source-manifest` -> `provide_source_manifest`; no `--policy` -> `provide_policy`; both omitted -> `provide_source_manifest`.

## Extract Source Snapshot Recheck

### Goals

- Re-check the independent verification record for `extract` source snapshot auto-generation.
- Confirm whether the four recorded issues are blocking defects or non-blocking observations.

### Completed work

- Added `docs/verifications/2026-06-07/extract_source_snapshot_auto_generation_recheck.md`.
  - Key change: independently re-read the prior verification record, plan v1.32, implementation, tests, and schema.
  - Key change: re-ran the reported test commands and additional smoke probes for relative `--out-dir` and mismatched `--spec` vs `--fixture-dir`.
  - Effect: the prior verification's pass verdict is independently confirmed.

### Issues found

- Problem: the generated `project_id` is weak metadata (`source` for fixture-style paths).
  Cause: `extract` derives it from `Path(args.spec).parent.name`.
  Resolution: left unchanged because current code does not consume `SourceSnapshot.project_id`.
  Outcome: recorded as a non-blocking future improvement candidate.

### Decisions

- No production code change was made during the recheck. The four recorded observations remain non-blocking.

### Next steps

1. Commit/publish only when the owner asks.
2. Consider improving generated `project_id` only if it becomes user-facing or semantically consumed.

### Verification

- `PYTHONPATH=src python3 -m pytest tests/test_cli_output_contract.py -q -k "extract"` -> 8 passed.
- `PYTHONPATH=src python3 -m pytest tests/test_cli_output_contract.py -q` -> 110 passed.
- `PYTHONPATH=src python3 -m pytest --collect-only -q` -> 279 tests collected.
- `PYTHONPATH=src python3 -m pytest -q` -> 279 passed.
- Independent smokes confirmed generated snapshot sha256 values, relative `--out-dir runs` behavior, and mismatched `--spec` vs `--fixture-dir` invalid-run isolation.
- `git diff --check` -> clean.
