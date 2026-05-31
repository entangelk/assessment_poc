<!-- .ko mirror created on finalize (publication_plan §7b) -->

<p align="center">
  <a href="./case_study.md"><img src="https://img.shields.io/badge/Language-EN-111111?style=for-the-badge" alt="English"></a>
  <a href="./case_study.ko.md"><img src="https://img.shields.io/badge/Language-KO-6B7280?style=for-the-badge" alt="한국어"></a>
</p>
<p align="center"><sub>Switch language / 언어 전환</sub></p>

# Case Study — Assessment Spec Harness

A proof-of-concept I designed and built (with AI agents) to validate the
*design* of a hiring assessment before any candidate is scored. This is the
narrative version, organized around the decisions; the full standalone decision
record with primary-source citations is in [decisions.md](decisions.md).

## The problem

A hiring assignment has two halves that drift apart: the **public specification**
the candidate reads, and the **private scoring rubric** the evaluator grades
against. When they silently diverge — a *must* requirement that no scored
criterion covers, a creative-judgement criterion that quietly grades something
the spec never asked for, a mandatory requirement that only earns bonus points —
the candidate is judged on undisclosed terms. Nobody notices until it is unfair.

This tool **does not evaluate candidates. It evaluates the assessment design** —
the internal consistency between spec and rubric — and surfaces the gaps as
reviewable findings before anyone is scored.

## The goal

A deterministic, auditable harness that, given a frozen spec + rubric + their
trace links, flags structural defects in the *design* — and that **never issues
an automatic pass/fail**. The first-class caller is an **AI agent** in a
pipeline; humans are the final reviewers, never replaced by the machine.

Scope honesty up front: this is a **proof-of-concept**. The deterministic
validation core and the review/verdict flow are implemented and tested; the
multi-run agent extraction pipeline that would feed them is contract/foundation
only. The boundary is drawn honestly in the [architecture
diagram](../README.md) and the [implementation
status](../README.md) table.

## Key decisions (the heart)

The value here is the judgment, not the line count. Five decisions that shaped
the system — each is one entry below, with the full treatment, trade-offs, and
contemporaneous citations in [decisions.md](decisions.md):

### 1. The first-class user is an AI agent, not a human — `decisions.md` §A1

Early drafts treated this as a normal CLI with an LLM bolted on. I made
*agent-as-user* a first principle instead: a stable output contract (`status`,
`exit_code`, `command`, `next_actions`), `--output json`, a `schema --command`
introspection command an agent can self-discover, and a framework-agnostic
`AgentRunner` protocol. The cost — more upfront contract design, every later
feature constrained to keep the envelope stable — is the point: the stable
contract *is* the product.

### 2. The scope, drawn by what I refused to build — `decisions.md` §A2 / §A4

A tool is defined as much by what it declines to do. I rejected three proposed
rules on principle (weight-distribution lint, automatic scoring-drift detection,
contradictory-criteria detection) because they protect against evaluator
*discretion* a candidate can see, not the *undisclosed* criteria this tool
exists to catch. The same restraint produced the framing pivot that birthed the
whole "lint" rule family: "lint" here is not for my own Python — it is the
**inverse invariant** applied to the scoring structure ("is something here that
should *not* be?").

### 3. `check` never blocks; only `gate` does — `decisions.md` §A3

Letting the deterministic checker return pass/fail would quietly turn a *linter
of assessment design* into an *automatic judge* — and an automatic judge that can
be wrong is worse than none. So `check` only ever emits **provisional** findings;
the single command allowed to return a confirmed external verdict is `gate`, and
`gate` only reads a **human** final-review record. Even then, not every confirmed
finding blocks — the blocking verdict is scoped to three design-invalidating
types. The machine analyzes; the human judges.

### 4. The `validated` label that quietly lied → a staged integrity model — `decisions.md` §B1 (flagship)

Every candidate run carries an `integrity_status`. The contract defined
`validated` as "all integrity checks passed; eligible for downstream assessment."
An AI agent I tasked with **independently auditing** my own work probed a run
whose references were dangling and whose evidence quote was fabricated — and the
classifier returned `validated`, zero errors. It was stamping the gate-status
after only the two cheapest checks. No data was corrupted (the downstream
consumers don't exist yet) — it was caught at the *contract* level, which is
exactly why the independent audit exists. I did not patch it silently: the
*label* was making a promise the code didn't keep, so I **staged the model**
(`structurally_validated` vs `validated`) and later split the failure states
three ways under a rule I'll state plainly — *split states only as far as a
downstream consumer actually branches, and as far as the name would otherwise
lie.*

### 5. I had an AI audit my work — and let it withdraw a verdict — `decisions.md` §C1

A green test suite proves the code does what the tests say, not what the spec
demands. I made independent verification a first-class artifact
([docs/verifications/](verifications/)), held to rules with teeth: every spec
branch maps to a regression, guards must fail in *both* directions, and a missing
boundary lock is a **blocking** finding — never reframed as "future work." The
discipline is real: an initial Rule 3 verdict was **withdrawn** and re-issued
after the audit found incomplete boundary checks. I would rather record a
withdrawn verdict than ship a green bar that lies.

## What I built (today)

Implemented and tested:

- **Rule 0** reference-integrity engine (source-snapshot grounding, evidence
  completeness, mandatory `--source-manifest`).
- **Rules 1–3** (scored-rubric coverage, required-spec coverage, optionality
  consistency) and **lint rules L1 / L5 / L6** (double scoring, bonus
  re-grading mandatory work, mandatory-as-bonus-only).
- **`check` / `report` / `review` / `gate`** with a stable agent-consumable
  envelope and a `schema` introspection command.
- **Agent-runner protocol + deterministic mock**, candidate artifact schemas,
  audit-trace attribution, runner normalization, and a **staged candidate
  integrity model** with deep Rule 0 classification.

Contract / foundation only (deliberately deferred): `extract` / `compact` /
`verify` orchestration, real SDK runners, the Phase 1 manual run, and the full
end-to-end workflow. See the [implementation status
table](../README.md) for the honest area-by-area state.

## How it's verified

- **200 passing tests** with **two-directional regression guards** (each rule
  branch has both an under-strict guard — the original bug can re-fail — and an
  over-strict guard — a normal case is not wrongly flagged).
- **Independent AI verification records** under
  [docs/verifications/](verifications/), produced by an agent held to the
  blocking-on-missing-locks discipline above.
- Fixtures recompute their source hashes against the manifest in tests, so every
  claim is grounded in the original frozen text.

(A measured test + smoke evidence table is the next publication step,
`docs/evaluation.md`, built from real run output rather than transcribed.)

## Limitations / deliberately deferred

- The agent extraction pipeline (`extract` / `compact` / `verify`, real runners)
  is not built — only its contracts and schemas are.
- The tool holds **no opinion on threshold values**; they are caller-tunable
  policy, not authoritative defaults.
- Raw-trace retention/redaction policy is deferred; only the audit trace is
  schema-validated today.
- This is a single-run-quality PoC; determinism is scoped honestly to "same
  compacted + verified artifacts → same findings," not to agent reproducibility.

## What's next

1. `docs/evaluation.md` — measured test/smoke tables from real `docker compose
   run` output.
2. The agent extraction pipeline (`extract` / `compact` / `verify`) on top of the
   existing runner-protocol and candidate-integrity foundations.
3. A first real-assignment manual run (Phase 1).

---

*Built with AI agents — for drafting, candidate generation, and (deliberately)
independent audit of my own work. The decisions were mine; the agents executed
and probed. More on that in [decisions.md](decisions.md).*
