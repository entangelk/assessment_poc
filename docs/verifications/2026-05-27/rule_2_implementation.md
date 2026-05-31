# Verification — Rule 2 (Required Spec Coverage) Implementation

- 검증 일자: 2026-05-27
- 검증 요청자: Owner (kdtyohan@gmail.com)
- 검증 수행자: AI (Claude Code, claude-opus-4-7)
- 검증 대상: Phase 0 Rule 2 (`uncovered_must_spec_item` / `review_uncovered_must_spec`) slice — working tree, uncommitted
- 정본 spec 기준: `docs/implementation_plan_assessment_harness_poc_v1.md` v1.14 §6 Rule 2
- 작업 보고 출처: 같은 슬라이스를 구현한 다른 AI의 핸드오프 보고 + `docs/daily_logs/2026-05-27/work_log.md` 마지막 절

## Scope

다음 다섯 면을 모두 같은 정본 계약에 합치하는지 독립적으로 검증한다.

1. plan v1.14 §6 Rule 2 본문 (출력 계약, 구조적 경계).
2. 구현 코드 (`run_rule_two`, CLI 결합).
3. 회귀 테스트 (`test_rules.py` Rule 2 케이스, 양방향 가드).
4. Fixture grounding (`fixtures/uncovered_must_spec/`, 기존 `fixtures/bonus_misuse/` 갱신분).
5. 공개 envelope/schema discovery (`test_cli_output_contract.py`, `schema --command check`).

또한 `docker compose run --rm test`가 보고된 117개 통과하는지, 두 fixture smoke check가 보고 envelope 수치와 일치하는지를 실 환경에서 확인한다.

## Methodology

- 모든 검증은 `docker compose` 기반 dev 환경에서 수행. 실행 명령은 각 항목에 함께 기재.
- 코드 검토는 변경 핵심 파일과 plan 본문을 line 단위로 대조. 모든 인용에는 file:line 링크를 부여.
- Fixture grounding은 `sha256sum`으로 manifest와 직접 대조.
- 양방향 가드는 plan 본문의 over-strict 절을 한 항목씩 따라가며 테스트 함수가 그 조건을 직접 잠그는지 확인.

## Findings

### 1. plan v1.14 §6 Rule 2 계약 확인

[implementation_plan_assessment_harness_poc_v1.md:634-643](../implementation_plan_assessment_harness_poc_v1.md#L634-L643) 기준.

- finding type: `uncovered_must_spec_item` — 일치.
- severity / decision_status: `medium` / `provisional` — 일치.
- next_action: `review_uncovered_must_spec` — 일치.
- 구조적-only 명시 ("`semantic_status`를 참조하지 않는다", L643) — 구현 일치.
- Rule 1과 `gate`만 final-coverage 경계를 적용한다는 §6 헤더 절(L632)이 Rule 2/3에 그대로 적용 안 됨을 명시 — Rule 2의 pending coverage 인정과 정합.

### 2. 구현 코드

#### `run_rule_two` ([rules.py:698-743](../../src/assessment_harness/rules.py#L698-L743))

- `scored_rubric_ids` set은 `evaluation_role == "scored"`인 rubric만 추출. bonus/qualitative는 자연 제외.
- `scored_spec_ids`는 위 set에 속한 rubric의 trace_link만으로 구성. `semantic_status`를 참조하지 않음 → 구조적-only 경계 정확.
- finding 발화 조건은 `requirement_level == "must"` AND `spec_id not in scored_spec_ids` — optional/informational은 자연 제외, bonus/qualitative-only coverage는 cover로 인정되지 않음.
- 최소 코드, 분기 단순, plan 본문 외 임의 추론 없음.

#### CLI 결합 ([cli.py:166](../../src/assessment_harness/cli.py#L166), [cli.py:242-249](../../src/assessment_harness/cli.py#L242-L249))

- Rule 0 clean pass 직후, Rule 1과 같은 단계에서 `run_rule_two` 호출.
- `uncovered_must_spec_item` finding마다 `review_uncovered_must_spec` next_action을 spec_id와 함께 추가.
- envelope `provisional_medium_count`에 자연스럽게 집계됨 (별도 카운터 미신설 — Rule 1과 같은 경로).

### 3. 회귀 테스트 — 양방향 가드

[test_rules.py:1320-1368](../../tests/test_rules.py#L1320-L1368) 기준. plan §6 Rule 2의 본문 조건과 1:1 대응되는지 확인.

| 가드 종류 | plan 본문 조건 | 테스트 함수 | 합격 |
|---|---|---|---|
| under-strict | must 무추적 → 발화 | `test_rule_two_uncovered_must_spec_emits_medium_finding` | ✓ |
| over-strict A | pending scored 추적 → 미발화 (semantic_status 비참조) | `test_rule_two_pending_scored_trace_counts_as_structural_coverage` | ✓ |
| over-strict B | optional/informational 무추적 → 미발화 | `test_rule_two_ignores_uncovered_optional_and_informational_specs` | ✓ |
| over-strict C | bonus 또는 qualitative만 추적 → 발화 (scored coverage 아님) | `test_rule_two_non_scored_trace_does_not_cover_must_spec` (parametrized: bonus, qualitative) | ✓ |

특히 over-strict A 가드가 "Rule 1의 final-coverage 필터를 상속하지 않는다"는 보고서 주장을 회귀 테스트로 잠근 점이 정확.

### 4. Fixture grounding

#### `fixtures/uncovered_must_spec/`

- `sha256sum source/spec.md` = `bc2d577f091b64de92a093210b1ddb29aa65798e5fcc4d5e275128efcbfd8cf6` — manifest와 일치.
- `sha256sum source/rubric.md` = `42e90663c64ad2b3e3039a836ecfab9b934ee445bed4ce235ee66cd4a8419c76` — manifest와 일치.
- 6개 spec(must 4, optional 1, informational 1) × 3개 rubric(scored / bonus / qualitative)으로 모든 Rule 2 경계를 한 fixture에서 동시에 잠금.
  - S_COVERED: scored R_SCORED가 pending_verification으로 추적 → cover 인정 (over-strict A 시각화).
  - S_UNTRACED: 추적 없음 → finding (under-strict 시각화).
  - S_BONUS_ONLY: bonus R_BONUS만 추적 → finding + L5/L6 co-firing (over-strict C bonus 시각화).
  - S_QUAL_ONLY: qualitative R_QUAL만 추적 → finding, L6는 미발화 (qualitative 경계 시각화).
  - S_OPTIONAL / S_INFO: 추적 없어도 미발화 (over-strict B 시각화).

#### `fixtures/bonus_misuse/` 갱신

- RB4(bonus) + S3(must) 추가로 Rule 2 + L5 + L6 동시 발화 경계를 같은 fixture에서 시각화.
- [test_fixtures.py:252-253](../../tests/test_fixtures.py#L252-L253)에서 `(S3, medium)` Rule 2 finding을 직접 assert. 기존 RB1/RB3 boundary와 충돌하지 않음 (RB1은 L1+L5, RB3은 Rule 1 informational, S2/RB2는 미발화).

### 5. 공개 envelope / schema discovery

- `next_actions_types`에 `review_uncovered_must_spec` 추가 ([cli.py:460](../../src/assessment_harness/cli.py#L460), [test_cli_output_contract.py:281-293](../../tests/test_cli_output_contract.py#L281-L293)). 계약 회귀 잠금.
- `findings.schema.json`은 finding `type`을 enum 아닌 `minLength: 1` 문자열로 두기 때문에 새 finding type 추가만으로 별도 schema 변경 불필요. validate(findings) 통과로 확인.

### 6. 실 환경 smoke + 전체 회귀

```text
$ docker compose run --rm test
============================= 117 passed in 1.11s ==============================
```

```text
$ check on fixtures/uncovered_must_spec
status: provisional_findings, exit: 0
(high=1, medium=5, info=0), review_queue_count=1
actions ⊇ {
  review_uncovered_must_spec(S_UNTRACED),
  review_uncovered_must_spec(S_BONUS_ONLY),
  review_uncovered_must_spec(S_QUAL_ONLY),
  review_mandatory_spec_bonus_only(S_BONUS_ONLY),
  review_bonus_mandatory_only(R_BONUS),
  review_unconfirmed_trace_coverage(R_SCORED),
}
```

```text
$ check on fixtures/bonus_misuse
status: provisional_findings, exit: 0
(high=1, medium=5, info=1), review_queue_count=2
```

세 결과 모두 HANDOFF Verification 절(L141-148)과 work_log Verification 절의 보고 수치와 1:1 일치.

## Issues / Risks

- 없음. 보고된 다섯 면이 모두 정본 계약과 합치하고, 양방향 가드와 fixture grounding이 plan §6의 boundary clause를 회귀로 잠금.

## Verdict

**합격 — Rule 2 구현은 plan v1.14 §6 Rule 2 계약과 정확히 일치한다.**

근거:

1. 출력 literal 두 개(`uncovered_must_spec_item`, `review_uncovered_must_spec`)가 plan / 구현 / 테스트 / 계약 자기소개(`schema --command check`)에 한 자리에서 잠겨 있다.
2. "구조적-only, semantic_status 미참조" 경계가 회귀 테스트(over-strict A)와 fixture(S_COVERED pending coverage)로 양쪽 모두 시각화되어 있다.
3. Rule 2와 L6의 의도된 co-firing이 fixture와 테스트에서 숨겨지지 않고 명시적으로 assert되어 있다 (보고자가 의도한 "특수 케이스는 Rule 2의 medium 위에 L6의 high를 더 쌓는다"는 §6 본문과 정합).
4. 117 tests 전부 통과, 두 fixture smoke 결과가 보고 envelope과 완전 일치.

## Outstanding items (작업 자체와 무관, 운영 흐름)

- 본 슬라이스는 검증 시점 working tree에서 미커밋 상태이다 (`git log`의 HEAD는 `e2cdce9 Implement Rule L6 bonus-only mandatory coverage`).
- HANDOFF "Publication Boundary"에 Rule 2가 아직 포함되어 있지 않은 것이 정합: owner의 독립 AI 검증 + 게시 권한 부여 단계가 다음.
- 다음 구현 슬라이스는 plan §6 Rule 3 (`optionality_mismatch`, `policy.optionality_mismatch.weight_threshold`). HANDOFF Next Tasks에 그대로 잠겨 있어 추가 조치 불필요.

## Reproduction

본 검증을 재현하려면:

```bash
# 1. 전체 회귀
docker compose run --rm test -q

# 2. uncovered_must_spec fixture smoke
docker compose run --rm harness --output json check \
  --spec-items fixtures/uncovered_must_spec/spec_items.yaml \
  --rubric-items fixtures/uncovered_must_spec/rubric_items.yaml \
  --trace-links fixtures/uncovered_must_spec/trace_links.yaml \
  --source-manifest fixtures/uncovered_must_spec/source_manifest.yaml \
  --policy fixtures/uncovered_must_spec/policy.yaml \
  --out /tmp/findings.json --diagnostics-out /tmp/diag.json \
  --review-queue-out /tmp/queue.json

# 3. fixture grounding
sha256sum fixtures/uncovered_must_spec/source/spec.md \
          fixtures/uncovered_must_spec/source/rubric.md
# manifest와 동일해야 함

# 4. schema discovery
docker compose run --rm harness --output json schema --command check
# next_actions_types에 review_uncovered_must_spec 포함되어야 함
```
