<!-- .ko mirror created on finalize (publication_plan §7b) -->

<p align="center">
  <a href="./evaluation.md"><img src="https://img.shields.io/badge/Language-EN-111111?style=for-the-badge" alt="English"></a>
  <a href="./evaluation.ko.md"><img src="https://img.shields.io/badge/Language-KO-6B7280?style=for-the-badge" alt="한국어"></a>
</p>
<p align="center"><sub>Switch language / 언어 전환</sub></p>

# Evaluation — measured

> **Moving snapshot.** This project is under active development, so every number
> below changes as rules, fixtures, and tests evolve. The figures here are a
> dated snapshot, **recomputed from a real run — never transcribed** — and each
> table ships with the command to reproduce it. Treat the *shapes and behaviors*
> (which fixture fires which finding, which input is rejected, in what order) as
> the stable claim; treat the *counts* as "true on the snapshot date."
>
> **Snapshot:** 2026-06-04 · plan v1.31 · Python 3.12.3 · direct `pytest`
> (`PYTHONPATH=src`). Canonical dev environment is Docker (`python:3.11-slim`);
> see [Reproduction](#reproduction).

## Test suite

`266 passed` (full suite, this snapshot).

| Test module | Count | Locks |
|---|---:|---|
| `tests/test_rules.py` | 95 | Rule 0–3 + lint L1/L5/L6, each with under-strict + over-strict guards |
| `tests/test_cli_output_contract.py` | 107 | envelope/exit-code contract, `schema` introspection, `extract`/`compact`/`verify`, semantic-verification consumption, `review`/`gate`/`materialize-review` branches |
| `tests/test_agent_runner_contract.py` | 27 | runner protocol, candidate schemas, normalization, staged + deep integrity |
| `tests/test_compacting.py` | 7 | compacting helper union, id_map lineage, run exclusion, trace-reference remapping |
| `tests/test_models.py` | 22 | YAML/schema loader, source-snapshot sha256, span access |
| `tests/test_fixtures.py` | 8 | grounded end-to-end fixture behavior |
| **Total** | **266** | |

Every rule branch is locked in **both directions** (the original bug can re-fail
the test, *and* an over-correction that flags a normal case also fails) — the
project's regression discipline, described in `CLAUDE.md` / `AGENTS.md`.

## `check` behavior on the grounded fixtures

Each row is a real `check` run on the named fixture, using that fixture's own
`policy.yaml` and `source_manifest.yaml`, `--output json`. Counts are the
provisional finding counts `(high, medium, informational)` straight from the
envelope.

| Fixture | status | exit | (high, med, info) | review_queue | exercises |
|---|---|---:|---|---:|---|
| `clean_assignment` | `provisional_findings` | 0 | (0, 2, 0) | 0 | automation baseline — 2 `unconfirmed_trace_coverage` (links pending) |
| `orphan_scored_rubric` | `provisional_findings` | 0 | (1, 1, 1) | 0 | all three Rule 1 branches (orphan scored / unconfirmed / orphan bonus) |
| `uncovered_must_spec` | `provisional_findings` | 0 | (1, 5, 0) | 1 | Rule 2 coverage gap, co-firing L5/L6 on a bonus-only must |
| `optionality_mismatch` | `provisional_findings` | 0 | (2, 1, 0) | 0 | Rule 3 optional-only scored weight at/above threshold |
| `bonus_misuse` | `provisional_findings` | 0 | (1, 5, 1) | 2 | lint L1/L5/L6 + Rule 2 overlap, with mutual-exclusion boundaries |
| `reference_integrity` | `invalid_input` | 2 | — | — | Rule 0 fails the input: `high_integrity_count=9` (8 distinct codes; `evidence_quote_missing_for_spec_id` fires twice) |

`next_actions` observed (deduplicated) — the agent-consumable review hints:

| Fixture | `next_actions` types |
|---|---|
| `clean_assignment` | `review_unconfirmed_trace_coverage` |
| `orphan_scored_rubric` | `review_orphan_rubric`, `review_orphan_bonus_rubric`, `review_unconfirmed_trace_coverage` |
| `uncovered_must_spec` | `review_uncovered_must_spec`, `review_bonus_mandatory_only`, `review_mandatory_spec_bonus_only`, `review_unconfirmed_trace_coverage` |
| `optionality_mismatch` | `review_optionality_mismatch`, `review_unconfirmed_trace_coverage` |
| `bonus_misuse` | `review_double_scoring`, `review_bonus_mandatory_only`, `review_mandatory_spec_bonus_only`, `review_uncovered_must_spec`, `review_orphan_bonus_rubric`, `review_unconfirmed_trace_coverage` |
| `reference_integrity` | `fix_reference_integrity` |

## Input-contract guards (fail loud, never silent — see [decisions.md](decisions.md) §B5)

Load-bearing inputs are required; omitting one returns a structured, typed
recovery action rather than a silent skip or argparse usage text. **The manifest
is validated before the policy**, so when both are absent the manifest action
fires first.

| Case | status | exit | next_action |
|---|---|---:|---|
| no `--source-manifest` (policy present) | `invalid_input` | 2 | `provide_source_manifest` |
| no `--policy` (manifest present) | `invalid_input` | 2 | `provide_policy` |
| both omitted | `invalid_input` | 2 | `provide_source_manifest` (manifest checked first) |

## Reproduction

Canonical (Docker dev environment):

```bash
docker compose build
docker compose run --rm test          # full pytest suite
```

What produced this snapshot (direct, equivalent):

```bash
PYTHONPATH=src python3 -m pytest -q                 # 266 passed
PYTHONPATH=src python3 -m pytest --collect-only -q  # per-module counts
```

A single fixture smoke (swap the fixture name for any row above):

```bash
PYTHONPATH=src python3 -m assessment_harness.cli --output json check \
  --spec-items      fixtures/optionality_mismatch/spec_items.yaml \
  --rubric-items    fixtures/optionality_mismatch/rubric_items.yaml \
  --trace-links     fixtures/optionality_mismatch/trace_links.yaml \
  --source-manifest fixtures/optionality_mismatch/source_manifest.yaml \
  --policy          fixtures/optionality_mismatch/policy.yaml \
  --out             work/findings.json \
  --diagnostics-out work/integrity_diagnostics.json \
  --review-queue-out work/review_queue.json
```

The independent verification records under [docs/verifications/](verifications/)
recompute these same smoke numbers as part of auditing each slice — they are not
taken on trust from the work logs.
