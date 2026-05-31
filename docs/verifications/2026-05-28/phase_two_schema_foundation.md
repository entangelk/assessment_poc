# Verification — Phase 2 Contract Schema Foundation

- 검증 일자: 2026-05-28
- 검증 요청자: Owner — "핸드오프와 데일리 로그 확인해서 작업분 검증하고 의심해서 확인해줘"
- 검증 수행자: AI (Claude Code, claude-opus-4-7)
- 검증 대상: Phase 2 contract schema foundation — `schemas/id_map.schema.json`, `schemas/semantic_verifications.schema.json`, `src/assessment_harness/schemas.py` 등록, `tests/test_models.py` 회귀
- 검증 소스: working tree, uncommitted (HEAD = `62e0b78`, 본 슬라이스는 그 위의 미커밋 작업분)
- 정본 spec 기준:
  - `docs/implementation_plan_assessment_harness_poc_v1.md` v1.21 §5.0 (199-210, id_map), §5.3.1 (342-373, semantic_verifications), §7 (804-832, 파일 레이아웃)
  - 표면 단일 작업자 주장: 작업로그 §"Phase 2 Contract Schema Foundation" ([work_log:439-486](../daily_logs/2026-05-28/work_log.md#L439-L486))

## Scope

1. 계약 범위 분리(scoping): 작업자가 명시한 비범위(runner credential, identity-basis 알고리즘, run count, trace retention)가 실제 변경분에 포함되지 않았는가.
2. Spec ↔ 스키마: 두 신설 스키마의 필수/선택 필드, 타입, enum이 plan §5.0 / §5.3.1과 일치하는가.
3. Spec ↔ 스키마 enum 경계: `id_map.entity_type`, `semantic_verifications.status_proposal` 둘 다 plan 본문이 명시한 경계와 일치하는가.
4. 등록: `SCHEMA_FILES`에 두 키가 등록되어 있고 `validate()` 헬퍼로 도달 가능한가.
5. 회귀 테스트 audit: 회귀가 (a) plan-example을 잠그는가, (b) under-strict 가드(빈 `run_refs`, human-final status_proposal)가 양쪽 모두 실제로 실패시키는가.
6. 회귀 무손상: 전체 스위트 + Docker 외 (작업자 주장 165 passed, 48 CLI / 8 fixture / 14 model / 95 rule).
7. 문서 일관성: HANDOFF.md / CHANGELOG.md / README.md / work_log.md의 "ten/twelve schemas" 카운트 동기화.

## Methodology

- 계약: plan v1.21 §5.0 199-210 + §5.3.1 342-373 정독.
- 스키마: `schemas/id_map.schema.json`, `schemas/semantic_verifications.schema.json` 직접 비교.
- 등록: [src/assessment_harness/schemas.py:19-32](../../src/assessment_harness/schemas.py#L19-L32) `SCHEMA_FILES` 직접 확인.
- 테스트 audit: [tests/test_models.py:62-133](../../tests/test_models.py#L62-L133) 두 신규 테스트 함수 본문 정독.
- 회귀 직접 재현:
  - `PYTHONPATH=src python3 -m pytest tests/test_models.py -q` → **14 passed**.
  - `PYTHONPATH=src python3 -m pytest -q` → **165 passed**.
  - `pytest --collect-only -q` → 48 CLI contract / 8 fixture / 14 model / 95 rule (= 165) 일치.
- 워킹트리 스코프: `git status --short` — 변경 파일 = HANDOFF, CHANGELOG, README, work_log, schemas.py, test_models.py + 신규 두 스키마 파일. 다른 파일 미수정.

## Findings

### 1. 작업 범위 — 작업자가 선언한 비범위 그대로 지켜짐

작업자는 work_log에서 "Phase 2의 큰 결정들(runner credential, identity-basis 알고리즘, run count 정책 등)은 건드리지 않고, 이미 계획서에 고정돼 있던 계약 표면만 깔았다"고 명시. `git status --short` 직접 확인 결과:
- 신규: `schemas/id_map.schema.json`, `schemas/semantic_verifications.schema.json` (2개)
- 수정: `src/assessment_harness/schemas.py`, `tests/test_models.py`, `HANDOFF.md`, `CHANGELOG.md`, `README.md`, `docs/daily_logs/2026-05-28/work_log.md`
- `cli.py`, `rules.py`, `models.py`, `report.py`, `config/policy.yaml`, fixture 디렉토리 **미수정** — 작업자 선언과 일치. runner/compact/verify 코드는 일절 추가되지 않음. **정합.**

### 2. Spec ↔ id_map 스키마 — 본문은 일치, enum은 plan보다 광범위(소견)

Plan §5.0 (199-210) 예시:
```yaml
id_map:
  - canonical_id: S1
    entity_type: spec_item
    run_refs:
      - { run_id: "run_..._a1b2", local_id: "S4" }
      - { run_id: "run_..._c3d4", local_id: "S1" }
```

스키마([id_map.schema.json:7-42](../../schemas/id_map.schema.json#L7-L42))의 필수/타입 매핑:
- `canonical_id`: string minLength 1 — plan 예시와 일치.
- `entity_type`: enum `["spec_item", "rubric_item", "trace_link"]`.
- `run_refs`: minItems 1, 각 항목 `{run_id, local_id}` 필수, 둘 다 string minLength 1 — plan 예시와 일치.
- top-level + 각 entry `additionalProperties: true` — plan §5.0 끝줄 "향후 프로젝트/버전 관리가 추가되면 `project_id`, `assessment_version`, canonical ID lineage를 확장한다"와 호환 ✓.

**소견 (계약 갭, 아직 비차단)**: plan §5 본문 199행은 `compact`가 "spec/rubric item을 먼저 compacting하여 canonical item ID를 부여하고, 이후 trace link의 **run-local reference**를 canonical ID로 remap한다"고 명시. trace link 자체는 reference만 다시 매핑될 뿐 canonical_id가 부여되지 않는 것으로 보임. plan 예시도 `entity_type: spec_item`만 보임. 스키마의 `entity_type` enum이 `trace_link`까지 포함하는 것은 plan 본문이 명시적으로 허용하지도 금지하지도 않은 권한 확장. **현 시점에는 스펙-침묵-스키마-허용 상태**이므로 [CLAUDE.md "Spec-silent-but-code-enforced is a contract gap"](../../CLAUDE.md) 규정에 따라 다음 슬라이스에서 (a) trace_link가 id_map에 들어오는 합법 시나리오가 있는지 plan에 명시하거나, (b) enum을 `["spec_item", "rubric_item"]`으로 좁히는 결정이 필요. 본 슬라이스 범위는 "계약 표면 등록"이고 trace_link entry가 실제로 생성되지는 않아 즉시 잘못된 데이터 흐름은 없음 — **conditional pass** 수준.

### 3. Spec ↔ semantic_verifications 스키마 — 정합

Plan §5.3.1 예시(345-356) 필드와 [semantic_verifications.schema.json:17-43](../../schemas/semantic_verifications.schema.json#L17-L43) 필수 필드 정확히 일치:
- `trace_link_id`, `status_proposal`, `rationale`, `source_refs`, `support`, `variants` 모두 required.
- `support` 구조: `total_valid_runs` (integer ≥0) + `found_in_runs` (array of string) — plan 예시(352-354)와 일치.
- `source_ref` 내부 필수: `document_id`, `start_line`, `end_line` — plan §5.3.1 line 349-351의 예시 그대로.
- `additionalProperties: true` for forward compatibility — plan 일반 패턴과 호환.

`status_proposal` enum = `["agent_supported", "agent_rejected", "agent_uncertain"]`. plan §5.3.1 상태표(362-371):
- agent_supported / agent_rejected / agent_uncertain → verifier-agent proposal — 포함.
- pending_verification → trace_link 초기 상태이지 verifier "proposal"이 아님 — 제외 정합.
- human_accepted / human_rejected / human_overridden / rerun_requested → 최종 reviewer 결정, `gate`/final review territory — 제외 정합.

**정합.** 작업자가 work log "Decisions"에 "Human statuses remain final-review/gate territory and are rejected by the schema" 명시한 그대로.

### 4. 등록 — OK

[schemas.py:30-31](../../src/assessment_harness/schemas.py#L30-L31)에서 `id_map`, `semantic_verifications` 키로 등록. `lru_cache` 캐시 + `validate()` 헬퍼 경로가 모든 등록 키에 동일 적용되므로 별도 회로 추가 없음. ✓.

### 5. 테스트 audit — under-strict 가드 양방향 잠김, 단 over-strict 보강 여지 있음

**Under-strict (계약 위반이 실제로 회귀로 잡히는가)**:

| 잠긴 경계 | 테스트 위치 | 검증 |
|---|---|---|
| 스키마 키 등록 자체 | [test_models.py:97-98](../../tests/test_models.py#L97-L98) | `assert "id_map" in SCHEMA_FILES`, 동일하게 `semantic_verifications` |
| plan-example validation | [test_models.py:99-100](../../tests/test_models.py#L99-L100) | `validate(...) == []` — plan §5.0 / §5.3.1 예시 그대로 통과 |
| `run_refs: []` (canonical ID가 어떤 run에서도 유래하지 않는 비추적 entry) | [test_models.py:103-115](../../tests/test_models.py#L103-L115) | `assert id_map_errors` — minItems:1 가드가 강제 |
| `status_proposal: human_accepted` (verifier 단계에 human-final 상태 침입) | [test_models.py:116-131](../../tests/test_models.py#L116-L131) | `assert semantic_errors` — enum 위반 |

직접 재현 — `pytest tests/test_models.py -q` **14 passed**.

**Over-strict (정상 데이터가 잘못 거부되지 않는가)**: 작업자 plan-example 테스트가 사실상 over-strict 가드 역할. 추가로 `agent_rejected` / `agent_uncertain` 두 verifier 상태가 enum에 있으므로 잠겨 있지만, **각 verifier 상태별 parametrize 테스트는 없음**. 현재는 `agent_supported`만 한 케이스 통과. 향후 verifier 구현 시 status별 행동 차이가 추가되면 그때 parametrize 필요. **본 슬라이스 범위에서는 차단 아님**(스키마-only 작업이므로 status별 처리 분기 자체가 없음).

**스키마 셀프-디스커버리 검증**: 본 슬라이스는 신규 스키마를 `schema --command` 자기 노출 표면에 노출하지 않음. plan §5에 `schema --command id_map` 등이 정의되어 있지 않으므로 부재가 결함 아님 — 두 스키마는 `validate()` helper로만 접근하는 데이터 계약일 뿐 CLI 출력 envelope이 아님. **정합.**

### 6. 회귀 무손상 — 직접 재현 OK

- `PYTHONPATH=src python3 -m pytest -q` → **165 passed**, 0 failed.
- `pytest --collect-only -q`로 48 CLI / 8 fixture / 14 model (12→14, +2) / 95 rule 카운트 일치.
- 신규 회귀가 추가된 곳은 `test_models.py`만(+2). 기존 통과율 동일.

### 7. 문서 카운트 일관성 — OK

- HANDOFF [line 16](../../HANDOFF.md#L16): "twelve JSON Schemas" — 12 ✓.
- HANDOFF [line 195](../../HANDOFF.md#L195): "twelve JSON Schemas, including ... Phase 2 contract foundations `id_map.schema.json` / `semantic_verifications.schema.json`" ✓.
- CHANGELOG [신규 row](../../CHANGELOG.md): "Phase 2 contract schema foundation" 일자 항목 추가됨, 본 슬라이스 범위와 정합.
- work_log Verification절 "Stale schema-count grep" 보고: 직접 재현 — `rg -n "ten JSON Schemas|10 JSON Schemas|ten schemas|10 schemas" README.md HANDOFF.md CHANGELOG.md docs src tests` → no matches (재확인 권장하면 즉시 수행 가능).
- README diff는 v1.20 → v1.21 한 줄 정렬뿐, 본 슬라이스와 별개 정합 작업(이미 별도 work_log 절에서 보고됨).

## Issues / Risks

1. **(소견, 비차단)** `id_map.entity_type` enum이 `trace_link`까지 포함하지만 plan §5.0 본문은 spec/rubric의 canonical_id 부여만 명시. `trace_link`는 reference remap 대상으로만 기술됨. 향후 `compact` 구현 시 trace_link entry가 실제로 id_map에 들어오는지 plan 차원에서 명시(또는 enum 축소)가 필요. **CLAUDE.md "Spec-silent-but-code-enforced" 규정상 conditional gap.** 본 슬라이스가 계약 등록만 수행하고 데이터 생성 코드를 추가하지 않으므로 즉시 잘못된 산출물이 발생하지는 않음.
2. **(소견, 비차단)** `semantic_verifications`의 `source_refs`는 minItems 제약 없음(빈 배열 허용). plan §5.3.1 예시는 비어 있지 않으나 본문이 "최소 1개 이상" 같은 표현으로 잠그지 않음. `agent_uncertain` 케이스에서 인용 근거가 없는 합법 시나리오가 있을 수 있으므로 현재 허용이 합리적이지만, 추후 verifier 구현 시 status별 요구가 갈리면 명시 필요.
3. **(보강 여지)** `status_proposal` enum의 세 verifier 상태(`agent_supported`/`agent_rejected`/`agent_uncertain`)는 현재 한 케이스(`agent_supported`)만 회귀로 잠겨 있음. 추후 verifier 구현 시 status별 처리 분기가 생기면 parametrize 필요. 현 슬라이스 차단 아님(스키마-only).
4. **(보강 여지)** `id_map`/`semantic_verifications` fixture가 아직 없음 — 작업자도 "compact/verify 구현 슬라이스에서 추가"로 미룬 사항으로 보임. 정합.

## Verdict

**조건부 합격(Conditional pass).**

근거:
- 작업자 선언 범위(스키마 두 개 등록 + plan-example/거부 회귀 + 문서 카운트 동기화)를 정확히 그 범위만큼 수행. Phase 2의 큰 결정(runner/identity-basis/run-count/retention)에 침범 없음 ✓.
- plan §5.0 / §5.3.1 본문 필드/타입/enum이 스키마에 그대로 잠김 ✓.
- under-strict 가드 두 방향(빈 `run_refs`, human-final 상태_proposal) 잠김 ✓.
- 회귀 165 passed 직접 재현 ✓.
- 단, **`id_map.entity_type` enum의 `trace_link` 포함이 plan 본문에서 명시적으로 인가되지 않은 권한 확장**으로 남아 있어 다음 슬라이스에서 plan 명시 또는 enum 축소 결정 필요. 본 슬라이스 자체는 데이터 흐름을 만들지 않으므로 즉시 잘못된 산출은 없음.

## Outstanding Items

- 워킹트리 미커밋. 작업자가 owner 인가를 받고 commit/push 진행 예정.
- 위 Issues 1 (entity_type 권한 확장)을 다음 슬라이스 entry point — `compact` 구현 또는 plan v1.22 명시화 — 어디서 결정할지 owner 선택 필요.

## Reproduction

```bash
cd <repo>
PYTHONPATH=src python3 -m pytest tests/test_models.py -q          # → 14 passed
PYTHONPATH=src python3 -m pytest -q                                # → 165 passed
PYTHONPATH=src python3 -m pytest --collect-only -q | tail -5       # → 48 CLI / 8 fixture / 14 model / 95 rule
git status --short                                                  # → 두 신규 스키마 + 6 수정 파일만
rg -n "ten JSON Schemas|10 JSON Schemas|ten schemas|10 schemas" \
   README.md HANDOFF.md CHANGELOG.md docs src tests                 # → no matches
```
