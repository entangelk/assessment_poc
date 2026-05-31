<!-- .ko mirror created on finalize (publication_plan §7b) -->

<p align="center">
  <a href="./audit_index.md"><img src="https://img.shields.io/badge/Language-EN-111111?style=for-the-badge" alt="English"></a>
  <a href="./audit_index.ko.md"><img src="https://img.shields.io/badge/Language-KO-6B7280?style=for-the-badge" alt="한국어"></a>
</p>
<p align="center"><sub>Switch language / 언어 전환</sub></p>

# Audit Index — work logs & independent verifications

A curated guide to the project's contemporaneous record, not a raw dump. Two
trails run alongside the code:

- **Work logs** (`docs/daily_logs/`) — what was built each day, why, and the
  decisions made, written as the work happened.
- **Independent verification records** (`docs/verifications/`) — each implemented
  slice was independently audited (by an AI agent held to a strict, blocking
  discipline). These are a first-class asset: they show the work was checked
  against the spec, not just against a green test bar. See decision
  [C1](decisions.md) for why this discipline exists.

The decision narrative itself lives in [decisions.md](decisions.md); the measured
test/smoke evidence is in [evaluation.md](evaluation.md).

## Work logs (by day)

| Day | Focus |
|---|---|
| [2026-05-25](daily_logs/2026-05-25/work_log.md) | Ideation review; plan v1.0→v1.7 (agent-harness pivot, compacting, gate, source grounding); Phase 0 scaffold + Rule 0 + audit-blocker repair |
| [2026-05-26](daily_logs/2026-05-26/work_log.md) | Rule 1 slices 1/2/3 (orphan scored / unconfirmed coverage / orphan bonus); slice-2.5 plan reconciliation; CLI envelope contract lock |
| [2026-05-27](daily_logs/2026-05-27/work_log.md) | Ideation v2.2 lint family (draft→final→revision); lint Rules L1/L5/L6; Rule 2 + Rule 3 |
| [2026-05-28](daily_logs/2026-05-28/work_log.md) | Initial `gate` + `review` draft writer + safety guards; policy completeness; Phase 2 schema foundations; AgentRunner protocol; audit-trace schema |
| [2026-05-29](daily_logs/2026-05-29/work_log.md) | Candidate schema / attribution / normalization; staged candidate integrity; deep candidate Rule 0 (3-way isolation); verification-record layout |
| [2026-05-31](daily_logs/2026-05-31/work_log.md) | Publication effort: decision harvest + curation; case study; evaluation; LICENSE + secret scan + audit index |

## Independent verification records (by subject)

Notable first — the records that carry a reconciliation or correction story:

- [rule_3_boundary_tightening](verifications/2026-05-27/rule_3_boundary_tightening.md)
  — **a verdict withdrawn and re-issued** after the audit found incomplete
  boundary checks (supersedes the initial Rule 3 pass). The clearest example of
  the discipline having teeth.
- [gate_initial_slice](verifications/2026-05-28/gate_initial_slice.md)
  — **conditional pass**: code behaved correctly on branches that had no named
  regression; the empty boundary-matrix cells were treated as blocking until
  locked, then re-verified to a pass.
- [candidate_run_integrity_classifier](verifications/2026-05-29/candidate_run_integrity_classifier.md)
  + [deep_candidate_run_integrity](verifications/2026-05-29/deep_candidate_run_integrity.md)
  — the audit that caught the **`validated` label promising more than the code
  delivered** (decision [B1](decisions.md)).

Full set, by date:

**2026-05-27** — [rule_2_implementation](verifications/2026-05-27/rule_2_implementation.md) ·
[rule_3_implementation](verifications/2026-05-27/rule_3_implementation.md) ·
[rule_3_boundary_tightening](verifications/2026-05-27/rule_3_boundary_tightening.md)

**2026-05-28** — [gate_initial_slice](verifications/2026-05-28/gate_initial_slice.md) ·
[review_draft_writer](verifications/2026-05-28/review_draft_writer.md) ·
[review_safety_guards](verifications/2026-05-28/review_safety_guards.md) ·
[policy_completeness](verifications/2026-05-28/policy_completeness.md) ·
[agent_runner_protocol_foundation](verifications/2026-05-28/agent_runner_protocol_foundation.md) ·
[audit_trace_schema](verifications/2026-05-28/audit_trace_schema.md) ·
[phase_two_schema_foundation](verifications/2026-05-28/phase_two_schema_foundation.md)

**2026-05-29** — [candidate_schema_foundation](verifications/2026-05-29/candidate_schema_foundation.md) ·
[candidate_audit_trace_attribution](verifications/2026-05-29/candidate_audit_trace_attribution.md) ·
[runner_candidate_normalization](verifications/2026-05-29/runner_candidate_normalization.md) ·
[candidate_run_integrity_classifier](verifications/2026-05-29/candidate_run_integrity_classifier.md) ·
[deep_candidate_run_integrity](verifications/2026-05-29/deep_candidate_run_integrity.md)
