# Changelog

| Date | Change | Detail |
|---|---|---|
| 2026-05-26 | Phase 0 iteration 2 slice 2: Rule 1 `unconfirmed_trace_coverage` finding (medium/provisional), final-coverage boundary fixed at `{human_accepted, human_overridden}`, `clean_assignment` canonical baseline shifted to `status=provisional_findings` with 2 mediums, 85 passing tests. | [Work log](docs/daily_logs/2026-05-26/work_log.md) |
| 2026-05-26 | Phase 0 iteration 2 slice 1.5: `--source-manifest` mandated as a `check` input (plan v1.8 §5.0/§5.1/§11), both non-clean fixtures grounded with source/manifest, new `source_manifest_required` diagnostic, 73 passing tests. | [Work log](docs/daily_logs/2026-05-26/work_log.md) |
| 2026-05-26 | Phase 0 iteration 2 slice 1: Rule 1 `possible_orphan_scored_rubric_item` finding, `orphan_scored_rubric` fixture, two-directional regression guards, 72 passing tests. | [Work log](docs/daily_logs/2026-05-26/work_log.md) |
| 2026-05-25 | Phase 0 implementation iteration 1: package scaffold, Rule 0 reference-integrity engine, `check`/`schema`/`report` CLI, eight JSON Schemas, two fixtures, 31 passing tests, Docker dev workflow. | [Work log](docs/daily_logs/2026-05-25/work_log.md) |
| 2026-05-25 | Implementation plan reached v1.7; read-only multi-run semantic verifier-agent adopted as a required PoC stage. | [Work log](docs/daily_logs/2026-05-25/work_log.md) |
| 2026-05-25 | Implementation plan reached v1.6; provisional findings/gate boundary, source grounding, and canonical ID mapping adopted. | [Work log](docs/daily_logs/2026-05-25/work_log.md) |
| 2026-05-25 | Implementation plan reached v1.5; all Phase 0 pre-decisions adopted; README.md created. Phase 0 ready to start. | [Work log](docs/daily_logs/2026-05-25/work_log.md) |
| 2026-05-25 | Compacting model (v1.4) replaced aggregation-as-classification. Every valid candidate is preserved as a reviewable entry; no quorum, no automatic acceptance. | [Work log](docs/daily_logs/2026-05-25/work_log.md) |
| 2026-05-25 | PoC plan refined to multi-run agent harness (v1.3); intermediate human approval removed in favour of final review only. | [Work log](docs/daily_logs/2026-05-25/work_log.md) |
| 2026-05-25 | PoC plan defined; agent-runner protocol and framework portability adopted (v1.2). | [Work log](docs/daily_logs/2026-05-25/work_log.md) |

## 2026-05-25

- Defined the Assessment Spec Harness PoC implementation plan from v2.1 ideation.
- v1.0–v1.1: initial plan with single LLM adapter, Rule 0–3, fixture-based regression, intermediate human approval.
- v1.2: shifted the LLM integration boundary to a framework-agnostic `AgentRunner` protocol; declared the 1st-class caller to be an AI agent, not a human; added stable CLI contract and agent-consumable output requirements.
- v1.3: replaced single-run candidate approval with a multi-run agent harness; integrity check, aggregation, deterministic validation, and final human review became the canonical flow.
- v1.4: redefined aggregation as auditable compacting (union with `support`/`identity_basis`/`variants` preserved); removed quorum and automatic acceptance; renamed `aggregate`/`consolidated` to `compact`/`compacted`; added Final Review Record schema with `accept`/`hold`/`rerun_requested`/`override` actions and `human_override` provenance.
- v1.5: adopted all three Phase 0 pre-decisions — canonical document precedence, per-entry Rule 0 verification modes (`token_sequence` opt-in, `ai_judgement` default), and layered CLI output stability with a `schema` self-discovery command; unified policy files into `config/policy.yaml`; added `review_queue` entry schema and a dedicated mock runner; created top-level `README.md` documenting the harness for both AI agents and humans.
- v1.6: separated provisional `check` results from final external `gate` verdicts; specified immutable source snapshot/hash/span grounding without DB/RAG; required run-local-to-canonical ID remapping; refined review queue states; and proposed a semantic verifier-agent stage for confirmation.
- v1.7: adopted that semantic verifier-agent stage as mandatory; it runs read-only over compacted links/source snapshots, preserves multi-run proposals separately, and makes the final flow `extract -> compact -> verify -> check -> report -> review -> gate`.
