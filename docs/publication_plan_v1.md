# Assessment Spec Harness — Publication Plan v1.0

## 0. Purpose of this document

This is the canonical, living plan for taking this project public as a
portfolio piece. It governs the **publication effort** the way
`implementation_plan_assessment_harness_poc_v1.md` governs the implementation:
single source of truth, versioned, updated as work proceeds. **The plan is
complete at the moment the project is published** — finishing the inventory and
closing the Open Decisions *is* the publication.

This plan is itself a public artifact (Owner decision, 2026-05-29): it shows how
the publication was reasoned about, which is consistent with the project's
core framing — **foreground the decisions and the process, not just the code.**

## 1. Publication principles (non-negotiable)

1. **No overclaiming.** Implemented vs. pending is stated honestly everywhere.
   The repository's own discipline (verification records, "do not reframe gaps
   as future work") applies to the public docs too.
2. **Decisions and process over code.** The differentiator is *why the code is
   the way it is* — the judgment, tradeoffs, and reconciliations — not raw LOC.
3. **Single source of truth per fact.** Each fact (test counts, status, version)
   lives in exactly one document; everything else links. Duplication is the
   drift mechanism we are explicitly removing.
4. **Audit discipline is a first-class asset, shown not hidden.** The
   independent verification records and contract reconciliations are a senior
   signal and should be surfaced, not buried.
5. **English primary + Korean mirror.** Separate files (`*.md` EN, `*.ko.md`
   KO), English is canonical. Each file carries a language-switch header:
   ```html
   <p align="center">
     <a href="./README.md"><img src="https://img.shields.io/badge/Language-EN-111111?style=for-the-badge" alt="English"></a>
     <a href="./README.ko.md"><img src="https://img.shields.io/badge/Language-KO-6B7280?style=for-the-badge" alt="한국어"></a>
   </p>
   <p align="center"><sub>Switch language / 언어 전환</sub></p>
   ```
6. **This plan is public.** Meta-process on display.

## 2. Audience & framing

- **Primary public audience:** recruiters / interviewers (human), reading in
  English, spending 3–5 minutes. Entry point is `README.md`.
- **Secondary audience:** AI workers continuing the project — served by the
  internal-operational docs (`HANDOFF.md`, `AGENTS.md`, `CLAUDE.md`).
- **Framing goal:** present a *system-design PoC with an explicit decision
  basis, honest scope, and verification evidence* — not "a project with many
  features." The reader should leave understanding the problem, the design
  judgment, what works today, and what is deliberately deferred.

## 3. What to publish (inventory)

### 3.1 Public-facing showcase (bilingual EN + KO)
- [ ] `README.md` / `README.ko.md` — hub; makes the project understood and
      trusted in 3 minutes. Links out; does not duplicate facts.
- [ ] `docs/case_study.md` / `.ko.md` — the decision narrative (the heart).
      Organized by decisions, not by feature list.
- [ ] `docs/evaluation.md` / `.ko.md` — measured test + smoke evidence.
- [ ] `docs/decisions.md` / `.ko.md` — standalone decision vignettes (§7.1).

### 3.2 Reference (public, linked from the Documentation Map, light cleanup only)
- [ ] `docs/implementation_plan_assessment_harness_poc_v1.md` — canonical SoT.
- [ ] `docs/verifications/YYYY-MM-DD/*` — independent audit records (asset).
- [ ] `docs/daily_logs/YYYY-MM-DD/work_log.md` — contemporaneous decision trail.
- [ ] `CHANGELOG.md`, `schemas/`.

### 3.3 Internal-operational (public, but addressed to AI workers)
- [ ] `HANDOFF.md` — current-state snapshot.
- [ ] `AGENTS.md` / `CLAUDE.md` — agent working rules.

### 3.4 This plan
- [ ] `docs/publication_plan_v1.md` (+ `.ko` mirror — Open Decision §7).

## 4. How / sequencing (the work plan)

Each step is a small, self-contained commit with a `work_log` entry. Slice work
and presentation work stay in separate commits (established convention).

- [ ] **Step 0 — Truth pass (do first).** Make the current public surface
      *accurate* before making it pretty. README plan version v1.28 → v1.30;
      replace the linear "Phase 1/2/3 후" table with an **area-based status
      table** (the work did not proceed linearly — Phase 2 foundations exist
      while Phase 1 manual-run does not, so the linear table actively misleads);
      scan for any other overclaim.
- [ ] **Step 1 — Bilingual scaffold.** Create EN/KO file pairs and the
      language-switch header for the showcase docs *and* the technical docs
      (HANDOFF / AGENTS / CLAUDE; impl-plan per §7a). Embed the **Mermaid
      architecture diagram** in the README (replaces a separate arch doc).
- [ ] **Step 2 — Case study + decision vignettes (the heart).** Curate 3–5
      decisions from existing `work_log` Decisions + verification verdicts into
      the form **What / Why / Tradeoff / How verified / Where to confirm (link)**.
- [ ] **Step 3 — Evaluation (measured).** Build test/smoke tables **from real
      `docker compose run` output**, never transcribed. Every number recomputed.
- [ ] **Step 4 — AGENTS / CLAUDE augment.** Add agent workflow rules that are
      not already present; do not duplicate or contradict existing content.
- [ ] **Step 5 — Reference cleanup + safety scan.** Add `LICENSE` (Apache 2.0,
      §7.4); build a curated index for `daily_logs`/`verifications` (§7.7);
      secret/credential scan over working tree *and history* (repo is flipped
      as-is, so history is exposed); fix broken links; confirm no private data
      in fixtures.
- [ ] **Step 6 — Documentation Map.** Wire README to all docs with a clear
      "which door for which purpose" map.
- [ ] **Step 6.5 — Freeze + mirror all docs (§7b).** Once development and
      publication copy are frozen, produce the bilingual mirrors in one pass:
      full English mirror of the implementation plan, `.ko` mirror of this
      publication plan, `HANDOFF.md` mirror, README EN/KO flip, and the
      showcase/doc mirrors.
- [ ] **Step 7 — Visibility flip (Owner, manual).** Owner sets repo
      description/topics and flips `entangelk/assessment_poc` to public; this
      plan provides the ready-to-paste metadata.

## 5. Decision vignettes to feature (candidates, curate to 3–5)

- [ ] **`validated` over-claim → staged model → 3-way routing** (flagship). A
      contract defined `validated` as "all Rule 0 passed", but the classifier
      assigned it after only schema + attribution checks — a safety gap where a
      dangling-reference candidate could reach assessment. Caught by independent
      verification; resolved by staging the model (`structurally_validated`) and
      then splitting failure states with the principle *"split states only as
      far as downstream branches and as far as the name would otherwise lie."*
- [ ] **`ai_judgement` over-strict guard** — semantic-judgment quotes are not
      forced to be literal substrings; the boundary and its reason.
- [ ] **Union-based compacting, no auto-acceptance** — a values decision:
      disagreement between runs is preserved for review, never silently merged.
- [ ] **`check` vs `gate` boundary** — `check` never blocks externally; `gate`
      is the only external pass/fail verdict, behind mandatory human review.
- [ ] **Agent-consumable CLI stable core** — output contract designed for an AI
      caller, not a human.

## 6. Quality gates for the publication itself

Publication is blocked until all pass:
- [ ] Every claimed number (tests, counts, smoke statuses) recomputed from a
      real run within the same change.
- [ ] Implemented/pending status is consistent across README, HANDOFF, and plan.
- [ ] No broken internal links.
- [ ] Secret/credential scan clean (tree + history).
- [ ] Bilingual parity: EN and KO state the same facts.

## 7. Decisions resolved (kickoff Q&A, 2026-05-29 → v1.1)

1. **Decision record = standalone `docs/decisions.md`** (+ `.ko`). A section
   inside the case study would grow too long once vignettes accumulate.
2. **Bilingual extends to the technical docs too**, not only the showcase. Each
   doc carries the language-switch header; EN docs link to EN docs, KO to KO.
   (Exact scope for the large implementation plan: see §7a.)
3. **No separate `architecture.md`.** Instead embed a **Mermaid architecture
   diagram in the README** (draw.io-style visual) plus a link to the plan.
4. **License = Apache 2.0.** Permissive: free use/modification/distribution with
   notice + license retention and a patent grant; copyright owner = `entangelk`
   (Owner may swap to a legal name).
5. **Repo metadata + visibility flip = Owner does manually** (no `gh` in this
   environment). This plan hands Owner ready-to-paste description/topics.
6. **Demo vs. result artifact: deferred.** Keep a Demo/Results section reserved;
   decide later between a terminal cast and a static external-analysis result.
7. **`docs/daily_logs/` and `docs/verifications/` → curated index**, not fully
   raw in the public surface (too long). A short index links the notable ones.

## 7b. Bilingual timing principle (resolved v1.2)

Mirror **all docs only once, as the final pre-publication step**, after product
development and publication copy both freeze — translating a moving target
repeatedly is wasted work.

- **Mirror last:** implementation plan (full English mirror), this publication
  plan (`.ko` mirror), `HANDOFF.md`, README, case study, decisions,
  evaluation, audit index, AGENTS, and CLAUDE.
- **Delta checkpoint:** until mirroring begins, treat the 2026-06-01 work log as
  the baseline for publication-doc state. A later mirror pass should review
  document changes from that log forward instead of assuming any current
  showcase document is stable.

## 7a. Remaining Open Decisions

- [ ] Final repo description / topics wording (drafted for Owner to paste; Owner
      applies it manually together with the visibility flip — §7.5).

## 8. Definition of Done (= the publication moment)

- [ ] All §3 inventory items complete and cross-consistent.
- [ ] All §7 Open Decisions resolved.
- [ ] All §6 quality gates pass.
- [ ] Repository visibility flipped to public (§4 Step 7).

## 9. Change log

### v1.2 (2026-05-29)

Added the **bilingual timing principle** (§7b): docs are mirrored once at the
end after development and publication copy freeze, not translated repeatedly
against a moving target. The 2026-06-01 work log is the baseline for later
publication-doc delta review before mirroring. Resolves prior §7a items:
implementation plan gets a full English mirror deferred to the final step; this
plan's `.ko` mirror is also deferred. Added Step 6.5 (freeze + mirror). Only the
repo description/topics wording remains open (§7a).

### v1.1 (2026-05-29)

Resolved the kickoff Open Decisions (§7): standalone `decisions.md`; bilingual
extended to the technical docs; no `architecture.md` (a Mermaid diagram lives in
the README instead); Apache 2.0 license; repo metadata + visibility flip done
manually by Owner (no `gh` available); demo-vs-results deferred;
`daily_logs`/`verifications` surfaced through a curated index. Remaining open
items moved to §7a (implementation-plan bilingual scope, this plan's `.ko`
mirror, repo metadata wording).

### v1.0 (2026-05-29)

Initial publication plan. Owner decisions captured from kickoff Q&A:
- **Language:** English primary + Korean mirror as separate files, with a
  language-switch header on each.
- **Scope of "publish":** clean up the existing `entangelk/assessment_poc`
  repository and flip it to public (history retained and treated as part of the
  decision narrative; secret scan required).
- **This plan is public:** included as a portfolio artifact to show the
  publication reasoning itself.
Rationale baked into §1: foreground decisions/process over code, single source
of truth per fact, audit discipline shown as an asset, public/internal doc
roles separated, evaluation numbers must be measured not transcribed.
