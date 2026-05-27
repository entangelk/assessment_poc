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
  --diagnostics-out integrity_diagnostics.json

assessment-harness report \
  --findings findings.json \
  --diagnostics integrity_diagnostics.json \
  --out report.md
```

`--source-manifest`는 Phase 0 `check`의 필수 인자다 (plan §5.0 / §5.1 / §11). 누락하면 `status=invalid_input`, exit `2`, 진단 `source_manifest_required`, next_action `provide_source_manifest`가 반환된다.

Phase 0에서 semantic verification 입력이 없으면 `ai_judgement` link는 의미 확인 대기 상태로 남는다. Agent 실행 흐름에서는 아래 `verify` 산출물을 후속 명령에 전달한다.

### 3. 에이전트 실행 포함 전체 흐름 (Phase 2/3)

```bash
# 복수 독립 실행
assessment-harness extract \
  --spec assignment/README.md \
  --rubric assignment/rubric.md \
  --runner claude_sdk \
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
  --runner claude_sdk \
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

# 최종 human review 기록
assessment-harness review \
  --compacted-dir work/compacted \
  --findings work/findings.json \
  --diagnostics work/integrity_diagnostics.json \
  --semantic-verifications work/semantic_verification/semantic_verifications.yaml \
  --review-queue work/compacted/review_queue.json \
  --report work/report.md \
  --out-dir work/final_review

# 최종 review 이후 외부 판정
assessment-harness gate \
  --final-review work/final_review/review.yaml \
  --policy config/policy.yaml \
  --output json
```

---

## 흐름 개요

```
caller agent → CLI
    ↓
spec.md + rubric → agent runner (multi-run, tool use)
    ↓
run별 candidate + agent_trace (raw + audit 분리 저장)
    ↓
run integrity check (Rule 0)
    ↓
compacting (union, 자동 채택 없음, support/identity_basis/variants 보존)
    ↓
compacted artifacts + review_queue
    ↓
semantic verifier-agent (read-only, multi-run)
    ↓
semantic_verifications (제안 보존, 자동 확정 없음)
    ↓
deterministic check (Rule 0~3, provisional findings)
    ↓
findings + report
    ↓
final human review (accept | hold | rerun | override)
    ↓
gate (external final decision)
```

---

## 핵심 데이터 계약

자세한 schema는 [구현 계획서 §5](docs/implementation_plan_assessment_harness_poc_v1.md#5-데이터-계약) 참고. 요약:

- **spec_items / rubric_items / trace_links**: compacted artifacts. `support` (어느 run에서 발견), `identity_basis` (동일성 판단 기준), `variants` (미세 차이 보존)
- **source_manifest / source_ref**: immutable input snapshot hash와 line/span anchor. DB/RAG 없이도 원문 grounding 검증
- **id_map**: run-local ID를 compacted canonical ID로 remap한 provenance. 후속 프로젝트/버전 관리 확장 지점
- **trace_links.evidence_quotes**: `verification_mode` 별 분기
  - `token_sequence`: strict substring 매칭 (정량 marker 검증)
  - `ai_judgement` (default): reference integrity만, 의미는 read-only verifier-agent 제안과 최종 human review로 확인
- **semantic_verifications.yaml**: verifier-agent 복수 run의 `supported` / `rejected` / `uncertain` 제안 취합. compacted link는 수정하지 않음
- **integrity_diagnostics.json**: Rule 0 위반 기록
- **review_queue.json**: `invalid_run` / `ai_judgement_pending` / `identity_collision` / `low_support` / `semantic_disclosure` 5종 entry
- **findings.json**: Rule 1~3 위반 (Rule 0는 별도 diagnostic)
- **final_review/**: 최종 검토자의 accept/hold/rerun/override 기록
- **gate output**: final review 이후 외부 호출자가 소비하는 pass/fail/pending 판정

---

## 정책 파일

모든 정책은 `config/policy.yaml` 하나로 통합.

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

## Phase 진행 상태

| Phase | 범위 | 상태 |
|---|---|---|
| 0 | Deterministic validation core (Rule 0~3, 수동 fixture) | 진행 중 (Rule 0 + Rule 1 전체 분기 (`possible_orphan_scored_rubric_item`, `unconfirmed_trace_coverage`, `orphan_bonus_rubric_item`) 완료. Rule 2, Rule 3, `gate` 대기) |
| 1 | 실제 과제 manual run | Phase 0 후 |
| 2 | Candidate/verifier agent multi-run + compacting | Phase 1 후 |
| 3 | Final human review + `gate` + caller agent 시연 | Phase 2 후 |

상세 진입 조건/완료 기준: [구현 계획서 §9, §12](docs/implementation_plan_assessment_harness_poc_v1.md#9-단계별-구현-계획)

---

## 문서

| 문서 | 역할 |
|---|---|
| [docs/implementation_plan_assessment_harness_poc_v1.md](docs/implementation_plan_assessment_harness_poc_v1.md) | **구현 명세 (1순위 SoT)** — 현재 v1.11 |
| [docs/ideation_assessment_harness_v2.2.md](docs/ideation_assessment_harness_v2.2.md) | Rubric Lint Rules 가족 (2순위, 2026-05-27 final + in-place 개정) |
| [docs/ideation_assessment_harness_v2.1.md](docs/ideation_assessment_harness_v2.1.md) | 제품 목적과 장기 방향 (3순위) |
| [docs/ideation_assessment_harness_v2.md](docs/ideation_assessment_harness_v2.md) | historical reference |
| [docs/ideation_assessment_harness_v1.md](docs/ideation_assessment_harness_v1.md) | historical ideation |
| [HANDOFF.md](HANDOFF.md) | 현재 상태 스냅샷, 다음 작업자용 |
| [CHANGELOG.md](CHANGELOG.md) | 주요 milestone |
| [docs/daily_logs/](docs/daily_logs/) | 작업 일지 |
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
