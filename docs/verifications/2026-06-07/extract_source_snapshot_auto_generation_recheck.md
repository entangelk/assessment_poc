# Verification — extract source snapshot auto-generation recheck

## Subject Metadata

- **Date**: 2026-06-07
- **Requester**: Owner (kdtyohan@gmail.com) — asked to re-check the completed independent verification.
- **Verifier**: Codex
- **Target slice/artifact**: `extract` source snapshot auto-generation plus the prior verification record at `docs/verifications/2026-06-07/extract_source_snapshot_auto_generation.md`
- **Canonical spec reference**: `docs/implementation_plan_assessment_harness_poc_v1.md` v1.32, especially the `extract` command behavior paragraph in §8 and v1.32 changelog in §15; `schemas/source_manifest.schema.json`
- **Source of work being verified**: working tree, uncommitted

## Scope

- Plan v1.32 source snapshot contract.
- `src/assessment_harness/cli.py` snapshot generation implementation.
- `tests/test_cli_output_contract.py` extract regressions.
- Generated `source_manifest` schema and sha256 grounding.
- Reported test counts in `docs/evaluation.md`.
- The four non-blocking issues recorded by the first verification.

## Methodology

- Re-read the prior verification record instead of trusting its summary.
- Re-read the in-scope implementation and tests directly.
- Re-read the plan v1.32 contract and schema.
- Re-ran the reported test commands and independent smokes.

Commands used:

```bash
PYTHONPATH=src python3 -m pytest tests/test_cli_output_contract.py -q -k "extract"
PYTHONPATH=src python3 -m pytest tests/test_cli_output_contract.py -q
PYTHONPATH=src python3 -m pytest --collect-only -q
PYTHONPATH=src python3 -m pytest -q
rm -rf /tmp/snaptest_recheck && mkdir -p /tmp/snaptest_recheck
PYTHONPATH=src python3 -m assessment_harness.cli --output json extract \
  --spec fixtures/clean_assignment/source/spec.md \
  --rubric fixtures/clean_assignment/source/rubric.md \
  --runner mock_fixture \
  --fixture-dir fixtures/clean_assignment \
  --runs 2 \
  --out-dir /tmp/snaptest_recheck/runs
rm -rf /tmp/snaptest_rel && mkdir -p /tmp/snaptest_rel
cd /tmp/snaptest_rel
PYTHONPATH=/workspace/assessment_poc/src python3 -m assessment_harness.cli --output json extract \
  --spec /workspace/assessment_poc/fixtures/clean_assignment/source/spec.md \
  --rubric /workspace/assessment_poc/fixtures/clean_assignment/source/rubric.md \
  --runner mock_fixture \
  --fixture-dir /workspace/assessment_poc/fixtures/clean_assignment \
  --runs 1 \
  --out-dir runs
rm -rf /tmp/snaptest_mismatch && mkdir -p /tmp/snaptest_mismatch
PYTHONPATH=src python3 -m assessment_harness.cli --output json extract \
  --spec fixtures/reference_integrity/source/spec.md \
  --rubric fixtures/clean_assignment/source/rubric.md \
  --runner mock_fixture \
  --fixture-dir fixtures/clean_assignment \
  --runs 1 \
  --out-dir /tmp/snaptest_mismatch/runs
git diff --check
```

## Findings

### Contract And Implementation

Plan v1.32 requires `extract` to generate a sibling `source_snapshot/manifest.yaml` when `--source-manifest` is omitted, and to preserve explicit `--source-manifest` precedence. `cli.py` implements that contract directly:

- `_extract_source_manifest_path` returns the explicit path when present.
- Otherwise `_generate_extract_source_snapshot` writes beside `Path(args.out_dir).parent`.
- The generated manifest uses `DOC_SPEC` / `DOC_RUBRIC`, role literals `candidate_spec` / `evaluator_rubric`, relative paths `spec.md` / `rubric.md`, and sha256 values computed from the copied snapshot files.
- The manifest is schema-validated before being loaded as the source snapshot for deep candidate Rule 0.

No contradiction found between the plan, schema, and code.

### Regression Coverage

The two load-bearing branches are covered:

- Omitted manifest -> snapshot generation, manifest schema validity, copied content, generated sha256 values, and validated runs are pinned by `test_extract_mock_fixture_writes_validated_candidate_runs`.
- Explicit manifest -> explicit path is returned and no auto-generated manifest is written, pinned by `test_extract_explicit_source_manifest_takes_precedence`.

The first verification's "boundary matrix has no empty cells" claim is accurate for the in-scope contract.

### Independent Smokes

Generated `/tmp/snaptest_recheck/source_snapshot/manifest.yaml` matched the snapshot file hashes:

- `DOC_SPEC`: `21a7cd6e486e69839ab1fe22e07444625965e1d123f333c87c2a9a6eec72b947`
- `DOC_RUBRIC`: `d36b47621e812e080e0ddad99b5a7b95233bc429b233b73f60f7b79eac7cba91`

The extract run reported `valid_run_count=2` and `invalid_run_count=0`.

With relative single-component `--out-dir runs`, the command wrote `source_snapshot/manifest.yaml` in the current working directory. This matches the specified sibling rule.

With `--spec` intentionally pointed at a mismatched source while the mock fixture still emitted clean-assignment candidates, the command returned success for the extract command but isolated the run as invalid: `valid_run_count=0`, `invalid_run_count=1`, and run-local `integrity_diagnostics.json` recorded source grounding errors. This matches the existing extract contract: invalid runs are isolated rather than making the whole extract command fail.

### Test Counts

Reproduced:

- extract subset: 8 passed.
- CLI contract suite: 110 passed.
- collection: 279 tests collected, with module counts 27 / 110 / 7 / 8 / 22 / 95 / 10.
- full suite: 279 passed.
- `git diff --check`: clean.

These match the prior verification record and `docs/evaluation.md`.

## Issues / Risks

- **Project ID metadata quality**: confirmed. `project_id` becomes `source` for fixture-style paths such as `fixtures/clean_assignment/source/spec.md`. Current code only loads and stores `SourceSnapshot.project_id`; no rule or CLI behavior consumes it. This is a metadata-quality nit, not a defect.
- **Relative single-component `--out-dir` location**: confirmed. `--out-dir runs` writes `source_snapshot/manifest.yaml` under cwd. This is exactly `sibling of --out-dir`, not a contract violation.
- **Mock fixture candidate vs generated snapshot mismatch**: confirmed. If `--spec` and `--fixture-dir` disagree, the run is isolated as invalid with grounding diagnostics. This is stricter and consistent with the source-grounding model; not a regression.
- **Generated manifest schema failure branch lacks a dedicated test**: confirmed. With normal inputs the generated document is effectively always schema-valid. This is defensive code with no practical failing route absent monkeypatching or future code changes. Not blocking for this slice.

No additional defects found.

## Verdict

**Pass.**

The prior verification record is accurate. The implementation matches plan v1.32 and the schema, the two contract branches are locked by regressions, sha256 grounding reproduces independently, reported test counts are correct, and the four noted issues are non-blocking quality or edge-case observations rather than defects.

## Outstanding Items

- Working tree remains uncommitted.
- Optional future improvement: choose a more meaningful generated `project_id` if that metadata becomes user-facing or semantically consumed.

## Reproduction

Run the commands in the Methodology section from `/workspace/assessment_poc`.
