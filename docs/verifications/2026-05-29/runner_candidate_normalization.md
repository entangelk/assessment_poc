# Verification: Runner Artifact → Candidate Normalization Helper (plan v1.26)

## Subject metadata

- **Date**: 2026-05-29
- **Requester**: Owner (kdtyohan@gmail.com) — "다음 작업 검증해줘"
- **Verifier**: Claude (independent audit)
- **Target slice**: `normalize_result_candidates` 헬퍼 신설(`normalization.py`) + 회귀 테스트, plan v1.26 승격, 문서 갱신. 직전 라운드 outstanding(단언 정밀화) 적용 여부 동시 확인.
- **Canonical spec reference**: `docs/implementation_plan_assessment_harness_poc_v1.md` v1.26, 변경 이력 v1.26 (lines 1322-1339). 연계: `candidates.schema.json`, `spec_items`/`rubric_items`/`trace_links` schema, `base.py:AgentRunResult`, `mock.py`.
- **Source of work verified**: working tree, uncommitted.

## Scope

1. 정본 계약(v1.26 changelog 3요구: 변환 / provenance·default status 부여 / compacting-only 필드 제거) ↔ 구현 일치.
2. 구현 정확성(`normalization.py`) — artifact 이중 중첩 형태 가정, stripping 범위, 카운트.
3. 회귀 테스트가 boundary matrix를 비공허하게 잠그는지 (특히 schema 통과만으로는 못 잡는 stripping).
4. export 표면.
5. 직전 라운드 단언 정밀화 적용 확인.
6. 문서 정량 주장 재계산.

## Methodology

- 코드 정독: `normalization.py`(85 lines), `base.py`, `mock.py`.
- fixture 형태 확인: `fixtures/clean_assignment/{spec_items,rubric_items,trace_links}.yaml`, compacting 필드 grep.
- 동작 탐침: `PYTHONPATH=src python3 -c` 로 실제 mock runner→normalize 호출, 카운트/키/stripping 직접 측정.
- 테스트: `pytest tests/test_agent_runner_contract.py`, 전체 `pytest`, `--collect-only`, `git diff --check`.

## Findings

### F1. artifact 형태 가정 — 정확

`normalization.py:59-62` 는 `result.artifacts["spec_items"]["spec_items"]` 식 이중 중첩을 읽는다. `mock.py:34-38` 가 `artifacts["spec_items"] = read_yaml(spec_items.yaml)` 이고 fixture YAML 최상위가 `{spec_items: [...]}` (compacted-artifact 형태)이므로 이중 키가 **올바름**. 비-Mapping/비-list 면 `[]` 반환(방어 분기). → 조용한 빈 반환 위험 없음(탐침에서 실제 4/4/3 산출 확인).

### F2. 구현 정확성 — 정확 (탐침)

mock(clean_assignment) → normalize 직접 호출:
- counts spec/rubric/trace = **4/4/3**, candidate_id 가 섹션별 `SC1.. / RC1..RC4 / TC1..` 순차 부여 ✓
- spec proposed_item: `support`/`identity_basis`/`variants` **제거됨** ✓
- rubric proposed_item: 동일 3필드 **제거됨** ✓ (공유 `_normalize_items` 경로)
- trace proposed_item: `sources`/`reviewed_by`/`reviewed_at` 제거, `semantic_status: pending_verification` **유지** — `candidates.schema.json` trace_link $defs가 semantic_status를 허용하고 값이 중립 초기상태라 타당(아래 관찰 참조).
- provenance: `agent_runner=mock_fixture`, `agent_run_id=mock_run`, `integrity_status=pending_check` 부여 ✓

### F3. 회귀 테스트 — 핵심 over-strict guard 존재

`candidates.schema.json` 은 전 객체가 `additionalProperties: true` 이므로 **stripping을 안 해도 스키마는 통과**한다. 따라서 schema 검증만으로는 stripping 회귀를 못 잡는다. 이를 정확히 인지하고 `test_candidate_normalization_strips_compacting_only_fields` 가 **필드 부재를 직접 단언**(`assert "support" not in spec_item` 등) — 핵심 잠금 존재.

| 분기 | 테스트 | 상태 |
|---|---|---|
| normalize 출력이 candidate-schema valid | `..._normalizes_to_candidate_artifacts` (`== []`) | ✓ |
| attribution helper 호환 | 동 (`validate_candidate_audit_trace == []`) | ✓ |
| provenance(runner/run_id) 부여 | 동 단언 | ✓ |
| default `pending_check` | 동 단언 | ✓ |
| candidate_id 생성(SC1) | 동 단언 | ✓ |
| spec compacting 필드 제거 | `..._strips_compacting_only_fields` (부재 단언) | ✓ |
| trace review/provenance 제거 | 동 | ✓ |

### F4. export / 직전 outstanding — 확인

- `__init__.py` `__all__` 에 `normalize_result_candidates` 추가, 패키지 최상위 import 로 테스트가 공개 표면 사용.
- 직전 라운드 권고 단언 정밀화 적용됨: `test_candidate_audit_trace_validation_keeps_schema_errors_visible` 가 `error.startswith("candidates:") and "agent_run_id" in error and "is a required property" in error` 로 핀 (schema 오류 경로를 attribution 오류와 구별).

### F5. 문서 정량 주장 — 재계산 일치

- "185 tests pass" → `pytest`: **185 passed** ✓
- "13 agent-runner / 48 CLI / 8 fixture / 21 model / 95 rule" → agent-runner `--collect-only` = **13** ✓ (합 185)
- plan/HANDOFF/README/CHANGELOG v1.26 참조 일관, `validation.py` 옆 `normalization.py` 구조 기재 ✓
- `git diff --check` clean ✓

## Issues / Risks

비차단 관찰만:
- **[경미·완전성]** stripping/provenance/candidate_id 단언이 **spec + trace 섹션에만** 명시. rubric 섹션은 동일 `_normalize_items` 공유 경로라 탐침상 정상 작동하나 섹션-특정 단언 없음. 직전 attribution 테스트처럼 섹션 parametrize 하면 매트릭스가 완전 대칭이 됨. (공유 구현이라 spec 단언이 깨지면 rubric도 깨지므로 차단 아님.)
- **[관찰]** trace candidate에 `semantic_status` 유지. plan strip 목록에 미열거이고 스키마가 허용하므로 결함 아니나, "추출 단계 runner가 verification 상태값을 설정"하는 것이 의도인지 향후 verifier 슬라이스에서 재확인 권장.
- **[CLAUDE.md §2]** `_normalize_items` 의 비-Mapping/비-list 방어 분기는 계약에 명시되지 않은 방어 코드이며 테스트 없음. 무해하나 약한 over-engineering 소지.
- **[경미]** `integrity_status` 오버라이드 파라미터와 candidate 개수(완전성)는 미단언(현재 [0]만 확인).

## Verdict

**합격 (pass).**

근거:
- v1.26 세 요구(변환 / provenance·default status / compacting-only 제거)를 정확히 구현, 탐침으로 4/4/3 산출과 stripping·provenance·default status 확인(F1/F2).
- schema 통과만으로 못 잡는 stripping을 **필드 부재 직접 단언**으로 잠금 — 핵심 over-strict guard 존재(F3). attribution 호환·schema valid 는 `== []` 강한 단언.
- 직전 라운드 단언 정밀화 적용 확인(F4). 문서 정량 전부 재계산 일치(F5).
- 잔여는 전부 비차단(섹션 대칭성/관찰/방어코드/완전성 노트).

## Outstanding items

- 모든 변경 uncommitted. 커밋 권한 Owner 결정.
- rubric 섹션 stripping 단언 추가(섹션 parametrize)는 선택적 완전성 개선 — 차단 아님.
- `semantic_status` 유지 의도는 verifier 슬라이스 진입 시 재확인 권장.

## Follow-up verification — 잔여 정리 + semantic_status 의도 확인 (2026-05-29, 동일 슬라이스)

Owner가 비차단 잔여 중 두 가지를 정리하고 `semantic_status` 유지 의도 확인을 요청. 독립 재확인 결과:

- **rubric stripping 대칭 확보**: `test_candidate_normalization_strips_compacting_only_fields` 가 `spec_item_candidates`/`rubric_item_candidates`/`trace_link_candidates` 3섹션 parametrize 로 전환됨. 각 섹션이 해당 stripped 필드 부재를 단언(trace는 `support/identity_basis/variants/sources/reviewed_by/reviewed_at` 6종). boundary matrix의 섹션 대칭 빈 칸 해소.
- **무계약 방어 제거**: `_normalize_items` 가 `result.artifacts[artifact_key]` / `artifact[item_key]` 직접 subscript 로 변경(`isinstance` 가드·`.get` 제거). malformed/누락 artifact 는 이제 조용한 빈 후보 대신 자연 예외로 드러남 — "malformed를 정상 empty로 위장하지 않는다"는 §10.2 격리 취지와 정합. orphan `collections.abc.Mapping` import 도 제거됨(§3 위생).
- **재계산 일치**: `pytest` → **187 passed**; agent-runner `--collect-only` = **15** (strip 테스트 1→3 parametrize 로 +2); HANDOFF/work_log 카운트 187/15 로 갱신 일관; `git diff --check` clean; normalization.py 내 `Mapping` 참조 0.

### `semantic_status` 유지 의도 — **타당함 (deferral 적절)**

§5.3 상태표(plan line 360, 366) 재확인:
- line 360: `check` 는 "compacted trace link의 초기 `pending_verification` 상태"와 별도 `semantic_verifications.yaml` 을 함께 읽어 effective semantic status 를 계산하며 원본 link 를 덮어쓰지 않는다 — 즉 **권위 있는 상태는 candidate 필드가 아니라 downstream 계산** 이다.
- line 366: `pending_verification` = "compact 직후, 의미 확인 전", **confirmed coverage 아님**.

따라서 fixture 의 `semantic_status: pending_verification` 를 candidate 에 유지하는 것은: (a) 스키마가 허용(trace_link $defs 선택 필드), (b) 값이 중립 초기상태라 coverage 부풀림·false-pass 불가, (c) plan 이 candidate 단계 stripping 을 명시하지 않음 — 세 조건 모두 충족하므로 **결함 아님**. lifecycle 결정(추출 candidate 가 semantic_status 를 보유/리셋해야 하는지)을 verifier/effective-semantic-status 슬라이스로 미루는 것도 범위상 옳다.

**단, 후속 슬라이스가 반드시 잠가야 할 한 가지**: 현재 normalization 은 artifact 의 semantic_status 를 **값 검사 없이 그대로 통과**시킨다. mock fixture 가 항상 중립 `pending_verification` 이라 "실제 runner 가 비중립 상태(`agent_supported`/`human_accepted` 등)를 추출 candidate 에 주입"하는 경로를 막는 가드가 없다. verifier/effective-status 슬라이스에서 normalization(또는 compacting)이 candidate semantic_status 를 `pending_verification` 으로 리셋할지 신뢰할지 결정하고 회귀로 잠가야 한다. (이번 슬라이스 차단 사유 아님 — 의도된 deferral.)

### 갱신 판정: **합격 (pass).** 직전 라운드 비차단 잔여 2건 정리됨, semantic_status 유지 의도는 스펙상 타당하며 deferral 도 적절. 위 후속-슬라이스 잠금 항목만 추적으로 남김.

## Reproduction

```bash
cd "/workspace/assessment_poc"
PYTHONPATH=src python3 -c "
from pathlib import Path
from assessment_harness.agent_runners import MockFixtureRunner, normalize_result_candidates
r=MockFixtureRunner(Path('fixtures/clean_assignment'), run_id='mock_run')
res=r.run(Path('fixtures/clean_assignment/source/spec.md'),Path('fixtures/clean_assignment/source/rubric.md'),[],1,{'rules':{}})
c=normalize_result_candidates(res)
print(len(c['spec_item_candidates']),len(c['rubric_item_candidates']),len(c['trace_link_candidates']))
print(sorted(c['rubric_item_candidates'][0]['proposed_item']))"
python3 -m pytest tests/test_agent_runner_contract.py -q
python3 -m pytest
python3 -m pytest tests/test_agent_runner_contract.py --collect-only | grep -c test_
git diff --check
```
