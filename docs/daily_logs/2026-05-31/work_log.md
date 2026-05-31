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

## Publication Step 1 — Bilingual Scaffold + README Architecture Diagram (partial)

### Goals

- Begin publication_plan Step 1 without doing any translation (Owner: bilingual mirroring is batched at finalization, §7b/§6.5): set up the language-switch header scaffold on the English docs and embed the Mermaid architecture diagram in the README.

### Completed work

- Embedded a **Mermaid architecture diagram** in `README.md`, replacing the plain-text ASCII pipeline under `## 흐름 개요`.
  - The diagram marks the implemented/foundation boundary honestly (the prior ASCII flow did not): deterministic core (Rule 0 → Rules 1-3 + lint → findings) and the review/verdict flow (check → report → review → human → gate → verdict) are styled "implemented"; the agent extraction pipeline (AgentRunner ×N → candidates → compact → verify) is styled "foundation only". The solid arrow into Rule 0 is today's manual/fixture input path; the dashed arrow is the agent path "when built".
  - Everything anchors to the immutable source snapshot node.
- Added the language-switch header (EN/KO badges + `<!-- .ko mirror created on finalize -->` comment) to the English docs: `HANDOFF.md`, `AGENTS.md`, `CLAUDE.md`. `docs/decisions.md` already carried it.

### Issues found

- Problem: severe tool-output mangling this session led me to draft README edits against an **assumed English README** that does not exist — the live `README.md` is **Korean**. All three README edits failed (string-not-found), so `README.md` was undamaged; I then re-read the real file and redid the diagram against the actual Korean content.
  Cause: I issued edits in the same batch as the README read instead of confirming the read result first.
  Resolution: re-established ground truth with clean `git status` / `grep` before any further edit; only the verified diagram replacement and the AGENTS header were applied afterward.
  Outcome: no damage; lesson — never edit a file in the same batch as its first read this session.

### Decisions

- **README language-switch header deferred (not added yet).** `README.md` is currently Korean, but publication_plan §1.5 makes `README.md` the **English** canonical file (Korean → `README.ko.md`). Putting an "EN"-highlighted badge on a Korean file would be a false signal, so the README header waits until the finalization-time EN/KO split (§6.5) decides which content lands at which path. The English docs (HANDOFF/AGENTS/CLAUDE/decisions) get the header now because their EN badge is already accurate.
- The Mermaid diagram uses English technical-term node labels inside the Korean README — consistent with the README's existing inline-English-term style, and it carries over unchanged when `README.md` becomes the English canonical file.

### Next steps / open question for Owner

1. **README language at finalization:** confirm the plan — current Korean `README.md` content moves to `README.ko.md`, and a new English `README.md` is authored (per §1.5 EN-canonical). This is the one piece blocking the README language header; everything else in Step 1 for existing docs is done.
2. `docs/case_study.md` (Step 2) and `docs/evaluation.md` (Step 3) do not exist yet; they get the language-switch header when authored.
3. Proceed to Step 2 (case study, curating 3–5 decisions from the 11 in `decisions.md`).

### Verification

- `grep -c '```mermaid' README.md` = 1; `grep -c 'caller agent' README.md` = 0 (ASCII flow replaced).
- Language-switch header presence: README=0 (deferred), HANDOFF=1, AGENTS=1, CLAUDE=1, decisions=1.
- Docs-only; no code or test surface touched.

## Publication Step 2 — Case Study (`docs/case_study.md`)

### Goals

- Write the narrative case study (the "heart" per publication_plan §3.1) in English (canonical), curating 3–5 key decisions *from* `decisions.md` rather than re-deriving them.

### Completed work

- Authored `docs/case_study.md` (English) with the language-switch header and the structure: Problem / Goal (with scope honesty) / **5 curated key decisions** / What I built (today) / How it's verified / Limitations / What's next / an AI-collaboration footer.
  - The 5 featured decisions link back to `decisions.md`: §A1 (agent-as-user), §A2+§A4 (scope by rejection + lint pivot), §A3 (check never blocks), §B1 (the `validated` label that lied — flagged as flagship), §C1 (independent audit + withdrawn verdict). The case study gives each a 2–4 sentence curated version and links to the full vignette — no duplication of the decision record.
  - "What I built" mirrors the README implementation-status table honestly (implemented core/review flow vs foundation-only extract/compact/verify).
- Updated `HANDOFF.md` Step 2 line to "drafted".

### Decisions

- **Owner confirmation (2026-05-31): English is canonical, Korean is the full-parity mirror — even though the target market is domestic-centric.** The two language versions say the same facts; neither is written in more detail (publication_plan §1.5 + §6 bilingual-parity gate). This resolves the README "open question" from the Step 1 note: at finalization the Korean `README.md` content moves to `README.ko.md` and a new English `README.md` is authored. Rationale (Owner): main/canonical in English for reach and consistency with the already-English technical docs; Korean mirror serves the domestic audience without being a reduced version. So new showcase docs (case study, evaluation) are authored in English first.
- Case study links deliberately omit heading fragments (e.g. `decisions.md` not `decisions.md#a1-...`) to stay robust against vignette-title edits and satisfy the "no broken links" quality gate without fragile anchor matching.

### Next steps

1. Step 3 — `docs/evaluation.md` (English): test + smoke tables built from real `docker compose run` / `pytest` output (recompute the 200-pass count and the smoke envelope numbers; never transcribe).
2. Step 4 — AGENTS/CLAUDE augment; Step 5 — LICENSE (Apache 2.0) + curated index + secret scan; Step 6 — Documentation Map in README.
3. Step 6.5 (finalization) — bilingual mirrors in one pass, including the README EN/KO flip.

### Verification

- Case study internal link targets exist: `docs/decisions.md`, `README.md` (`../README.md`), `docs/verifications/`, `docs/implementation_plan_assessment_harness_poc_v1.md` — all present; links use no fragments.
- `grep -c 'Switch language' docs/case_study.md` = 1.
- Docs-only; no code or test surface touched.

## Publication Step 3 — Evaluation (`docs/evaluation.md`), measured

### Goals

- Build the measured test + smoke evidence doc from a **real run** (publication_plan §6: recompute, never transcribe), and — per Owner — frame the numbers as a dated, moving snapshot since the project is under active development.

### Completed work

- Ran the suite and fixture smokes live, then authored `docs/evaluation.md` (English) from the captured output:
  - **Test suite:** `200 passed`; per-module from `--collect-only`: rules 95 / cli-output-contract 48 / agent-runner-contract 27 / models 22 / fixtures 8.
  - **`check` smoke table** for all six grounded fixtures (each with its own `policy.yaml` + `source_manifest.yaml`): measured `(high, medium, informational)`, `review_queue_count`, and a separate deduplicated `next_actions` table.
  - **Input-guard table** with the *verified* order (see Issues).
  - **Reproduction** section: canonical Docker commands + the direct `PYTHONPATH=src python3 -m pytest` form + a single-fixture smoke template.
- Banner frames the figures as a 2026-05-31 snapshot that moves; "treat shapes/behaviors as the stable claim, counts as true-on-the-date."

### Issues found

- Problem: I nearly recorded the input-guard order as "policy validated before manifest" — which is **wrong**.
  Cause: an early no-manifest smoke (run while the sandbox shell was mangling output and one of my debug one-liners piped stderr into a JSON parser) produced an unreliable reading.
  Resolution: re-ran all three guard cases cleanly and read the source. Confirmed `_cmd_check` checks `--source-manifest` first (cli.py:102) then `--policy` (cli.py:104): manifest-omitted → `provide_source_manifest`; manifest-present/policy-omitted → `provide_policy`; both-omitted → `provide_source_manifest`. Only the verified order went into the doc.
  Outcome: reinforced the session rule — re-verify any measurement taken while the environment is degraded, and read the code rather than trusting a single CLI reading, before recording it. (This wrong ordering never reached a committed file; the earlier Step-3 edits were cancelled mid-batch.)
- Note: an earlier draft mentioned `200 passed in 7.16s`; dropped the wall-clock time from the doc since it is the least stable number and adds no signal on a "moving snapshot."

### Verification

- Measured live this session (clean shell): six-fixture smoke counts — clean `(0,2,0)` q0, orphan `(1,1,1)` q0, uncovered `(1,5,0)` q1, optionality `(2,1,0)` q0, bonus_misuse `(1,5,1)` q2, reference_integrity `invalid_input` exit 2 `high_integrity_count=9`. `next_actions` per fixture captured from the live envelopes (not from memory).
- Input guards re-verified clean: `provide_source_manifest` / `provide_policy` / both-omitted→`provide_source_manifest`, cross-checked against cli.py:102-105.
- `evaluation.md` internal links: `verifications/` and `decisions.md` exist; `#reproduction` is its own H2.
- Docs-only; no code or test surface modified (smokes wrote only to `/tmp` and `work/`).

### Next steps

1. Step 4 — augment `AGENTS.md` / `CLAUDE.md` with any agent workflow rules not already present (no duplication).
2. Step 5 — `LICENSE` (Apache 2.0, `entangelk`); curated index for `daily_logs`/`verifications`; secret scan over tree + history.
3. Step 6 — Documentation Map in README; Step 6.5 — bilingual mirrors in one pass incl. README EN/KO flip.
