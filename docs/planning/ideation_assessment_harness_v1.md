<!-- .ko mirror created on finalize (publication_plan §7b) -->

<p align="center">
  <a href="./ideation_assessment_harness_v1.md"><img src="https://img.shields.io/badge/Language-EN-111111?style=for-the-badge" alt="English"></a>
  <a href="./ideation_assessment_harness_v1.ko.md"><img src="https://img.shields.io/badge/Language-KO-6B7280?style=for-the-badge" alt="한국어"></a>
</p>
<p align="center"><sub>Switch language / 언어 전환</sub></p>

# Ideation — Hiring Assignment Assessment Harness

> Written: 2026-05-22 / Ideation that emerged after completing one round in this repo and closely reading the evaluation material
> Nature: unfinished thinking. Not a concrete system specification, but a collection of questions around "could this direction work?"

## 0. Motivation

After completing one round and closely reading the retrospective material shared by the company (`dfinite_applicant_share_v1/00_FINAL_REPORT.md`), I came away with the impression that several **systemic weaknesses repeat as patterns** inside the assessment process. These did not look like individual evaluator mistakes; they looked like **gaps in the infrastructure that operates the assessment itself**.

These weaknesses read as a sign that, although the hiring side has adopted AI tools, scoring, review, and statistical operations still run loosely through people and documents. Just as a "test harness" is a safety net for code changes, the hypothesis is that **a similar kind of harness for hiring assessments** could be valuable.

This document is a thinking note that unfolds that hypothesis.

---

## 1. Observed Problem Categories

Cases directly observed in this round (patterns that can be generalized regardless of company or round).

### A. Information Asymmetry — Distance Between README and Actual Evaluation

- README recommended time (10-18h) vs. work depth implied by the retrospective material (26 unique attempt list, distribution peak at 2-5 days)
- Phases marked as "optional" functioning in practice as decisive differentiation signals
- Evaluation criteria (B7 self-discovery, D6 refund-policy conflict) not explicitly stated in the README spec

Candidates prioritize based on the README, but evaluation happens against criteria outside it. With the same time investment, the outcome becomes close to luck over who knew what.

### B. Statistical Methodology — Visualization and Interpretation When N Is Small

- Whether visualization/normalization expressions have a natural meaning when candidate N is small (estimated 13-20 people in one round)
- Expressions such as splines, box plots, and normalization are stable to interpret only above a certain N. With small N, the representation choice itself shapes the impression of the result.

### C. Post-hoc Addition of Evaluation Criteria

- Items absent from the README carry weight in post-hoc evaluation (self-discovery items such as B7 and D6)
- From the candidate's perspective, this means being evaluated against criteria that were not announced in advance

### D. IP / Source Handling — Externalizing Cookbooks

- One candidate's accumulated working method (CookBook) was anonymously exposed in the evaluation material as a list of "external top-cluster decisive signals"
- It was externalized without a prior consent-sharing procedure

### E. Selection Bias in Evaluation Axes

- If areas that can occur whenever a candidate chooses to pursue them, such as "library bug discovery / workaround," are treated as decisive signals, the assessment becomes driven by luck and discretion more than skill
- There was no review of whether the evaluation axis itself is game-theoretically stable

---

## 2. Hypothesis

Move the concept of a "test harness" into hiring assessment — **infrastructure that applies a fixed rubric consistently and guarantees coherence, reproducibility, and transparency at the system level**.

Three core questions:

1. **Pre-assessment coherence** — Does the README map 1:1 to the rubric?
2. **Assessment-time reproducibility** — Does the same input produce the same score?
3. **Post-assessment transparency** — Can candidates debug their own results?

If all three axes are satisfied, many of the problem categories in §1 should resolve naturally.

---

## 3. Layers the Harness Should Cover

This is a theoretical partition. A real system may still be valuable even if it implements only part of it. Layers 0-5 are baseline required areas; Layer 6+ is an optional area introduced once scale grows.

### Layer 0: Dual SoT (Foundational)

All consistency in the assessment system rests on the premise that **two Sources of Truth are separated and cross-validated**.

- **Spec SoT** — the truth exposed to candidates (README, BR, PRD, data_model)
- **Rubric SoT** — the truth used by evaluators (scoring criteria, weight matrix, evaluator instructions)
- **Invariant**: every item in the Rubric SoT must trace to the Spec SoT. Orphan rubric items (evaluation criteria absent from the spec) are automatically blocked.
- **Versioning**: both SoTs are managed together with semver. When the rubric changes, spec coverage is automatically revalidated.

If this layer is enforced, many cases of post-hoc criterion addition (§1.C) and information asymmetry (§1.A) become **structurally impossible**, because they are automatically detected as orphan rubric items.

Feature example: every PR that changes rubric YAML runs spec coverage validation in CI. If mapping fails, the PR merge is blocked.

### Layer 1: Pre-flight Coherence Check

A validation layer that runs on top of Layer 0.

- Check 1:1 mapping between README and rubric items (regular execution of the Layer 0 invariant)
- Pre-disclose evaluation axes (including self-discovery and out-of-spec areas)
- Check coherence between recommended time and rubric depth (for example, number of rubric items x average work time <= recommended time)
- Make the actual weight of "optional" items such as a chatbot explicit

Feature example: before a round begins, feed Spec SoT + Rubric SoT into the system and automatically report missing mappings, weight contradictions, time-budget violations, and similar issues.

### Layer 2: Scoring Reproducibility

- Machine-checkable items are automatically scored through LLM / regex / AST-based checks
- AI scoring results always include a human override loop
- Measure multi-evaluator consensus (κ statistic, etc.)
- Attach an audit trail to evaluation results (which rubric version, which evaluator, which AI output was relied on)

Feature example: applicant submission + rubric input -> JSON score sheet output, with evidence (file:line) attached for each item.

### Layer 3: Statistical Validity

- Automatically choose visualizations appropriate for candidate N (individual dots for N<10, box plot + dots for N<30, distribution curve for N>=30)
- Require confidence intervals
- Bias detection — anchor effect (earlier candidates' scores influencing later candidates), halo effect, selection bias

Feature example: score dataset + visualization request -> output only valid visualizations; reject invalid visualizations with a warning.

### Layer 4: Post-test Disclosure

- Candidate feedback channels (anonymous and identified)
- Standard for post-assessment disclosure of evaluation axes (which item had which weight)
- Source-attribution procedure for externally shared material — if a particular candidate asset became an anchor, obtain prior consent or generalize it

Feature example: score breakdown, partial audit trail, and feedback form automatically sent to candidates after assessment closes.

### Layer 5: Cross-round Learning

- Rubric versioning (semver) — synchronized with Layer 0 SoT versioning
- Candidate feedback -> rubric improvement PR
- Compare score distributions across rounds (measure drift caused by rubric changes)

Feature example: rubric repo + change log + retrospective PR template after every round.

### Layer 6: Large-scale Processing + Pattern Provenance (Optional, Scale-gated)

An optional layer to consider once candidate N reaches company scale (50+ candidates per round, 100+ files per candidate, accumulated 1000+ candidates across rounds). **For small rounds (N<=30), the operating cost is larger than the value.**

- **VectorDB** — store code/doc embeddings and index semantic search
- **Cross-applicant Pattern Miner** — embedding clusters + attribution. A "unique attempt list" like §4.9 is extracted automatically rather than curated by humans
- **Pattern Provenance** — track the first candidate in whom a given pattern appeared. Automatically address the IP/cookbook issue (§1.D)
- **Outlier Detection** — automatically detect semantically different approaches and route them to the human review queue. Mitigates selection bias (§1.E)
- **RAG-augmented LLM Grader** — when grading a candidate's code, the LLM grader references similar patterns from other candidates as context. Enables more comparative evaluation

#### Adoption Caution — Embedding Model Dependency Vulnerability

VectorDB-based features **directly depend on the performance and characteristics of the embedding model**, which introduces new vulnerabilities in the harness's own reproducibility and evaluation consistency.

| Vulnerability | Cause | Impact |
|---|---|---|
| **Cluster-result drift when the model changes** | Model A and Model B have different embedding spaces | The same candidate's "X% similarity" changes depending on the model |
| **Retroactive changes in pattern provenance** | Applying a new model can change recomputed attribution results for past rounds | The truth value of "candidate X found this pattern first" becomes unstable |
| **Increase in harness parameters** | Many model-specific parameters appear, such as cluster threshold, similarity cutoff, and outlier z-score | Operators inherit responsibility for "which threshold is correct." Variables outside the rubric begin affecting scoring |
| **Limits of domain-specific models** | Code-domain embeddings (CodeBERT, GraphCodeBERT, etc.) have different strengths and weaknesses from general text models | Model choice itself becomes a source of evaluation bias |

Mitigations:

- Pin the embedding model version and forbid changes until the round closes (same principle as Layer 0 SoT versioning)
- When replacing the model, run regression validation on baseline round data (Model A scoring ~= Model B scoring within tolerance)
- Treat VectorDB similarity as **one signal, not a single truth value**. Final evaluation always combines Layer 2 deterministic checks + LLM grader + human override
- Include model-dependent parameters (threshold, cutoff) in the SoT and store them with the audit log

---

## 4. Conceptual Architecture Sketch

```
┌─────────────────────────────────────────────────────────┐
│  Layer 0: 2중 SoT (Foundational)                        │
│  ┌──────────────────┐    ┌──────────────────────┐       │
│  │  Spec SoT        │◄──►│  Rubric SoT          │       │
│  │  README+BR+PRD   │    │  scoring+weights     │       │
│  │  +data_model     │    │  +evaluator instr.   │       │
│  └────────┬─────────┘    └──────────┬───────────┘       │
│           │  Invariant: rubric ⊆ spec                   │
│           └──────────────┬───────────┘                  │
│                          │ (CI cross-validates)         │
└──────────────────────────┼──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 2-5: Core Pipeline                               │
│                                                         │
│  [Applicant Repo Ingestion]                             │
│        │                                                │
│        ├── AST/static analyzer                          │
│        ├── Document chunker                             │
│        └── (optional → Layer 6 embedding)               │
│        │                                                │
│        ▼                                                │
│  [Evaluator Pipeline]                                   │
│    ├── Static checker (deterministic)                   │
│    ├── LLM grader (rubric prompt)                       │
│    ├── Human reviewer (override)                        │
│    └── Audit log writer                                 │
│        │                                                │
│        ▼                                                │
│  [Aggregator]                                           │
│        │                                                │
│        ├── Statistical Validator (Layer 3)              │
│        ├── Disclosure Layer (Layer 4)                   │
│        └── Round Retro Loop (Layer 5)                   │
└─────────────────────────────────────────────────────────┘

   ↓ (scale-gated, when N≥30 ~ 50 per round)

┌─────────────────────────────────────────────────────────┐
│  Layer 6: 대용량 + Pattern Provenance (Optional)        │
│                                                         │
│  [Embedding Generator]                                  │
│        │ (model version pinned in Layer 0 SoT)          │
│        ▼                                                │
│  [VectorDB]                                             │
│        │                                                │
│        ├── Cross-applicant Pattern Miner                │
│        ├── Pattern Provenance Tracker                   │
│        ├── Outlier Detector → Human Review Queue        │
│        └── RAG context for LLM Grader                   │
│                                                         │
│  ⚠ Vulnerability: embedding model 의존성 (§3 Layer 6)   │
└─────────────────────────────────────────────────────────┘
```

Each component can be adopted independently.

- **Smallest start**: Layer 0 only — dual SoT separation + invariant CI validation. This alone resolves about 80% of §1.A and §1.C.
- **Next step**: Layers 2-5 — LLM grader + statistical validator + disclosure + round retrospective
- **At scale**: Layer 6 — VectorDB and pattern provenance. However, it must be introduced together with the embedding-model dependency mitigations (§3 Layer 6 ending).

---

## 5. Phased Adoption Possibility

| Phase | Adoption target | Estimated cost | Problem categories addressed | Scale gate |
|---|---|---|---|---|
| Phase 0 | Dual SoT separation + invariant CI validation | Low (Spec/Rubric YAML + mapping validation script) | §1.A information asymmetry, §1.C post-hoc criterion addition | — |
| Phase 1 | Pre-flight validation (time budget, weight contradictions, etc.) | Low | §1.A | — |
| Phase 2 | LLM-assisted scoring + human override | Medium (LLM prompt design + UI) | §1.E selection bias | — |
| Phase 3 | Statistical validator | Low (N-based visualization library) | §1.B statistical methodology | — |
| Phase 4 | Disclosure standard | Medium (candidate report template + feedback channel) | §1.D IP, §1.A information asymmetry | — |
| Phase 5 | Cross-round learning loop | High (requires organizational process change) | All | — |
| **Phase 6** | **VectorDB + Pattern Miner + RAG grader** (optional) | **High (infrastructure + embedding-model operation + parameter audit)** | **§1.D pattern-provenance automation, §1.E automatic outlier detection** | **Consider when N≥30~50 / accumulated company total reaches 1000+ candidates** |

Even adopting only **Phase 0+3** appears likely to resolve many of the weaknesses observed in this round. Phase 6 becomes cost-justifiable only after reaching scale.

---

## 6. Expected Effects (Direction)

- **Candidate side**: clear criteria, reasonable time allocation, post-assessment learning value
- **Evaluator side**: consistency, reproducibility, audit trail, fuel for cross-round improvement
- **Company side**: improved hiring quality, external reputation, reduced legal risk (blocking issues such as post-hoc criterion addition)
- **AI-tool side**: traceable hallucinations from scoring assistants, a clear complementary role for human evaluators

---

## 7. Limitations and Unknowns

- **Limits of automating qualitative assessment** — areas such as code quality and documentation depth are limited even with LLM scoring. Full automation is unrealistic
- **Value of human evaluator intuition** — whether fully algorithmic assessment is always fairer is a separate question. How far to mix intuition + algorithms is a design question
- **Intrinsic statistical limits in small-N environments** — even a harness cannot reduce statistical noise at N=15. It may be more honest to reduce statistical display itself
- **Embedding model dependency (when introducing Phase 6)** — the VectorDB layer directly depends on model performance and introduces new vulnerabilities such as cluster/provenance result drift when models change, increased operator-owned parameters (threshold, cutoff), and domain-specific model bias. It must be introduced together with the mitigations at the end of §3 Layer 6 (model version pinning, regression validation, treating it as one signal)
- **IP/cookbook handling** — requires Legal / HR collaboration. Cannot be solved by technology alone
- **Organizational culture** — the Phase 5 cross-round learning loop assumes a culture that accepts feedback among people

---

## 8. Next Steps (Optional)

If this ideation should be made more concrete:

- **Phase 1 PoC** — a sample assignment + rubric YAML + mapping-check script would take 1-2 days. Possible as a personal side project
- **External literature** — `Talent Analytics`, academic material on `Work Sample Tests`, `Hiring Plan` (Lou Adler), Google `re:Work` hiring material
- **Similar-tool survey** — investigate which of the five layers existing hiring platforms such as Codility / HackerRank / Coderbyte cover, and which they leave empty

Keep this as a thinking asset that can be used in a future hiring round or if another company requests consulting on its hiring assessment system.

---

## 9. Note

This document is at the ideation stage and may be updated in a later cycle. The core hypothesis is **"assessment methodology should also have verifiable infrastructure, like code"** — if that hypothesis is right, the smallest unit among the five layers above is worth trying first.
