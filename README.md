# Assessment Spec Harness PoC

> CI for hiring assessments — 채용 과제의 공개 명세(spec)와 비공개 평가 rubric 사이의 불일치를 사전에 검출하는 하네스.

본 도구는 응시자를 평가하지 않는다. **평가 설계 자체를 평가한다.**

---

## 1차 사용자: AI 에이전트

본 도구의 1차 호출 주체는 Claude Code, Codex, Gemini 같은 AI 에이전트다. CLI 계약, 종료 코드, 출력 형식은 모두 agent-consumable하게 설계되었다. 사람은 최종 검토자로만 참여한다.

사람이 직접 CLI를 호출해도 동작한다 (보조 사용 경로).

---

## 빠른 시작

### 0. 설치 (PoC 단계: 로컬 개발)

```bash
git clone <repo>
cd assessment_poc
pip install -e .
```

### 1. 현재 contract 확인 (caller agent 첫 단계 권장)

```bash
assessment-harness schema --command check --output json
```

매번 schema introspection으로 stable core / informational / exit codes / next_actions types를 확인하라. 문서를 따라잡지 않아도 안전한 통합이 가능하다.

### 2. 결정론적 검증만 (Phase 0)

수동으로 작성한 compacted YAML을 입력으로 Rule 0~3 검사.

```bash
assessment-harness check \
  --spec-items fixtures/clean_assignment/spec_items.yaml \
  --rubric-items fixtures/clean_assignment/rubric_items.yaml \
  --trace-links fixtures/clean_assignment/trace_links.yaml \
  --source-manifest fixtures/clean_assignment/source_manifest.yaml \
  --policy config/policy.yaml \
  --out findings.json \
  --diagnostics-out integrity_diagnostics.json \
  --review-queue-out review_queue.json

assessment-harness report \
  --findings findings.json \
  --diagnostics integrity_diagnostics.json \
  --out report.md
```

`--source-manifest`는 Phase 0 `check`의 필수 인자다 (plan §5.0 / §5.1 / §11). 누락하면 `status=invalid_input`, exit `2`, 진단 `source_manifest_required`, next_action `provide_source_manifest`가 반환된다.

`--policy`도 필수다. `rules.optionality_mismatch.weight_threshold`가 없으면 Rule 3 경계를 조용히 건너뛰지 않고 `status=invalid_input`, exit `2`로 복구 지시를 반환한다.

Phase 0에서 semantic verification 입력이 없으면 `ai_judgement` link는 의미 확인 대기 상태로 남는다. Agent 실행 흐름에서는 아래 `verify` 산출물을 후속 명령에 전달한다.

Rule L1/L6 lint safeguard는 Phase 0 `check`에서도 `review_queue.json`에 기록된다.
`--review-queue-out`을 생략하면 `--out` 옆에 생성되며, Rule 0 clean 실행에서
finding이 없으면 빈 queue로 갱신되어 이전 검토 항목이 남지 않는다.
Phase 0 `check` 출력은 lint safeguard 전용이다. Phase 2 `compact`는
`--review-queue-in`으로 기존 queue를 보존하고 invalid run 항목을 추가할 수
있다. Phase 2 `verify`도 `--review-queue-in`으로 기존 queue를 보존하고
`ai_judgement_pending` 항목을 중복 없이 추가한다. `check`
`--review-queue-out`은 여전히 lint safeguard 단독 출력이므로 기존 통합 queue
경로에 직접 쓰지 않는다.

최종 검토가 `final_review.yaml`에 기록된 뒤에는 `gate`가 외부 판정을 낸다.
final review의 finding decision은 `type` + 생성 식별자(`rubric_id`,
`spec_id`, paired rubric IDs)만으로 finding을 가리키며, `message`나
`evidence` payload를 복사하지 않는다.

```bash
assessment-harness gate \
  --final-review final_review.yaml \
  --output json
```

### 3. 에이전트 실행 포함 전체 흐름 (Phase 2/3, 일부 구현)

> ⚠️ 아래 전체 흐름 중 `extract` / `compact` / `verify` CLI는 초기
> `mock_fixture` 경로만 구현되었다. 실제 SDK runner는 아직 미구현이다. 현재
> `extract`는 fixture를 재생해 run별 `candidates.yaml`과 raw/audit trace를
> 만들고, `compact`는 `--runs-dir` 아래 run별 `candidates.yaml`을 읽거나
> 저수준 입력으로 `--candidates` 파일 목록을 받아 canonical YAML을 생성한다.
> `verify`는 compacted trace link의 `ai_judgement` evidence를 별도
> `semantic_verifications.yaml` 및 review queue 항목으로 기록하지만,
> compacted link를 수정하거나 의미 판정을 확정하지 않는다. `id_map.yaml`이
> 있으면 trace link canonical ID는 파일 순서가 아니라 id_map lineage에서
> 가져온다. `check`는 이 제안을 원본 link에 쓰지 않고 in-memory effective
> `semantic_status`로만 반영한다. compacted lineage가 있는 trace에
> `--semantic-verifications`를 줄 때는 `--id-map`도 함께 전달해야 하며,
> 그래야 `check`가 `verify`와 같은 lineage 기준으로 제안을 적용한다.

```bash
# 복수 독립 실행
assessment-harness extract \
  --spec fixtures/clean_assignment/source/spec.md \
  --rubric fixtures/clean_assignment/source/rubric.md \
  --runner mock_fixture \
  --fixture-dir fixtures/clean_assignment \
  --runs 3 \
  --out-dir work/runs

# compacting (자동 채택 없음, support/identity_basis/variants 보존)
assessment-harness compact \
  --runs-dir work/runs \
  --policy config/policy.yaml \
  --out-dir work/compacted

# 의미 검증 agent 복수 실행 (원문/link read-only, 제안 별도 저장)
assessment-harness verify \
  --compacted-dir work/compacted \
  --source-manifest work/source_snapshot/manifest.yaml \
  --runner mock_fixture \
  --runs 3 \
  --policy config/policy.yaml \
  --out-dir work/semantic_verification

# 결정론적 검사 (provisional findings 생성)
assessment-harness check \
  --spec-items work/compacted/spec_items.yaml \
  --rubric-items work/compacted/rubric_items.yaml \
  --trace-links work/compacted/trace_links.yaml \
  --source-manifest work/source_snapshot/manifest.yaml \
  --semantic-verifications work/semantic_verification/semantic_verifications.yaml \
  --id-map work/compacted/id_map.yaml \
  --policy config/policy.yaml \
  --out work/findings.json \
  --diagnostics-out work/integrity_diagnostics.json

# 사람용 report
assessment-harness report \
  --findings work/findings.json \
  --diagnostics work/integrity_diagnostics.json \
  --semantic-verifications work/semantic_verification/semantic_verifications.yaml \
  --review-queue work/compacted/review_queue.json \
  --out work/report.md

# 브라우저로 확인할 수 있는 HTML report
assessment-harness report \
  --findings work/findings.json \
  --diagnostics work/integrity_diagnostics.json \
  --semantic-verifications work/semantic_verification/semantic_verifications.yaml \
  --review-queue work/compacted/review_queue.json \
  --format html \
  --out work/report.html

# 최종 human review 기록
assessment-harness review \
  --compacted-dir work/compacted \
  --findings work/findings.json \
  --diagnostics work/integrity_diagnostics.json \
  --semantic-verifications work/semantic_verification/semantic_verifications.yaml \
  --review-queue work/compacted/review_queue.json \
  --report work/report.md \
  --reviewer kdt \
  --out-dir work/final_review

# 최종 review 이후 외부 판정
assessment-harness gate \
  --final-review work/final_review/review.yaml \
  --output json
```

---

## 흐름 개요 (아키텍처)

전체 파이프라인은 **불변 소스 스냅샷**(sha256 + line/span `source_ref`)에 anchor된다.
결정론적 검증 코어와 review/verdict 흐름은 **구현 완료**, 이를 먹이는 multi-run
에이전트 추출 파이프라인은 **contract/foundation 단계**다. 아래 다이어그램은 그
경계를 그대로 표기한다 — Rule 0로 들어가는 실선은 *현재* 입력 경로(수동/fixture),
점선은 *구현 시* 에이전트 경로다.

```mermaid
flowchart TB
    SNAP["Immutable source snapshot<br/>(sha256 + line/span source_ref)"]

    subgraph EXTRACT["Agent extraction (mock initial / SDK pending)"]
        direction LR
        RUNS["AgentRunner x N<br/>framework-agnostic"] --> CANDS["candidates<br/>+ raw/audit trace"] --> COMPACT["compact<br/>union, no auto-merge"] --> VERIFY["verify<br/>semantic, multi-run"]
    end

    subgraph CORE["Deterministic validation core (implemented)"]
        direction LR
        R0["Rule 0<br/>reference integrity"] --> RJ["Rules 1-3<br/>+ lint L1/L5/L6"] --> FINDINGS["provisional findings"]
    end

    subgraph FLOW["Review and verdict (implemented)"]
        direction LR
        CHECK["check"] --> REPORT["report"] --> REVIEW["review<br/>hold draft"] --> HUMAN(["human final review<br/>accept / hold / rerun / override"]) --> GATE["gate"] --> VERDICT{{"pass / fail / pending"}}
    end

    SNAP --> RUNS
    SNAP -->|"manual / fixture inputs today"| R0
    VERIFY -.->|"compacted + verified artifacts (mock initial)"| R0
    FINDINGS --> CHECK

    classDef done fill:#e6ffed,stroke:#22863a,color:#111827;
    classDef todo fill:#fff5e6,stroke:#b08800,color:#111827,stroke-dasharray:5 3;
    class R0,RJ,FINDINGS,CHECK,REPORT,REVIEW,HUMAN,GATE,VERDICT done;
    class RUNS,CANDS,COMPACT,VERIFY todo;
```

---

## 핵심 데이터 계약

자세한 schema는 [구현 계획서 §5](docs/planning/implementation_plan_assessment_harness_poc_v1.md#5-데이터-계약) 참고. 요약:

- **spec_items / rubric_items / trace_links**: compacted artifacts. `support` (어느 run에서 발견), `identity_basis` (동일성 판단 기준), `variants` (미세 차이 보존)
- **candidate artifacts**: run별 pre-compacting 후보. `classify_candidate_run_integrity`는 schema/audit trace attribution만 확인해 `structurally_validated`로 표시하고, `classify_deep_candidate_run_integrity`가 내부 reference, source grounding, token quote mismatch를 구분해 통과한 run만 `validated`로 승격한다.
- **source_manifest / source_ref**: immutable input snapshot hash와 line/span anchor. DB/RAG 없이도 원문 grounding 검증
- **id_map**: run-local ID를 compacted canonical ID로 remap한 provenance. 후속 프로젝트/버전 관리 확장 지점
- **trace_links.evidence_quotes**: `verification_mode` 별 분기
  - `token_sequence`: strict substring 매칭 (정량 marker 검증)
  - `ai_judgement` (default): reference integrity만, 의미는 read-only verifier-agent 제안과 최종 human review로 확인
- **semantic_verifications.yaml**: verifier-agent 복수 run의 `supported` / `rejected` / `uncertain` 제안 취합. compacted link는 수정하지 않으며, `check`는 이를 Rule 1 evidence의 effective status로만 사용. compacted lineage가 있는 trace에 `--semantic-verifications`를 줄 때는 `--id-map`도 함께 전달해야 하며, trace 순서가 아니라 canonical lineage로 proposal을 조인
- **verify mock path**: `ai_judgement` evidence는 보수적으로 `agent_uncertain` proposal을 남긴다. quote-level `source_ref`가 없으면 `source_refs: []`로 불확실성을 드러내고 review queue에도 남긴다
- **integrity_diagnostics.json**: Rule 0 위반 기록
- **review_queue.json**: 기존 검토 entry 5종과 lint safeguard `double_scoring_review` / `mandatory_spec_bonus_review`. Phase 0에서는 Rule L1/L6가 각각 paired queue entry를 생성하며, Rule L5는 finding/action만 생성
- **findings.json**: Rule 1~3 위반 (Rule 0는 별도 diagnostic)
- **final_review/**: 최종 검토자의 accept/hold/rerun/override 기록. `review` 명령은 `status=success`/`provisional_findings`인 findings만 받아 모든 finding을 `hold`로 둔 draft `review.yaml`을 만들고, 사람이 이를 수정해 최종 결정으로 닫음. 기존 draft는 기본적으로 덮어쓰지 않으며, 의도적 재생성은 `--force`를 사용. Finding decision은 최소 `target_key`로 `findings.json` 항목을 닫음
- **gate output**: final review 이후 외부 호출자가 소비하는 pass/fail/pending 판정. confirmed blocking finding이 있을 때만 exit `1`

---

## 정책 파일

모든 정책은 `config/policy.yaml` 하나로 통합. Phase 0 `check`에는 최소한
`rules.optionality_mismatch.weight_threshold`가 필요하다.

```yaml
rules:
  optionality_mismatch:
    weight_threshold: 10
compacting:
  identity_basis:
    spec_item: "source+section+normalized_text"
    rubric_item: "title+normalized_description"
    trace_link: "rubric_id+sorted(spec_ids)"
runs:
  min_valid_runs: 2
  default_runs: 3
  max_runs: 7
verification:
  default_mode: ai_judgement
```

CLI는 `--policy config/policy.yaml` 하나로 모든 정책을 받는다.

---

## CLI 출력 계약 (agent-consumable)

모든 명령은 `--output json` flag로 machine-readable 출력 지원.

### 종료 코드

| Code | 의미 |
|---|---|
| 0 | success/provisional/pending; final blocking verdict 없음 |
| 1 | `gate`에서 confirmed blocking finding 존재 |
| 2 | input/integrity 오류 (Rule 0 violation 포함) |
| 3 | internal 오류 (runner 실패 등) |

### Stable Core (모든 명령 필수)

- `status`: `success` / `provisional_findings` / `pending_review` / `fail` / `invalid_input` / `internal_error`
- `exit_code`: 0/1/2/3
- `command`: 실행된 명령 이름
- `next_actions`: caller agent용 hint 배열 (없으면 빈 배열)

그 외 필드는 informational이며 사전 통지 없이 변경 가능. caller agent는 **항상 `schema` 명령으로 현재 contract 확인** 권장.

---

## 구현 상태

| 영역 | 상태 |
|---|---|
| Phase 0 결정론적 검증 코어 (Rule 0~3 + lint L1/L5/L6, fixture 회귀) | 완료 |
| review / gate finding-level 흐름 | 초기 구현 완료 |
| AgentRunner protocol | 기반 완료 |
| Candidate artifact schema | 기반 완료 |
| Candidate audit-trace attribution | 기반 완료 |
| Runner artifact normalization | 기반 완료 |
| Candidate integrity 분류 (structural + staged model) | 기반 완료 |
| Deep candidate Rule 0 검증 헬퍼 (3-way 격리) | 기반 완료 |
| `extract` CLI 오케스트레이션 (`mock_fixture`) | 초기 구현 완료 |
| `compact` CLI 오케스트레이션 | 초기 구현 완료 |
| `verify` 오케스트레이션 (`mock_fixture`) | 초기 구현 완료 |
| `materialize-review` CLI 오케스트레이션 | 초기 구현 완료 |
| 실제 SDK runner | 미구현 |
| 전체 Phase 2/3 E2E 워크플로 | 미구현 |

> 진행은 선형 단계가 아니었다. Phase 2 기반(runner·candidate 계열)이 먼저 들어왔고,
> 실제 과제 manual run과 전체 E2E는 아직이다. 그래서 단계 번호 대신 영역별 상태로 표기한다.

상세 진입 조건/완료 기준: [구현 계획서 §9, §12](docs/planning/implementation_plan_assessment_harness_poc_v1.md#9-단계별-구현-계획)

---

## 문서 지도 (Documentation Map)

어떤 목적엔 어느 문서를 보면 되는지 정리한 지도다.

**이 프로젝트를 이해하고 싶다면 (3~5분)**

| 문서 | 역할 |
|---|---|
| [docs/case_study.md](docs/case_study.md) | **여기서 시작** — 문제 / 목표 / 핵심 결정 / 무엇을 만들었나 / 검증 / 한계의 서사 |
| [docs/decisions.md](docs/decisions.md) | 왜 이렇게 설계했는가 — 동시대 출처를 인용한 결정 vignette 모음 |
| [docs/evaluation.md](docs/evaluation.md) | 측정된 테스트·smoke 근거 (날짜 박힌 moving snapshot) |
| [docs/audit_index.md](docs/audit_index.md) | 작업 일지 + 독립 검증 기록 큐레이션 인덱스 |

**명세와 설계 (정본)**

| 문서 | 역할 |
|---|---|
| [docs/planning/implementation_plan_assessment_harness_poc_v1.md](docs/planning/implementation_plan_assessment_harness_poc_v1.md) | **구현 명세 (1순위 SoT)** — 현재 v1.32 |
| [docs/planning/ideation_assessment_harness_v2.2.md](docs/planning/ideation_assessment_harness_v2.2.md) | Rubric Lint Rules 가족 (2순위, 2026-05-27 final + in-place 개정) |
| [docs/planning/ideation_assessment_harness_v2.1.md](docs/planning/ideation_assessment_harness_v2.1.md) | 제품 목적과 장기 방향 (3순위) |
| [docs/planning/ideation_assessment_harness_v2.md](docs/planning/ideation_assessment_harness_v2.md) · [v1](docs/planning/ideation_assessment_harness_v1.md) | historical reference |
| [docs/planning/publication_plan_v1.md](docs/planning/publication_plan_v1.md) | 이 공개 작업 자체의 계획 (메타 프로세스) |
| [schemas/](schemas/) | JSON Schema 데이터 계약 |
| [docs/guidelines/sdk_runner_decisions.md](docs/guidelines/sdk_runner_decisions.md) | 실제 SDK runner 구현 전 결정해야 할 credential / sample / trace retention 체크리스트 |
| [docs/guidelines/sample_assignment_guidelines.md](docs/guidelines/sample_assignment_guidelines.md) | AI가 PoC용 테스트 과제 spec/rubric 샘플을 만들 때 따를 작성 가이드 |

**상세 기록 (감사 추적)**

| 문서 | 역할 |
|---|---|
| [docs/verifications/](docs/verifications/) | 슬라이스별 독립 검증 기록 (자산) |
| [docs/daily_logs/](docs/daily_logs/) | 동시대 작업 일지 |
| [CHANGELOG.md](CHANGELOG.md) | 주요 milestone |

**에이전트·기여자용 (운영)**

| 문서 | 역할 |
|---|---|
| [HANDOFF.md](HANDOFF.md) | 현재 상태 스냅샷, 다음 작업자용 |
| [AGENTS.md](AGENTS.md) / [CLAUDE.md](CLAUDE.md) | 코딩 에이전트 행동 지침 |

---

## 비범위 (오해 방지)

본 도구는 다음을 하지 않는다.

- 응시자 제출물 자동 채점
- 합격/불합격 판정
- 평가 결과 응시자 통보
- 법적 공정성 판단
- 평가자 대체

이 영역들은 자동화로 다룰 수 없거나, 본 PoC가 해결하려는 문제 범위 밖이다.
