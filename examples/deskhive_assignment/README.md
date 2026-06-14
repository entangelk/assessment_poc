# Example: DeskHive maintenance assignment (complex)

A fully synthetic, multi-phase take-over/debugging assignment used to demonstrate
the harness on a **complex** assignment format — closer to a real maintenance
hand-off than the per-rule scaffolding under [`fixtures/`](../../fixtures).

This directory is the harness **input** (a candidate-facing `spec.md` plus an
evaluator-only `rubric.md`), not a candidate solution. Unlike `fixtures/`, which
holds pre-extracted YAML for unit tests, this is a raw assignment a reader can run
end-to-end to watch the harness review the *assessment design itself*.

## Files

```text
spec.md     # candidate-facing assignment (Phase 0–4, 5 defects, boundaries)
rubric.md   # evaluator-only rubric (8 scored + 2 bonus + 1 qualitative)
notes.md    # human context (Korean): complexity intent + seeded signals
```

## Seeded spec↔rubric signals

Designed so the rules fire meaningfully (realistic, not a trap puzzle):

| Rubric | Intended finding |
|---|---|
| R5 | `possible_orphan_scored_rubric_item` (Rule 1) — quote not verbatim in spec |
| R8 | `optionality_mismatch` (Rule 3) — optional "may" spec scored at weight 10 |
| RB1 | `uncovered_must_spec_item` (Rule 2) + `mandatory_spec_bonus_only_traced` (L6) + `bonus_grades_mandatory_only` (L5) — required AI log graded as bonus only |
| R7 + RB2 | `double_scored_spec` (Rule L1) — CTO report scored and bonus-traced |
| scored items | `unconfirmed_trace_coverage` (Rule 1) — Phase 0 semantic still pending |

See [`notes.md`](notes.md) for the format constraints the
`deterministic_extraction` runner imposes (rubric header shape + verbatim
`Traceable spec quote`).

## Run it (from the repo root)

```bash
SAMPLE=examples/deskhive_assignment
OUT=work/deskhive_run

PYTHONPATH=src python3 -m assessment_harness.cli extract \
  --spec   $SAMPLE/spec.md \
  --rubric $SAMPLE/rubric.md \
  --runner deterministic_extraction --runs 1 \
  --policy config/policy.yaml --out-dir $OUT/runs
# then: compact -> verify -> check -> report -> review -> gate -> materialize-review
```

The latest end-to-end run produced 14 provisional findings (3 high / 11 medium),
`blocking_count=0`, exercising Rules 1, 2, 3, L1, L5, and L6. Run artifacts land
under `work/` (gitignored).
