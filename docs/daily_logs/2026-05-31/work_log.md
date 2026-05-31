# Work Log - 2026-05-31

## Decision Harvest → Reconcile into `docs/decisions.md`

### Goals

- Complete the publication-effort task left open in `HANDOFF.md`: systematically sweep the two un-swept decision sources (daily logs, verification records) so the standalone decision record is not built from a partial survey.
- Reconcile genuinely new decisions into `docs/decisions.md` as vignettes in the locked first-person voice, without duplicating the existing 8.

### Completed work

- Swept all four decision sources (sources 3/ideation and 4/plan-change-log were already done in prior sessions; sources 1/daily-logs and 2/verification-records were swept this session).
  - Daily logs read: `docs/daily_logs/2026-05-2[5-8]/work_log.md` `### Decisions` and `### Issues Found` sections (2026-05-29 was already read in HANDOFF context).
  - Verification records read: Verdict / Issues sections of `gate_initial_slice.md`, `policy_completeness.md`, `review_safety_guards.md` (2026-05-28), confirming they corroborate rather than introduce decisions beyond the daily-log harvest.
- Added 8 new vignettes to `docs/decisions.md` (8 → 16 total), matching the existing **Stake → Decision → Trade-off → Confirm** shape and first-person voice. Every "Confirm" line cites a primary source (plan change log, work log, verification record, or schema/config file).
  - Files changed: `docs/decisions.md`.
  - Part A (+3): **A4** lint-mindset pivot (Owner reframed "lint" from project code to scoring-structure validation → the inverse invariant that births the Rule L family); **A5** gate blocking scope (only 3 confirmed finding types block; severity ≠ blocking); **A6** no-opinion-on-threshold-values (`config/policy.yaml` thresholds are caller-tunable, not authoritative).
  - Part B (+4): **B5** fail-loud / never silently disable a rule (missing manifest/policy → `invalid_input`, "a silently-disabled rule is worse than a hard error"); **B6** `review` writes only `hold`, never manufactures an approval (+ refuses `invalid_input` laundering, no-overwrite-without-`--force`); **B7** the decision record points at findings via minimal keys, never copies payload (single-source-of-truth inside the data model); **B8** raw vs audit trace separated by retention/redaction, not convenience.
  - Part C (+1): **C2** the plan is the single source of truth; `HANDOFF.md` is never a shadow spec ("if a resolution changes what another worker implements, it goes in the plan body in the same slice").
- Updated `HANDOFF.md` Publication/Portfolio section: decisions.md now 16 vignettes; all four harvest sources marked DONE; next task reframed from "harvest" to "curate (16 → final cut) + Step 1 bilingual scaffold".

### Issues found

- Problem: the "no opinion on thresholds" decision (A6) was originally stated in ideation v2.2 §8 about `bonus_ratio_threshold` (Rule L2), which is **not implemented** (L2 deferred).
  Cause: ideation enumerated thresholds for rules not all promoted to the plan.
  Resolution: A6 cites the *live* instance `rules.optionality_mismatch.weight_threshold` (present in `config/policy.yaml`) for the principle by **name only** — no value is quoted in the vignette — and avoids implying `bonus_ratio_threshold` is active. Keeps the "no overclaiming" publication principle intact.
  Outcome: A6 is grounded in shipped code, not deferred spec.

### Decisions

- **Owner decision (2026-05-31): include generously, curate later.** When asked which harvested decisions to add, the Owner chose "adopt all; put in as much as possible and filter out later." So all 8 candidates were written as vignettes rather than pre-filtered. The 16 are explicitly a *superset to be trimmed during finalization*, not a final cut. Tradeoff: decisions.md is temporarily long; the curation pass is deferred to publication Step 2.
- Verification-record sweep (source 2) produced no vignette beyond the daily-log harvest: the conditional-pass / strengthening narratives (gate, policy, review) corroborate B5/B6/A5 and the C1 verification-discipline theme rather than standing as separate decisions. Recorded so a later worker does not re-sweep expecting more.

### Next steps

1. Curate the 16 vignettes down to the final cut during decisions.md finalization (publication_plan Step 2). Candidate trims if the doc must shrink: B7 (key minimalism) and B8 (trace separation) are the most implementation-detail-flavored.
2. Proceed to publication_plan Step 1 (bilingual scaffold + Mermaid architecture diagram in README) and Step 2 (case study, curating 3–5 decisions from decisions.md).
3. Commit boundary: this is presentation/docs work — commit separately from any code slice per the established convention.

### Verification

- Documentation-only change. Verified every newly-cited link/path exists: `schemas/agent_trace.schema.json`, `schemas/source_manifest.schema.json`, `config/policy.yaml`, the three 2026-05-28 verification records, `rule_3_boundary_tightening.md`, the 2026-05-2[6-8] work logs, and `ideation_assessment_harness_v2.2.md` — all present.
- No code or test surface touched; full suite unchanged at 200 passing (last recomputed v1.30, 2026-05-29).

## Curation Pass (`docs/decisions.md`: 16 → 11)

### Goals

- Honor the Owner's "include generously, curate later" intent by trimming the 16-vignette superset down to a final cut for the standalone decision record.

### Completed work

- Ranked all 16 vignettes on portfolio value (distinctiveness / senior signal / narrative strength / overclaim risk) and presented three cut depths (light=14, moderate=11, tight=9) with concrete keep/drop previews.
- **Owner chose "moderate" (11).** Applied the cut to `docs/decisions.md`:
  - **Kept 11:** A1, A2, A3, A4, B1, B2, B3, B4, B5, C1, C2.
  - **Dropped 5:** A5 (gate blocking scope), A6 (no-opinion-on-thresholds), B6 (review never auto-accepts), B7 (decision-record key minimalism), B8 (raw/audit trace separation).
  - **A5 folded into A3:** A3's trade-off paragraph now carries the "not every confirmed finding blocks — exit 1 scoped to three design-invalidating types" point in one sentence, so the gate-scope judgment survives without a standalone vignette. A3's Confirm gained the `plan §5.6 (gate blocking scope)` citation.
- Updated `HANDOFF.md` WIP/next-task to reflect the 11-vignette final cut, the 5 dropped (recoverable), and that the next step is publication_plan Step 1/2.

### Decisions

- Curation depth = **moderate (11)** per Owner. Rationale: removes thematic overlap (B6 with A3; A5 with A3) and the most implementation-detail-flavored entries (B7, B8, A6), so each surviving vignette carries a distinct kind of judgment — matching the publication principle "decisions and process over code" without diluting the signal across 16 entries.
- Dropped vignettes are intentionally **not deleted from history**: their full text remains in this work log's harvest section + git, so a later finalization pass (or the case study) can resurrect any of them if needed.

### Next steps

1. publication_plan Step 1 — bilingual scaffold (EN/KO pairs, language-switch header, README Mermaid diagram).
2. publication_plan Step 2 — `docs/case_study.md`, curating 3–5 decisions *from the 11* (link, don't re-derive).
3. `decisions.md` `.ko` mirror is deferred to Step 6.5 (content now frozen).

### Verification

- Post-curation structure check: `grep -cE "^### [A-C][0-9]\." docs/decisions.md` = 11; headers are exactly A1–A4, B1–B5, C1–C2.
- Dangling-reference scan for removed IDs (`see A5/A6`, `(B6/B7/B8)`, etc.): NONE — no surviving vignette references a dropped one (the only A5-style content is now inlined in A3).
