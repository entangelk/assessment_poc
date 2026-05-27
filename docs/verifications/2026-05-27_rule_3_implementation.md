# Verification — Rule 3 (Optionality Consistency) Implementation

> **Superseded / verdict withdrawn (2026-05-27):** This initial record incorrectly treated uncovered Rule 3 boundary branches as non-blocking and also incorrectly stated that omission of `--policy` loads a default policy. Its pass verdict is withdrawn. The corrected post-remediation verdict is recorded in [2026-05-27_rule_3_boundary_tightening.md](2026-05-27_rule_3_boundary_tightening.md).

- 검증 일자: 2026-05-27
- 검증 요청자: Owner (kdtyohan@gmail.com)
- 검증 수행자: AI (Claude Code, claude-opus-4-7)
- 검증 대상: Phase 0 Rule 3 (`optionality_mismatch` / `review_optionality_mismatch`) slice — working tree, uncommitted
- 정본 spec 기준: `docs/implementation_plan_assessment_harness_poc_v1.md` v1.15 §6 Rule 3
- 작업 보고 출처: 같은 슬라이스를 구현한 다른 AI의 핸드오프 보고 + `docs/daily_logs/2026-05-27/work_log.md` 마지막 절

## Scope

다음 다섯 면을 한 정본 계약(plan v1.15 §6 Rule 3 + §7 policy 구조)에 합치하는지 독립적으로 검증한다. 단순히 테스트가 통과한다는 사실로 합격을 선언하지 않고, 테스트 코드 자체와 fixture grounding이 spec의 boundary clause를 잠그는지를 확인한다.

1. plan v1.15 §6 Rule 3 본문 + §7 정책 구조 (출력 계약, 구조적 경계, threshold path).
2. 구현 코드 (`run_rule_three`, CLI policy threading).
3. 회귀 테스트 (`test_rules.py` Rule 3 케이스, under/over-strict 가드, 경계 누락 여부).
4. Fixture grounding (`fixtures/optionality_mismatch/`, sha256 재계산, 4가지 분기 시각화).
5. 공개 envelope / schema discovery (`test_cli_output_contract.py`, `schema --command check`).

또한 `docker compose run --rm test`가 보고된 통과 수치와 일치하는지, fixture smoke check가 envelope 수치 + finding payload와 일치하는지를 실 환경에서 직접 확인한다.

## Methodology

- 모든 검증은 `docker compose` 기반 dev 환경에서 수행.
- 코드 검토는 변경 파일과 plan 본문을 line 단위로 대조. 모든 인용에 file:line 링크 부여.
- Fixture grounding은 `sha256sum`으로 manifest와 직접 재계산 대조.
- 양방향 가드는 plan §6 본문 + §7 정책 path를 한 항목씩 따라가며 테스트 함수와 fixture 분기가 그 조건을 직접 잠그는지 확인. 누락된 경계는 "Issues / Risks"에 기록.

## Findings

### 1. plan v1.15 §6 Rule 3 + §7 정책 구조

[implementation_plan_assessment_harness_poc_v1.md:645-655](../implementation_plan_assessment_harness_poc_v1.md#L645-L655) 기준.

- 조건: `requirement_level == optional`인 spec에만 trace된 `scored` rubric의 `weight >= policy.optionality_mismatch.weight_threshold` — 일치.
- 결과 / severity / decision_status: `optionality_mismatch`, `high`, `provisional` — 일치.
- next_action: `review_optionality_mismatch` — 일치.
- 차단 대상: confirmed 상태에서만 (즉 `check` 단계에서는 `blocking_count` 미가산) — 일치. 실 smoke에서 `blocking_count=0` + `provisional_high_count=2` 확인.
- 구조적 경계 (§6 line 653): semantic_status 미참조, must 혼합 → 미발화, trace 없음 → 미발화, weight < threshold → 미발화 — 모두 구현 일치.

§7 정책 path([implementation_plan_assessment_harness_poc_v1.md:799-814](../implementation_plan_assessment_harness_poc_v1.md#L799-L814))은 `rules.optionality_mismatch.weight_threshold`로 정의되며, 구현/fixture/테스트 모두 이 path를 사용. 일치.

### 2. 구현 코드

#### `run_rule_three` ([rules.py:746-808](../../src/assessment_harness/rules.py#L746-L808))

라인별 검토:

- threshold 읽기 (L757-761): `policy_doc["rules"]["optionality_mismatch"]["weight_threshold"]` — §7 path와 일치.
- L762-763: threshold가 int/float 아니면 빈 list 반환. **silent return** — 정책 누락/오타 시 finding이 그저 사라짐. 사후 검토 필요 항목(아래 Issues 참조).
- L765-769: `spec_levels` map. id가 None인 spec은 자연 제외.
- L770-774: `linked_specs_by_rubric` — 한 rubric이 여러 link를 가질 때 spec_ids를 누적 (`extend`). 정상.
- L779: `evaluation_role != "scored"`면 skip. bonus/qualitative 자연 제외 (§6 line 647 "scored rubric item" 만족).
- L781-783: 추적 없음 / weight 비숫자 / weight < threshold 시 skip — 세 경계 모두 plan §6 line 653과 일치.
- L785-787: `all(level == "optional")` — **plan §6 line 647 "optional에만"의 가장 strict한 literal 해석**. must 혼합은 당연히 skip되지만, informational 혼합도 skip된다. plan §6 line 653 본문은 "must 섞이면 미발화"만 명시했으므로 informational 케이스는 spec 본문이 명시하지 않은 경계. 아래 Issues 참조.
- finding payload에 `spec_ids`, `requirement_levels`, `weight`, `weight_threshold`를 evidence로 담음 — reviewer가 한 화면에서 정당/부당 구별 가능.

#### CLI 결합

- [cli.py:111](../../src/assessment_harness/cli.py#L111): `load_policy`로 policy_doc 로드. `--policy`가 없으면 패키지 기본 policy를 사용 (plan §7 line 858).
- [cli.py:167](../../src/assessment_harness/cli.py#L167): Rule 0 clean 직후 `run_rule_three(spec_doc, rubric_doc, trace_doc, policy_doc)` 호출.
- [cli.py:174](../../src/assessment_harness/cli.py#L174): rule_three_findings가 provisional_findings 집계에 합류.
- [cli.py:253-260](../../src/assessment_harness/cli.py#L253-L260): finding마다 `review_optionality_mismatch` next_action을 rubric_id와 함께 emit.

### 3. 회귀 테스트 — 양방향 가드

[test_rules.py:1373-1473](../../tests/test_rules.py#L1373-L1473) 기준.

| 가드 | plan §6 본문 조건 | 테스트 함수 | 합격 |
|---|---|---|---|
| under-strict | optional-only + weight == threshold + pending status → 발화 | `test_rule_three_optional_only_scored_at_threshold_emits_high_finding` (weight=10, threshold=10, pending) | ✓ |
| over-strict A | weight < threshold → 미발화 | `test_rule_three_below_threshold_does_not_emit` (weight=9) | ✓ |
| over-strict B | must 혼합 → 미발화 | `test_rule_three_must_trace_suppresses_optional_only_mismatch` (trace에 must 포함, weight=20) | ✓ |
| over-strict C | 추적 없음 → 미발화 (Rule 1 territory) | `test_rule_three_untraced_scored_rubric_is_left_to_rule_one` (trace_links 빈 list) | ✓ |

테스트 코드 자체 검증 (단순 통과 여부와 별도로):

- 모든 테스트가 finding의 type / severity / decision_status / rubric_id / evidence 중 **계약과 직결되는 surface**를 assert 함. under-strict는 evidence dict까지 완전 비교 ([test_rules.py:1421-1426](../../tests/test_rules.py#L1421-L1426)) — payload 회귀 방지.
- under-strict가 `semantic_status: pending_verification` link로 발화를 시연 ([test_rules.py:1408](../../tests/test_rules.py#L1408)) — Rule 3가 semantic_status를 참조하지 않는다는 구조적 경계를 회귀로 잠금.
- threshold 경계는 weight=10 / threshold=10 즉 `==`에서 발화함을 직접 잠금. `weight=9`로 즉시 떨어지는 over-strict A와 짝.

테스트 코드 검증 중 발견한 누락은 아래 Issues 참조.

### 4. Fixture grounding

#### `fixtures/optionality_mismatch/`

- `sha256sum source/spec.md` = `bccd845ccad807177c7f75605585bc7223ba6656fa2633324d538e9b71630bcf` — manifest와 일치.
- `sha256sum source/rubric.md` = `e75cf055291bb683065afc2fde4ec9cc1494e54acd484fe0a24b6612c2f06a56` — manifest와 일치.

4개 분기를 한 fixture에서 동시에 시각화:

| rubric | role | weight | trace 대상 | semantic_status | Rule 3 기대 | 경계 시각화 |
|---|---|---|---|---|---|---|
| R_HIGH | scored | 10 (==) | S_OPTIONAL_HIGH | human_accepted | 발화 | under-strict (threshold 경계) |
| R_LOW | scored | 9 (<) | S_OPTIONAL_LOW | human_accepted | 미발화 | over-strict A (threshold 미만) |
| R_MIXED | scored | 15 (>) | S_OPTIONAL_MIXED + S_MUST | human_accepted | 미발화 | over-strict B (must 혼합) |
| R_PENDING | scored | 12 (>) | S_OPTIONAL_PENDING | pending_verification | 발화 | structural-only (semantic_status 비참조) |

R_MIXED 덕분에 Rule 2 (S_MUST가 scored R_MIXED로 cover됨) 미발화도 동시에 시각화됨. R_PENDING은 Rule 1 `unconfirmed_trace_coverage` (medium)도 함께 emit — Rule 3 + Rule 1의 의도된 co-firing이 fixture에서 명시적으로 보임 ([test_fixtures.py:328-335](../../tests/test_fixtures.py#L328-L335)에서 둘 다 assert).

### 5. 공개 envelope / schema discovery

- [test_cli_output_contract.py:292](../../tests/test_cli_output_contract.py#L292)에 `review_optionality_mismatch`가 expected_actions set에 추가됨 — 계약 회귀 잠금.
- [cli.py:472](../../src/assessment_harness/cli.py#L472) (schema discovery 본문)에 `review_optionality_mismatch` 노출.
- 실 환경 `schema --command check` 결과: `next_actions_types`에 정확히 11개 entry, `review_optionality_mismatch` 포함 확인.

### 6. 실 환경 smoke + 전체 회귀

```text
$ docker compose run --rm test
============================= 122 passed in 1.20s ==============================
```

작업 보고에서 새 테스트 수치는 명시하지 않았지만, Rule 2 검증 시점 117 → 현재 122로 +5 (Rule 3 단위테스트 4 + fixture 테스트 1) 증가. tests 분포:

- contract: 13
- fixtures: 6 (+1)
- models: 12
- rules: 91 (+4)

```text
$ check on fixtures/optionality_mismatch
status: provisional_findings, exit: 0
(high=2, medium=1, info=0), review_queue_count=0
findings:
  unconfirmed_trace_coverage medium R_PENDING  (link_count=1, semantic_statuses=[pending_verification])
  optionality_mismatch       high   R_HIGH    (spec_ids=[S_OPTIONAL_HIGH],    weight=10, threshold=10)
  optionality_mismatch       high   R_PENDING (spec_ids=[S_OPTIONAL_PENDING], weight=12, threshold=10)
actions ⊇ {
  review_optionality_mismatch(R_HIGH),
  review_optionality_mismatch(R_PENDING),
  review_unconfirmed_trace_coverage(R_PENDING),
}
```

수치 모두 [test_fixtures.py:324-338](../../tests/test_fixtures.py#L324-L338) assert와 1:1 일치. `review_queue_count=0`은 L1/L6가 없는 fixture에서 정상 (Rule 0 clean 시 빈 queue 파일은 생성됨, plan §8 line 844와 정합).

## Issues / Risks

코드/테스트가 정본 계약과 합치하지만, 사후 검토/추가 회귀에 후보가 될 만한 항목이 셋 있다. 모두 차단 사유는 아님 — Verdict는 합격.

### Risk 1 — Plan §6 line 647의 path가 §7 정책 구조와 표기 불일치

- §6 line 647: `policy.optionality_mismatch.weight_threshold` (no `.rules` segment).
- §7 line 801: 정책 yaml은 `rules.optionality_mismatch.weight_threshold` 구조.
- 구현 ([rules.py:757-761](../../src/assessment_harness/rules.py#L757-L761))은 §7 구조와 일치.
- 영향: 코드는 정확. plan §6 본문이 path를 축약 표기한 부분은 §15 v1.15 changelog에 다시 정확한 경로로 확정되어 있어 ([implementation_plan_assessment_harness_poc_v1.md:1249](../implementation_plan_assessment_harness_poc_v1.md#L1249)) decisive하지 않지만, 향후 worker가 §6만 보고 잘못된 path를 시도할 가능성이 있음. plan §6 line 647의 표기를 `policy.rules.optionality_mismatch.weight_threshold`로 보강하면 깔끔.

### Risk 2 — 정책 누락/오타 시 silent suppress

- [rules.py:762-763](../../src/assessment_harness/rules.py#L762-L763): threshold가 int/float이 아니면 빈 list 반환. 회귀 테스트 없음.
- 시나리오: 사용자가 `policy.yaml`에서 `weight_threshold`를 오타(`threshold_weight` 등)로 입력하면 Rule 3 finding이 그냥 나오지 않음. 운영 시 "Rule 3가 안 잡는다"가 spec 오해인지 policy 오타인지 구별이 어려움.
- 권장: 정책 schema validation 단계(또는 별도 진단)에서 부재/타입 위반을 high diagnostic으로 잡거나, 본 함수가 빈 list 대신 invalid_input을 raise하도록 강화. 본 슬라이스 책임은 아니나 차후 정책 schema 슬라이스 시 같이 다룰 후보.

### Risk 3 — `informational` 혼합 케이스가 회귀 테스트/fixture에 없음

- [rules.py:786](../../src/assessment_harness/rules.py#L786): `all(level == "optional" for level in requirement_levels)`. optional + informational 혼합 trace는 발화하지 않음.
- plan §6 line 647 ("optional에만 trace된")의 literal에는 부합하지만, line 653의 본문 설명은 "must가 섞이면 미발화"만 명시 — informational 혼합이 의도된 경계인지 spec 본문만 보고는 단정 불가.
- 명시 회귀가 없어 향후 worker가 의도를 바꾸려 할 때 회귀 안전망 부재.
- 권장: 오너 확인 후 한 방향(strict optional-only 유지 / informational은 허용) 중 하나를 fixture와 테스트로 잠금. 단순 코드 변경은 아니라 spec 의사결정 필요.

### Risk 4 — bonus 역할 rubric에 대한 명시 회귀 없음

- [rules.py:779](../../src/assessment_harness/rules.py#L779)에서 `evaluation_role != "scored"`를 skip하므로 bonus가 optional-only + heavy weight여도 발화하지 않음 (구조적으로 정확).
- 단, 이 분기를 직접 잠그는 테스트가 없음. L5가 발화하는 케이스와 의도적으로 mutually exclusive함을 시각화하면 좋음 (Rule 2 검증에서 L5/L6/Rule 2 co-firing을 fixture로 잠근 패턴 차용).
- 권장: 회귀 보강 시 1줄 추가 — `_rule_three_rubric(weight=20, evaluation_role="bonus")` 케이스. 비용 작음.

## Verdict

**합격 — Rule 3 구현은 plan v1.15 §6 Rule 3 + §7 정책 구조와 정확히 일치한다.**

근거:

1. 출력 literal 두 개(`optionality_mismatch`, `review_optionality_mismatch`)가 plan / 구현 / 테스트 / schema self-discovery에 한 자리에서 잠겨 있다.
2. "구조적-only, semantic_status 미참조" 경계가 under-strict 테스트(pending_verification link로 발화)와 fixture R_PENDING 분기로 양쪽 모두 시각화되어 있다.
3. threshold 경계(weight==10 발화 / weight=9 미발화)가 fixture와 단위테스트 양쪽에서 직접 잠겨 있다. plan §6 line 647의 `>=` 의미가 fixture에서 `==`로 시연됨.
4. CLI는 정책을 정확히 threading하며, `--policy`가 없을 때도 패키지 기본 policy로 fallback (plan §7 line 858 정합).
5. 122 tests 전부 통과, fixture smoke 결과가 보고 envelope과 finding payload 모두 1:1 일치.

위 Issues / Risks는 향후 보강 후보이며 본 슬라이스 차단 사유가 아니다. Spec 본문이 명시하지 않은 boundary (informational 혼합) 또는 본 슬라이스의 책임을 벗어나는 surface (policy schema validation)에 해당함.

## Outstanding items (작업 자체와 무관, 운영 흐름)

- 본 슬라이스는 검증 시점 working tree에서 미커밋 상태이다 (`git log`의 HEAD는 `e2cdce9 Implement Rule L6 bonus-only mandatory coverage`이며 Rule 2 + Rule 3 두 슬라이스 모두 아직 커밋되지 않음).
- HANDOFF "Publication Boundary"에 Rule 2 / Rule 3가 포함되지 않은 것이 정합: owner의 독립 AI 검증 + 게시 권한 부여 단계가 다음.
- HANDOFF Next Tasks에 따라 본 슬라이스 이후 다음 진입은 `gate` 슬라이스 — `final_review.schema.json` 도착 후 진행. Phase 0 결정론적 룰 가족은 본 슬라이스로 정본 v1.15 §6의 다섯 룰(Rule 0/1/2/3, Lint L1/L5/L6)이 모두 구현 완료.

## Reproduction

본 검증을 재현하려면:

```bash
# 1. 전체 회귀
docker compose run --rm test -q

# 2. optionality_mismatch fixture smoke
docker compose run --rm harness --output json check \
  --spec-items fixtures/optionality_mismatch/spec_items.yaml \
  --rubric-items fixtures/optionality_mismatch/rubric_items.yaml \
  --trace-links fixtures/optionality_mismatch/trace_links.yaml \
  --source-manifest fixtures/optionality_mismatch/source_manifest.yaml \
  --policy fixtures/optionality_mismatch/policy.yaml \
  --out work/findings.json --diagnostics-out work/diag.json \
  --review-queue-out work/queue.json

# 3. fixture grounding
sha256sum fixtures/optionality_mismatch/source/spec.md \
          fixtures/optionality_mismatch/source/rubric.md
# manifest와 동일해야 함

# 4. schema discovery
docker compose run --rm harness --output json schema --command check
# next_actions_types에 review_optionality_mismatch 포함되어야 함

# 5. policy threading 회귀
#    fixture의 policy.yaml에서 weight_threshold를 11로 올린 뒤 재실행하면
#    R_HIGH (weight=10)이 사라지고 R_PENDING (weight=12)만 남아야 한다.
#    threshold를 9로 내리면 R_LOW (weight=9)가 추가로 발화해야 한다.
```
