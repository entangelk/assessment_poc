<!-- .ko mirror created on finalize (publication_plan §7b) -->

<p align="center">
  <a href="./decisions.md"><img src="https://img.shields.io/badge/Language-EN-111111?style=for-the-badge" alt="English"></a>
  <a href="./decisions.ko.md"><img src="https://img.shields.io/badge/Language-KO-6B7280?style=for-the-badge" alt="한국어"></a>
</p>
<p align="center"><sub>Switch language / 언어 전환</sub></p>

# Design Decisions

The value of this project is not the line count — it is **why it is shaped the
way it is**. I recorded these decisions *as they happened*: in the
implementation plan's change history (v1.0 → v1.30), in daily work logs, in the
ideation documents, and in independent verification records. Nothing here was
reconstructed afterward for presentation; every entry links to its
contemporaneous, timestamped source.

**On how I worked:** I built this with AI agents — for drafting, for candidate
generation, and (deliberately) for *independent audit* of my own work. I am not
hiding that; in 2026 the skill worth showing is not typing code, it is **framing
the problem, directing the agents, and exercising the judgment about which
decision is correct.** So these entries are written in the first person: the
agents executed and probed, the decisions were mine.

Each decision follows the same shape: **what was at stake → the decision and why
→ the trade-off → how it was verified → where to confirm.**

---

## Part A — What this tool is, and what I refused to build

### A1. The first-class user is an AI agent, not a human

**Stake.** Early drafts treated this as a normal CLI with an "LLM adapter"
bolted on. But the realistic caller of an assessment-validation tool is itself
an AI agent in a pipeline, not a person typing commands.

**Decision (v1.2).** I made *agent-as-user* a first principle. The LLM
integration sits behind a **framework-agnostic `AgentRunner` protocol** (Claude
Agent SDK as the default, swappable as one module), and the CLI is a **contract
an agent can consume**: a stable output core (`status`, `exit_code`, `command`,
`next_actions`), `--output json`, separated stdout/stderr, actionable errors,
and a `schema --command <name>` introspection command so a caller can
self-discover the interface.

**Trade-off.** This is more upfront contract design than a human-facing CLI
needs, and it constrains every later feature to keep the envelope stable. I
accepted that: the stable contract is the product, not a convenience.

**Confirm.** Plan change log v1.2; `tests/test_cli_output_contract.py`.

### A2. The scope boundary, drawn by what I rejected

A tool is defined as much by what it refuses to do. Three rules were proposed
and I rejected each one on principle, not on effort:

- **L3 — fan-out / weight-distribution lint → rejected.** If every requirement
  is public, how an evaluator distributes weight is legitimate **design
  discretion**, not a hidden trap. The tool protects candidates from *undisclosed*
  criteria, not from choices they can see. No candidate-protection value → out.
- **L8 — automatic scoring-drift detection → rejected (manual kept).** An
  agent-based detector costs more than it is worth here, and the invariant it
  chases ("no scoring criterion absent from the spec") is already partly caught
  by Rule 1; genuine drift on an *existing* link is the responsibility of the
  human final review, recorded in `final_review_record.drift_observations[]`.
- **L9 — contradictory-criteria detection → rejected.** Two scoring criteria
  contradicting each other is a failure of *design*, not of scoring validation.
  That belongs to a future "design validation" family. Rejecting it kept this
  PoC's responsibility boundary sharp: **scoring-consistency, not design
  critique.**

**Why this matters.** Scope creep is the default failure mode of a PoC. Each
rejection is a deliberate line that keeps the system explainable in one
sentence.

**Confirm.** Ideation v2.2 §4–§5 (L3/L8/L9 rejection rationale, Owner-decided).

### A3. `check` never blocks; only `gate` does

**Stake.** It is tempting to let the deterministic checker return a pass/fail.
That would quietly turn a *linter of assessment design* into an *automatic
judge* — and an automatic judge that can be wrong is worse than none.

**Decision (v1.3, v1.6).** `check` only ever emits **provisional** findings. The
single command allowed to return a confirmed external verdict is `gate`, and
`gate` only reads a **human final-review record**. `ai_judgement` trace links do
not count as final coverage until a human accepts or overrides them. The machine
analyzes; the human judges.

**Trade-off.** Two commands and a mandatory human step instead of one
fire-and-forget call. That friction is the point.

**Confirm.** Plan change log v1.3/v1.6; verification record
[gate_initial_slice.md](verifications/2026-05-28/gate_initial_slice.md).

---

## Part B — How I kept the system honest

### B1. The `validated` label that quietly lied → a staged integrity model

**Stake.** Every candidate run carries an `integrity_status`. The contract
defined `validated` as *"all Rule 0 checks passed; eligible for compacting and,
downstream, for the deterministic assessment."* `validated` is the gate into the
part of the system that produces real verdicts.

**What the audit found.** I had an AI agent independently verify each slice. On
the run-integrity classifier it probed a run whose `trace_link` pointed at a
non-existent rubric and spec, with a fabricated evidence quote — and the
classifier returned `validated`, **zero errors**. It was stamping `validated`
after only two cheap checks (schema + audit-trace attribution) while the deep
reference and quote checks were still deferred. **No data was corrupted — the
downstream consumers (compacting, assessment) don't exist yet.** This was caught
at the *contract* level, before anything could rely on the lie. Catching a
latent trap proactively is the whole reason the independent audit exists.

**Decision.** I did not patch the classifier silently — the *label* was making a
promise the code didn't keep. I reconciled the contract instead, by **staging
the model**: a run that passes only the cheap checks is now
`structurally_validated` (a real state, no claim of deep correctness, **not**
compacting-eligible); `validated` is reserved for runs that pass full Rule 0.

**The follow-on principle.** When the deep checks landed, failures had to be
bucketed. The first attempt folded *source-grounding* failures into
`quote_mismatch` — but that label means "the evidence quote isn't a substring of
the spec text," and an ungrounded spec is a different failure. The label would
lie again. So I split failures three ways (`invalid_reference` /
`source_grounding_mismatch` / `quote_mismatch`) under a rule I'll state plainly:

> **Split states only as far as a downstream consumer actually branches on the
> difference, and as far as the name would otherwise mislead. Not further.**

A precedence order picks the representative status when several fire, and an
unknown future diagnostic falls back to the most conservative bucket.

**Trade-off.** More states + a precedence rule = more surface to maintain. I
accepted it: **a label that lies is worse than one extra label.** The
fine-grained reason is never lost — every diagnostic is preserved in the error
list regardless of the coarse status.

**Confirm.** Verification records
[candidate_run_integrity_classifier.md](verifications/2026-05-29/candidate_run_integrity_classifier.md)
and [deep_candidate_run_integrity.md](verifications/2026-05-29/deep_candidate_run_integrity.md);
plan §5.4; change log v1.27 → v1.28 → v1.30.

### B2. Compacting is a union, never an auto-merge

**Stake.** Multiple independent agent runs produce overlapping candidates.
The easy move is to "consolidate" — pick winners, drop the rest.

**Decision (v1.4).** I redefined the step from "classified aggregation" to
**auditable compacting**: no quorum, no automatic acceptance, no automatic
classification. Every valid candidate is preserved as an entry — *including ones
found in only a single run* — and entries judged to be the same entity carry
`support` (which runs found them), `identity_basis` (why they were judged
identical), and `variants` (the slightly different phrasings). The compacting
itself is therefore reviewable.

**Why.** Hiding disagreement between runs would launder uncertainty into false
confidence. Determinism is scoped honestly: I only guarantee *"same compacted
artifacts + same semantic-verification artifacts → same findings"*, not that two
runs of an agent produce the same candidates.

**Trade-off.** Reviewers see more, not less — every entry survives to review.
That is the correct cost for not hiding uncertainty.

**Confirm.** Plan change log v1.4; plan §5 (`support`/`identity_basis`/`variants`).

### B3. Semantic quotes are not forced to be literal substrings

**Stake.** Rule 0 checks that an evidence quote is grounded in the spec. The
strict form — exact substring match — is great for determinism but wrong for
paraphrased, meaning-level evidence; it would reject valid quotes.

**Decision (v1.5).** Evidence carries a **`verification_mode`** per quote:
`token_sequence` (strict substring, fully deterministic) vs `ai_judgement`
(reference integrity only, routed to review). The PoC default is `ai_judgement`;
strict checking is **opt-in** for claims that are genuinely quantifiable. The
deep integrity audit later added an explicit over-strict guard so an
`ai_judgement` quote is never failed for not being a literal substring.

**Trade-off.** Two modes instead of one universal rule. But a single rule would
have been wrong in one direction or the other for half the inputs.

**Confirm.** Plan change log v1.5; deep-integrity verification record
(over-strict `ai_judgement` guard).

### B4. Everything anchors to an immutable source snapshot

**Stake.** A validator that trusts the model's memory of the source can't be
trusted itself.

**Decision (v1.1, v1.6).** No DB, no RAG. Specs and rubrics are frozen into an
immutable snapshot with a `sha256`, and every item and quote carries a
line/span `source_ref` back into it. `--source-manifest` is a **mandatory**
argument to `check` (v1.8) — a missing manifest is `invalid_input`, not a
silent pass. Fixtures recompute their hashes against the manifest in tests.

**Trade-off.** More ceremony per input. But it makes every claim independently
verifiable against the original text, which is the entire premise.

**Confirm.** Plan change log v1.1/v1.6/v1.8; `schemas/source_manifest.schema.json`.

---

## Part C — The process itself

### C1. I had an AI audit my work — and I let it withdraw a verdict

**Stake.** A green test suite is necessary but not sufficient; it proves the
code does what the tests say, not what the spec demands.

**Decision.** I made independent verification a first-class artifact
(`docs/verifications/`), with rules I held the audit to: every spec branch —
both "should fire" and "should NOT fire" — must map to a regression; a guard
must fail in **both** directions (the original bug can reappear *and* an
over-correction is caught); and a missing guard is a **blocking** finding, never
reframed as "future work." When verification surfaced a contract gap, the slice
did not close until the *contract* was reconciled — not just the code.

This discipline has teeth: an initial Rule 3 verdict was **withdrawn** and
re-issued after the audit found the boundary checks were incomplete. I would
rather record a withdrawn verdict than ship a green bar that lies.

**Trade-off.** It is slower. Every slice carries an audit cost. For a tool whose
entire job is *trustworthy validation*, shipping fast and wrong defeats the
purpose.

**Confirm.** Verification records under `docs/verifications/`, e.g.
[rule_3_boundary_tightening.md](verifications/2026-05-27/rule_3_boundary_tightening.md)
(supersedes the withdrawn initial verdict); the verification rules live in
`CLAUDE.md` / `AGENTS.md`.
