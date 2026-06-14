<!-- .ko mirror created on finalize (publication_plan §7b) -->

<p align="center">
  <a href="./ideation_assessment_harness_v2.2.md"><img src="https://img.shields.io/badge/Language-EN-111111?style=for-the-badge" alt="English"></a>
  <a href="./ideation_assessment_harness_v2.2.ko.md"><img src="https://img.shields.io/badge/Language-KO-6B7280?style=for-the-badge" alt="한국어"></a>
</p>
<p align="center"><sub>Switch language / 언어 전환</sub></p>

# Ideation v2.2 — Rubric Lint Rules (Inverse Validation Family)

> **Revised 2026-05-27** (same date as final lock): the Owner immediately resolved remaining item 1 in §9.2 (the concrete form of the L6 safeguard) and remaining item 3 (L8 trace_drift handling). As a result, L6 was promoted from the v1.12+ slice in §7 to the **v1.11 slice** (L1+L5+L6 as one bundle). During implementation entry, the Owner resolved the contradiction between L6's `bonus-only` name/payload and wording that included `qualitative`, so L6 was fixed to target bonus traces only, while qualitative consistency was split into a later Rule 2-family rule. For detailed decision rationale, see the "Ideation v2.2 Revision" and "Phase 0 Rule L6 Implementation" sections in `docs/daily_logs/2026-05-27/work_log.md`. This in-place revision does not create a separate v2.3 document (paired with plan v1.10 -> v1.13 version updates).

## 0. Document Purpose and Position

v2.2 does not replace v2.1. The core invariant of v2.1 ("every scored rubric item must be traceable to an item in the candidate-facing spec") remains valid, and v2.2 proposes adding its **inverse rule family**.

This document is in the ideation stage, and promotion into plan v1.11 proceeds only after separate review. In other words, this document is not itself an implementation instruction (avoiding the anti-pattern where HANDOFF effectively becomes the spec).

### 0.1 Spec-precedence Position (Finalized)

Owner decision: the latest ideation document comes first within the ideation layer.

```text
plan v1.10  >  ideation v2.2  >  ideation v2.1  >  ideation v2  >  ideation v1
```

There is no area limitation. If v2.1 and v2.2 cover the same area, v2.2 takes precedence. In all areas not covered by v2.2 (v2.1 §1.1-§1.5 problem definition, §2 invariant, §5 MVP scope, §6 data model draft, §10 LLM role, etc.), v2.1 remains canonical. plan v1.10 is highest for all implemented areas (Rule 0-3).

---

## 1. Motivation

### 1.1 All Rules Through v2.1 Point in the Coverage Direction

Rules 0-3 implemented in plan v1.10 §6 all ask the same question.

> "Is what should exist actually present?"

- Rule 0: are references broken (missing IDs, missing evidence, snapshot mismatch)?
- Rule 1: does a scored rubric have a trace?
- Rule 2: does a must spec have scored grading?
- Rule 3: is the weight of a scored rubric traced only to optional specs below the threshold?

These four rules look for **absence / insufficiency**.

### 1.2 The Mirror Problem — The Area Not Covered

Scoring design has the mirror problem.

> "Has something been included that should not be there?"

- Is the same spec being scored both in core scoring and bonus scoring?
- Does a bonus carry as much differentiating power as core scoring (= effectively core scoring but labeled as bonus)?
- Has an evaluation axis not stated in the spec seeped into scoring?
- Does scoring reward behavior that the spec forbids?
- Do two scoring criteria contradict each other?

None of these questions is caught by current Rule 0-3. Rule 1 is adjacent in part (it catches scored rubric items with no trace), but cases where "a trace exists but is attached incorrectly" or "scoring rewards something forbidden by the spec" pass.

### 1.3 Lint Analogy

This pattern is like software linting. A linter automatically detects code that the compiler accepts but that is "syntactically valid yet undesirable." The lint rule family in v2.2 detects patterns that **pass the trace_links schema but are bad scoring design**.

### 1.4 Primary Motivation Identified by the User

The plan separates the **written-response scoring area** (evaluating stated requirements) from the **creative scoring area** (evaluating unstated excellence). If those two areas are managed separately, the creative area can encroach on the written-response area, or criteria absent from the spec — or forbidden by the spec — can seep into the creative area. The primary goal of v2.2 is to catch that encroachment systemically.

---

## 2. Core Hypothesis — Inverse Invariant

Extend the v2.1 invariant as follows.

> (v2.1) Every scored rubric must be traceable to the spec.
> (v2.2) Every rubric must not contradict the spec, and the same spec must not be scored twice.

These two invariants can be verified independently. v2.1 locks *coverage*; v2.2 locks *exclusion*. Scoring-design coherence is systemically guaranteed only when both axes are locked.

---

## 3. Taxonomy

Every rule in this family (hereafter "Lint Rules") belongs to one of the following three layers.

- **L-DET (deterministic)**: implementable immediately with the current schema and deterministic core. Phase 0 scope.
- **L-SEM (semantic)**: requires a verifier-agent (`ai_judgement` path). Phase 2+.
- **L-SCH (schema-dependent)**: requires schema extension first. After extension, absorbed into either L-DET or L-SEM.

**Owner confirmed (this document)**:

- Rule family naming uses `Rule L1, L2, ...`. This visually distinguishes it from the coverage family (`Rule 0~3`) and makes clear that it is the lint family.
- Finding type names use the candidates proposed in §4-§5 (`double_scored_spec`, `bonus_weight_encroachment`, ...) as-is. Readability is the top criterion.

---

## 4. Lint Rules — L-DET (Deterministic, Phase 0 Possible)

### Rule L1. Cross-role Double Scoring

- **Status**: adopted (Owner confirmed, promoted to v1.11).
- **Condition**: the same `spec_id` is referenced by both `trace_links` from a rubric with `evaluation_role == scored` and `trace_links` from a rubric with `evaluation_role == bonus`.
- **Result**: `medium`, `provisional`.
- **Finding type**: `double_scored_spec`.
- **Intent**: detect inflated effective weight caused by the same spec being scored in both core scoring and bonus scoring. This is the most direct form of the encroachment case the user identified in §1.4.
- **Limit**: legitimate cases exist — for example, scored covers basic behavior while bonus covers deeper / edge-case handling of the same spec. Therefore this is medium, not high.
- **Deep-review safeguard (Owner confirmed)**: do not leave the medium finding as a bare emission; guarantee human review through both of the following paths.
  - (a) **Extended finding payload**: a `double_scored_spec` finding includes `scored_rubric_id`, `bonus_rubric_id`, `spec_id`, the `title` / `description` or `text` of both rubric items, and the `semantic_status` of both links in a single payload. The reviewer must be able to distinguish justified from unjustified cases on one screen.
  - (b) **Separate review queue entry**: add a `type: double_scoring_review` entry to `review_queue.yaml` for the same emission. If the semantic verifier judges it as "justified deepening," it passes as `human_overridden`; if judged unjustified, the finding is promoted to confirmed in final review.
  - Cost: payload extension is free; review queue entry adds one verifier call. Owner decision: introduce both.
- **Two-directional regression guards**:
  - under-strict: same spec_id traced by both scored+bonus -> emit + payload includes both rubric_ids.
  - over-strict A: spec_id traced only by scored -> no emission.
  - over-strict B: different spec_ids (one scored, one bonus) -> no emission.

### Rule L2. Bonus Weight Encroachment

- **Status**: adopted (Owner confirmed, v1.12+ separate slice).
- **Condition**: `sum(weight of role==bonus rubrics) / sum(weight of role==scored rubrics) >= policy.lint.bonus_ratio_threshold` (PoC default: `0.25`)
- **Result**: `medium`, `provisional`.
- **Finding type**: `bonus_weight_encroachment`.
- **Intent**: if bonus carries as much differentiating power as core scoring, it is effectively scored while being labeled "bonus" to candidates — a mismatch between disclosure and scoring role.
- **Policy parameter**: `policy.lint.bonus_ratio_threshold`. Defined in §8. Owner decision: "Each company has different policy; this project has no reason to hard-code the threshold — expose it in the policy file and let users tune it to their team's standard."
- **Limit**: the ratio has no absolute standard. 0.25 is only the PoC default, not an authoritative value.

### Rule L3. Spec Over-trace

- **Status**: **rejected (Owner decision)**.
- **Reason for rejection**: even if candidates do not know the effective weight of one spec line, the principle is that they should follow the spec. If all information is public rather than asymmetrically disclosed, evaluator weight distribution belongs to design discretion. Therefore this rule adds no value for candidate protection.
- **Residual risk (for record)**: this rule will not catch a case where evaluators attach multiple scoring items to the same spec without realizing the effective weight. That is an evaluation-design quality issue, not candidate protection; it is handled in a future "design validation" extension (§5 Rule L9).
- (Original proposal — not applied) Condition: a single `spec_id` is referenced `>= policy.lint.spec_trace_fanout_threshold` times in `evaluation_role == scored` rubric traces (PoC default candidate: `4`). Result: `informational`, `provisional`. Candidate finding type: `spec_overtraced`.

### Rule L4. Duplicate Trace Link

- **Status**: adopted (Owner confirmed, v1.12+ separate slice, remains independent in lint family).
- **Condition**: the same `(rubric_id, spec_id)` pair appears more than once in `trace_links`.
- **Result**: `medium`, `provisional`.
- **Finding type**: `duplicate_trace_link`.
- **Intent**: data-quality defect. In later stages (semantic verification, gate promotion, scoring calculation), this can be double-weighted or the two links' `semantic_status` values can conflict.
- **Placement decision (Owner confirmed)**: keep it independent in the lint family rather than absorbing it into Rule 0 (reference integrity). Reason: blocking it as an input error (exit 2, stop work) would be consistent, but a real duplicate may be (a) a mistake, (b) intentional emphasis, or (c) separate links for different evidence/rationale. It is more appropriate to surface it as a lint finding for human judgment (pass / penalize / fix). This also leaves room to use it as a scoring penalty.

### Rule L5. Bonus Traces Only Mandatory

- **Status**: adopted (Owner confirmed, promoted to v1.11).
- **Condition**: **all** trace targets of a rubric item with `evaluation_role == bonus` have `requirement_level == must`.
- **Result**: `medium`, `provisional`.
- **Finding type**: `bonus_grades_mandatory_only`.
- **Intent**: mirror of v2.1 §2 action (3) ("demote to bonus / qualitative note"), where bonus should reward behavior beyond the spec. If all traces point only to must specs, the bonus is effectively rescoring mandatory requirements — the identity of bonus collapses.
- **Difference from L1**:
  - L1: the same spec_id appears in both scored and bonus — **direct double-counting**.
  - L5: bonus only looks at must specs — even without overlap with scored, **the bonus area is wrongly designed**.
- **Two-directional regression guards**:
  - under-strict: all bonus traces target must specs -> emit.
  - over-strict A: at least one bonus trace targets an optional/informational spec -> no emission.
  - over-strict B: bonus has no trace at all -> no emission (responsibility of Rule 1's `orphan_bonus_rubric_item`).

### Rule L6. Mandatory Spec Bonus-only Coverage

- **Status**: adopted (Owner confirmed, **promoted to v1.11** — moved from v1.12+ in the 2026-05-27 revision).
- **Adoption path**: the draft considered rejecting it (same information-asymmetry logic as L3 — if a must spec is in the spec, candidates know it is must). The Owner corrected this to adoption after deciding that "it would be good to have a safeguard for cases where a must spec is scored only as bonus." Once the concrete safeguard form was decided (below), it was promoted to v1.11 and could share fixtures with L1+L5.
- **Condition**: a trace exists for a spec_item with `requirement_level == must`, but every rubric in those traces has `evaluation_role == bonus`.
- **Result**: `high`, `provisional`.
- **Finding type**: `mandatory_spec_bonus_only_traced`.
- **Intent**: a must spec has no core scoring and only bonus attached. Rule 2 catches "must spec has no scored trace" as medium, but this rule is one step more specific — "not only absent, but designed to be evaluated *only as bonus*." Candidates may perceive a core requirement as bonus-like.
- **Relationship to Rule 2**: special case of Rule 2. Co-emission is possible. Because Rule 2 is medium, there is value in flagging this one level higher (high).
- **Qualitative boundary (Owner confirmed, reconciled during implementation entry)**: qualitative is not a scoring/bonus role, so it is excluded from the L6 emission condition. A must spec with qualitative-only or bonus+qualitative traces and no scored trace belongs to a separate later Rule 2-family rule.
- **Safeguard (Owner confirmed)**: adopt the same pattern as L1. Reason: L6 also requires semantic judgment to distinguish justified from unjustified cases (for example, intentional bonus placement vs. design mistake), and using the same mechanism as L1 unifies the review interface.
  - (a) **Extended finding payload**: a `mandatory_spec_bonus_only_traced` finding includes `spec_id` (must spec), all `bonus_rubric_ids[]` tracing that spec, the `title` / `description` or `text` of each bonus rubric, each link's `semantic_status`, and `spec_item.text` or `source_ref` in one payload.
  - (b) **Separate review queue entry**: add `type: mandatory_spec_bonus_review` to `review_queue.yaml`. If the semantic verifier or final reviewer judges it as "intentional bonus placement," it becomes `human_overridden`; if unjustified, the finding is promoted to confirmed (separate type from Rule 2's confirmed orphan_must_spec).
- **Two-directional regression guards**:
  - under-strict: must spec has traces but all are bonus -> emit + payload includes all bonus_rubric_ids + review_queue entry is created.
  - over-strict A: must spec has at least one scored trace -> no emission.
  - over-strict B: must spec has no trace at all -> no emission (Rule 2 responsibility).
  - over-strict C: must spec trace includes any qualitative -> no emission (responsibility of a later Rule 2-family rule).

---

## 5. Lint Rules — L-SEM (Semantic, Phase 2+)

This family is verified through the verifier-agent's `ai_judgement` path. Because emissions are not deterministic, all are finalized through the `human_overridden` path.

### Rule L7. Forbidden-clause Violation

- **Status**: adopted (Owner confirmed, separate plan version v1.12+ — paired with C1 schema extension).
- **Condition**: a rubric traced to a spec_item with `requirement_level == forbidden` (introduced by C1) exists (= scoring rewards behavior forbidden to candidates).
- **Prerequisite**: adoption of C1 in §6 (Owner confirmed). This makes L7-DET implementation possible.
- **Result**: `high`, `provisional` -> `confirmed` after final review or verifier approval.
- **Finding type**: `forbidden_clause_rewarded`.
- **Intent**: the largest kind of contradiction: scoring rewards what candidates were told "do not do." Direct breach of candidate trust.
- **Implementation layers**:
  - L7-DET: possible immediately after C1 adoption — schema comparison detects any rubric traced to a `forbidden` spec.
  - L7-SEM: verifier detects natural-language forbidden clauses in the spec body that were not marked as `forbidden`. Phase 2+. Burden is similar to the reason for rejecting L8 (cost), so priority is low.

### Rule L8. Criterion Drift in Scored Rubric

- **Status**: **automatic detection rejected (Owner decision). Manual discoveries are recorded in the final_review_record.**
- **Reason for rejection**: verifier-agent call cost exceeds the value of automatic detection for this rule. Also, the invariant "there must not be scoring criteria absent from the spec" is partially caught by Rule 1 (missing trace_link detection); when a trace_link exists but the actual scoring criterion has drifted, manual final review owns that responsibility.
- **Manual discovery recording method (Owner confirmed, 2026-05-27 revision)**: if a reviewer discovers drift during final review, record it in `final_review_record.drift_observations[]`. Each observation includes `rubric_id`, `linked_spec_ids[]`, `observed_drift_summary` (free text), `severity` (`informational` / `medium` / `high`), and `recommended_action` (`revise_rubric` / `revise_spec` / `accept_with_note`). No automatic finding is emitted; it remains in the audit log as part of final review.
- (Original proposal — automatic detection not applied) Condition: a rubric trace_link points to a spec_id, but that rubric's actual scoring criterion is an evaluation axis that does not appear in the spec_item body (semantic mismatch). Candidate result: `medium`, `provisional`. Candidate finding type: `criterion_drift`. This is a case where the "Hidden Criterion" pattern from v2.1 §1.1 recurs at rubric level. Automatic detection is out of PoC scope because the cost is not worth it, but the area can still be tracked through the manual recording path above.

### Rule L9. Mutually Contradictory Rubrics

- **Status**: **rejected (Owner decision)**.
- **Reason for rejection**: contradiction between two scoring criteria is a failure in the spec-rubric *design stage*, not a responsibility of the scoring-validation stage. If this project later expands into a "design validation" family, that family will handle it. This decision clearly limits the PoC responsibility boundary to "scoring coherence."
- (Original proposal — not applied) Condition: two rubrics reward opposing behaviors (semantic pair check). Result: `medium`, `provisional`. Candidate finding type: `rubric_self_contradiction`. Because this is pairwise, N rubrics require N(N-1)/2 verifier calls — also a large cost burden.

---

## 6. Schema Extension Candidates — L-SCH

### C1. `requirement_level: forbidden`

- **Status**: adopted (Owner confirmed). Paired with L7 adoption.
- **Change**: add `forbidden` to the `requirement_level` enum in `schemas/spec_items.schema.json`.
- **Meaning**: this spec_item defines behavior that candidates **must not** do.
- **Impact**:
  - The deterministic side of Rule L7 becomes possible (a rubric traced to a `forbidden` spec immediately becomes a high finding).
  - Rule 2 (must spec coverage) is unaffected. Rule 2 checks only `must`.
  - Rule 3 (optional weight) is unaffected.
  - Extend the `RequirementLevel` enum in `models.py`.
  - Existing fixtures are unaffected (a value is added, not changed).
- **Plan promotion timing**: not included in v1.11 (v1.11 is L1+L5 only). Enters in a separate plan version bundled with L7, v1.12+.
- **Cost**: small. Possible with one plan update + one slice.

### C2. `exclusion_links` (Symmetric Trace Table)

- **Change**: a new table parallel to `trace_links`, named `exclusion_links`. Each entry is `(rubric_id, spec_id, reason)`.
- **Meaning**: "this rubric must not score this spec."
- **Assessment**: **not recommended**. If C1 exists, it absorbs most use cases (rubric traced to a forbidden spec -> caught by L7). The benefit is small compared with the maintenance cost of a separate table (schema, integrity checks, fixtures, CLI args).
- **Reconsideration condition**: revisit only if real assignment application repeatedly discovers cases that C1 cannot express.

### C3. (Deferred After Review) `rubric_items.section`

- The "written-response scoring area" vs. "creative scoring area" distinction the user identified in §1.4 is already sufficiently represented by `evaluation_role: {scored, bonus, qualitative}`.
- Adding a separate `section` field risks conflicts between two classifications (for example, `role: scored, section: 창의` becomes possible).
- **Conclusion**: do not introduce a new field; keep using `evaluation_role`.

---

## 7. Plan Promotion Plan (Owner Confirmed, 2026-05-27 Revision)

| Plan version | Included rules | Notes |
|---|---|---|
| **v1.11** | **L1 + L5 + L6** | Core 3 rules for the bonus area. All L-DET. Shared fixture. Split into slices (L1 -> L5 -> L6, following the Rule 1 slice 1/2/3 pattern). Once the L6 safeguard (payload+review_queue) was finalized, it was unified with L1 under the same mechanism. |
| v1.12+ (separate) | L2 | Policy-threshold exposure slice. Can stand alone. |
| v1.12+ (separate) | L4 | Duplicate trace link detection. Can stand alone. Not absorbed into Rule 0. |
| v1.12+ or separate | L7 + C1 | Paired with spec schema extension (C1). L7-DET possible. L7-SEM after Phase 2 verifier-agent. |

**Rejected** (no re-discussion): L3 (if it is not information asymmetry, weight distribution is evaluator discretion), L8 automatic detection (insufficient value for verifier cost — manual discovery is recorded in `final_review_record.drift_observations[]`), L9 (design validation area, outside PoC responsibility boundary).

**Revision note (2026-05-27)**: in the draft, L6 was separated into v1.12+, but once its concrete safeguard form was decided to be the same pattern as L1, mechanism consistency + fixture-sharing benefits exceeded the cost of separation. L6 is included in v1.11.

---

## 8. New Policy Parameter (Owner Confirmed)

Add a lint section to `config/policy.yaml`.

```yaml
lint:
  bonus_ratio_threshold: 0.25          # Rule L2
```

`spec_trace_fanout_threshold` is removed because Rule L3 was rejected. Initial value `0.25` is only the PoC default, not an authoritative value — per Owner decision, "company/team policies differ, so users should tune it to their own standard." This value has the same status as `optionality_mismatch.weight_threshold: 10` in plan v1.10.

---

## 9. Decision Record and Remaining Items

### 9.1 Finalized Decisions (Owner, 2026-05-27)

1. **Spec-precedence**: latest ideation first -> `plan v1.10 > v2.2 > v2.1 > v2 > v1`. No area limit (§0.1).
2. **Rule family naming**: `Rule L1, L2, ...` (§3).
3. **Finding type naming**: use the candidates in this document §4-§5 as-is (`double_scored_spec`, `bonus_weight_encroachment`, `duplicate_trace_link`, `bonus_grades_mandatory_only`, `mandatory_spec_bonus_only_traced`, `forbidden_clause_rewarded`). Readability first (§3).
4. **Adopted rules**: L1, L2, L4, L5, L6, L7 (6).
5. **Rejected rules**: L3, L8 automatic detection, L9 (3) — no re-discussion. L8 automatic detection is rejected, but manual discovery records are preserved (item 11 below).
6. **Schema extension**: C1 (`requirement_level: forbidden`) adopted. C2 deferred, C3 unnecessary.
7. **L4 placement**: remains independent in lint family (not absorbed into Rule 0). Kept open for use as a scoring penalty.
8. **L1 deep-review safeguard**: introduce both extended finding payload and separate review queue entry.
9. **Plan v1.11 promotion scope**: L1 + L5 + **L6** (L6 added in the 2026-05-27 revision). Remaining adopted rules (L2, L4, L7+C1) are separated into v1.12+.
10. **Policy threshold**: keep `bonus_ratio_threshold = 0.25`. Teams can freely tune it — this project only provides a default.
11. **L6 safeguard (2026-05-27 revision)**: adopt the same pattern as L1 — extended payload + review_queue `mandatory_spec_bonus_review` entry. See §4 Rule L6.
12. **L8 manual discovery record (2026-05-27 revision)**: add `final_review_record.drift_observations[]`. No automatic detection; manually recorded as part of final review. Plan §5.6 must be updated.
13. **L6 qualitative boundary (reconciled during 2026-05-27 implementation entry)**: L6 emits only when every traced rubric is `bonus`. A must-spec no-core-scoring problem that includes `qualitative` is split into a separate later Rule 2-family rule. Reason: qualitative is not a scoring/bonus role, and the existing finding/queue payload explicitly represents bonus only.

### 9.2 Remaining Decision Items (Finalize During Future Plan Promotion)

1. **L7-DET vs. L7-SEM priority**: C1 adoption makes L7-DET possible. L7-SEM comes after the Phase 2 verifier-agent. Decide separately whether to enter both layers or close with L7-DET only.

---

## 10. Changes Compared With v2.1

### Added (Owner Confirmed)

- inverse invariant (§2)
- 6 adopted Lint Rule family rules (L1, L2, L4, L5, L6, L7) + preserved record of 3 rejected rules (L3, L8, L9)
- 1 adopted schema extension (C1: `requirement_level: forbidden`)
- 1 new policy parameter (`policy.lint.bonus_ratio_threshold`)
- Plan promotion table (§7, including same-day revision): v1.11 = L1+L5+L6, v1.12+ = L2/L4/L7+C1

### Unchanged

- all invariants in v2.1 (§2)
- the five problem definitions in v2.1 §1.1-§1.5
- Rule 1-6 definitions in v2.1 §7 (plan v1.10 narrowed and implemented Rule 0-3; Rule 4-6 remain unimplemented as "future rules" in plan §6)
- v2.1 §5 MVP scope, §6 data model draft, §10 LLM role
- Rule 0-3 implementation in plan v1.10 — v2.2 does not modify any existing Rule

### Adoption-path Note (Decision Changed During Session)

- L6 was considered for rejection in this document's draft (same information-asymmetry logic as L3), but during Owner review it was corrected to adoption because "a safeguard is needed for cases where a must spec is scored only as bonus."
- **Same-day revision on 2026-05-27**: the concrete L6 safeguard form (same mechanism as L1) and L8 manual discovery recording method (`drift_observations[]`) were decided by the Owner. L6 was promoted from separate v1.12+ work to the v1.11 slice. Rather than create a separate v2.3 document, this v2.2 was revised in place.

### Conscious Exclusions

- automatic scoring, automatic weight adjustment, automatic rule consensus — same out-of-scope boundary as v2.1 §5.3
- candidate behavior analysis, pattern mining — same as v2.1 §5.3

---

## 11. Next Steps

This document is in **final locked state** by Owner decision (2026-05-27, one same-day revision). It requires no code changes and remains ideation until plan promotion.

1. Update plan v1.10 -> v1.11 — add Rule L1 + L5 + L6 specs to §6, add `drift_observations[]` to §5.6 Final Review Record, add `double_scoring_review` / `mandatory_spec_bonus_review` types to §5.7 Review Queue Entry, and add a v1.11 changelog entry to §15. Plan-only change; no code change.
2. After plan v1.11 is locked, implement in slices (L1 -> L5 -> L6, following the Rule 1 slice 1/2/3 pattern).
3. Sequentially promote the remaining adopted items (L2, L4, L7+C1) into plan v1.12+.
4. Resolve this document's remaining decision (§9.2, one item) when L7 is promoted.
