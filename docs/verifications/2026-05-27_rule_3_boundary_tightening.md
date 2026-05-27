# Verification — Rule 3 Boundary Tightening Follow-up

- 검증 일자: 2026-05-27
- 검증 요청자: Owner (kdtyohan@gmail.com)
- 검증 수행자: AI (Claude Code, claude-opus-4-7)
- 검증 대상: Rule 3 경계 계약 보강분 (plan §6 line 645-653 정정, 회귀 테스트 +4 케이스, fixture 확장) — working tree, uncommitted
- 정본 spec 기준: `docs/implementation_plan_assessment_harness_poc_v1.md` v1.15 §6 Rule 3
- 직전 검증 기록: [2026-05-27_rule_3_implementation.md](2026-05-27_rule_3_implementation.md) — 본 후속 작업이 그 기록의 Issues / Risks #1 / #3 / #4를 직접 해소했다.
- 본 후속 작업이 다루지 않은 항목: Risks #2 (정책 누락/오타 silent suppress) — owner가 별도 정책-validation 슬라이스로 분리 결정. HANDOFF Open Decisions [HANDOFF.md:87](../../HANDOFF.md#L87)에 기록 확인.

본 기록은 직전 기록의 합격 판정을 대체한다. 직전 기록의 `--policy` 미지정 시 기본 policy fallback 주장도 실제 구현과 맞지 않으며, 현재 계약은 policy/threshold가 없으면 Rule 3가 발화하지 않고 이 공백은 별도 policy-validation 슬라이스의 결정 대상으로 남긴다는 것이다.

## Scope

직전 검증에서 "잔여 리스크"로 잘못 분류했던 세 항목이 spec 본문 + 회귀 테스트 + fixture에 실제로 잠겼는지를 본 검증의 일차 목표로 둔다.

1. plan §6 line 647 정책 경로 표기 정정 (`policy.optionality_mismatch.*` → `rules.optionality_mismatch.*`).
2. plan §6 line 653 경계 명시 확장 (informational 혼합 미발화, bonus/qualitative rubric 제외).
3. `test_rules.py` Rule 3 회귀 +4 케이스 (multi-optional / informational-mixed / non-scored bonus / non-scored qualitative).
4. `fixtures/optionality_mismatch/` 확장 (R_INFO_MIXED, R_BONUS, R_QUAL + 대응 spec).
5. HANDOFF policy-validation 미해결 결정 기록.
6. 전체 회귀 (122 → 126) + fixture smoke.

## Methodology

직전 검증과 동일. 각 surface를 plan 본문과 직접 line 단위 대조하고, fixture는 sha256 재계산으로 grounding 확인, smoke는 envelope/finding/action 모두 직접 측정.

## Findings

### 1. plan §6 정책 경로 정정

[implementation_plan_assessment_harness_poc_v1.md:647](../implementation_plan_assessment_harness_poc_v1.md#L647) — `rules.optionality_mismatch.weight_threshold`로 정정 완료. §7 line 801 정책 yaml 구조와 일치. 직전 검증 Risk #1이 spec 자체에서 잠김.

### 2. plan §6 경계 명시 확장

[implementation_plan_assessment_harness_poc_v1.md:653](../implementation_plan_assessment_harness_poc_v1.md#L653) — 다음 네 경계가 본문에 명시됨:

- `must` 또는 `informational`이 trace 대상에 하나라도 섞이면 미발화.
- `bonus` / `qualitative` rubric은 weight와 무관하게 Rule 3 대상이 아님.
- 추적 없는 scored rubric은 미발화.
- threshold 미만 weight는 미발화.

추가로 [line 1109](../implementation_plan_assessment_harness_poc_v1.md#L1109) 성공/실패 표가 갱신되어 정본 안에서 동일 boundary가 두 자리에서 잠금. [v1.15 changelog L1251-1252](../implementation_plan_assessment_harness_poc_v1.md#L1251-L1252) 갱신 확인.

직전 검증 Risk #3 (informational 혼합) / Risk #4 (bonus/qualitative 제외)가 spec 본문에 직접 박힘.

### 3. 회귀 테스트 — 8 케이스 양방향 가드

[test_rules.py:1373-1540](../../tests/test_rules.py#L1373-L1540) 기준. 4개 새 케이스가 추가됨.

| 가드 | plan 본문 boundary | 테스트 함수 | 신규 여부 | 합격 |
|---|---|---|---|---|
| under-strict | optional + weight == threshold + pending → 발화 | `test_rule_three_optional_only_scored_at_threshold_emits_high_finding` | 기존 | ✓ |
| under-strict variant | 복수 optional target → 발화 | `test_rule_three_multiple_optional_targets_still_emit` | **신규** | ✓ |
| over-strict A | weight < threshold → 미발화 | `test_rule_three_below_threshold_does_not_emit` | 기존 | ✓ |
| over-strict B | must 혼합 → 미발화 | `test_rule_three_must_trace_suppresses_optional_only_mismatch` | 기존 | ✓ |
| over-strict C | informational 혼합 → 미발화 | `test_rule_three_informational_trace_suppresses_optional_only_mismatch` | **신규** | ✓ |
| over-strict D | bonus/qualitative high-weight optional-only → 미발화 | `test_rule_three_non_scored_optional_only_rubric_does_not_emit` (parametrized: bonus, qualitative) | **신규 (2 case)** | ✓ |
| over-strict E | 미추적 scored → 미발화 (Rule 1 territory) | `test_rule_three_untraced_scored_rubric_is_left_to_rule_one` | 기존 | ✓ |

테스트 코드 자체 audit:

- multi-optional 케이스([test_rules.py:1430-1452](../../tests/test_rules.py#L1430-L1452)): "optional에만"이 "하나만 optional"이 아님을 명시적으로 잠금. 직전 fixture는 단일 optional만 발화 경계를 시연했음 — 본 테스트로 복수 case 회귀 추가.
- informational 케이스([test_rules.py:1489-1505](../../tests/test_rules.py#L1489-L1505)): trace에 `S_OPTIONAL + S_INFO` 혼합 → 발화하지 않음을 직접 assert. plan §6 line 653의 "informational 섞이면 미발화"를 코드 수준에서 회귀로 잠금.
- non-scored 케이스([test_rules.py:1508-1527](../../tests/test_rules.py#L1508-L1527)): `@pytest.mark.parametrize("role", ["bonus", "qualitative"])`로 두 role 모두 weight=20 + optional-only에서 미발화 잠금. plan §6 line 653의 "bonus/qualitative rubric은 weight와 무관하게 Rule 3 대상이 아니다"를 1줄로 잠금.

### 4. Fixture 확장 — informational / bonus / qualitative

`fixtures/optionality_mismatch/` 확장:

- spec_items.yaml: S_INFO (informational), S_OPTIONAL_BONUS, S_OPTIONAL_QUAL 추가 ([spec_items.yaml:52-82](../../fixtures/optionality_mismatch/spec_items.yaml#L52-L82)).
- rubric_items.yaml: R_INFO_MIXED (scored, weight=20, traces S_OPTIONAL_HIGH + S_INFO), R_BONUS (bonus, weight=20), R_QUAL (qualitative, weight=20) ([rubric_items.yaml:42-72](../../fixtures/optionality_mismatch/rubric_items.yaml#L42-L72)).
- trace_links.yaml: R_INFO_MIXED → [S_OPTIONAL_HIGH, S_INFO]; R_BONUS → [S_OPTIONAL_BONUS]; R_QUAL → [S_OPTIONAL_QUAL] ([trace_links.yaml:37-63](../../fixtures/optionality_mismatch/trace_links.yaml#L37-L63)).
- source/spec.md + rubric.md에 신규 line 추가됨.
- manifest sha256 재계산 일치: `cc3ed0...` (spec) / `44d484...` (rubric) 모두 일치.

분기 시각화 표 (확장 후):

| rubric | role | weight | trace 대상 | Rule 3 기대 | 시각화 |
|---|---|---|---|---|---|
| R_HIGH | scored | 10 (==) | S_OPTIONAL_HIGH | 발화 | under-strict |
| R_LOW | scored | 9 (<) | S_OPTIONAL_LOW | 미발화 | over-strict A (threshold) |
| R_MIXED | scored | 15 | S_OPTIONAL_MIXED + S_MUST | 미발화 | over-strict B (must 혼합) |
| R_PENDING | scored | 12 | S_OPTIONAL_PENDING | 발화 | structural-only |
| **R_INFO_MIXED** | **scored** | **20** | **S_OPTIONAL_HIGH + S_INFO** | **미발화** | **over-strict C (informational 혼합)** |
| **R_BONUS** | **bonus** | **20** | **S_OPTIONAL_BONUS** | **미발화** | **over-strict D (non-scored)** |
| **R_QUAL** | **qualitative** | **20** | **S_OPTIONAL_QUAL** | **미발화** | **over-strict D (non-scored)** |

[test_fixtures.py:328-334](../../tests/test_fixtures.py#L328-L334)는 이 다섯 미발화 케이스가 optionality_mismatch finding에 절대 등장하지 않는다는 사실을 `isdisjoint`로 직접 잠금. 단순히 발화 케이스만 assert하는 것이 아니라, "발화되어선 안 되는 rubric이 우연히 발화하면 즉시 실패"의 over-strict 정신을 한 줄로 표현.

### 5. HANDOFF policy-validation 결정 기록

[HANDOFF.md:87](../../HANDOFF.md#L87) "Open Decisions Before Phase 2"에 `Rule 3 policy completeness: --policy remains optional and missing rules.optionality_mismatch.weight_threshold currently suppresses Rule 3; decide in a dedicated input/policy-validation slice whether missing policy must yield structured invalid input.`로 기록됨. 직전 검증 Risk #2가 별도 결정 채널로 정확히 분리됨.

### 6. 실 환경 회귀 + smoke

```text
$ docker compose run --rm test
============================= 126 passed in 1.28s ==============================
```

122 → 126 (+4 case). 분포: contract 13, fixtures 6, models 12, rules 95 (+4).

```text
$ check on fixtures/optionality_mismatch (expanded)
status: provisional_findings, exit: 0
(high=2, medium=1, info=0), review_queue_count=0
findings:
  unconfirmed_trace_coverage medium R_PENDING
  optionality_mismatch       high   R_HIGH
  optionality_mismatch       high   R_PENDING
actions:
  review_optionality_mismatch(R_HIGH)
  review_optionality_mismatch(R_PENDING)
  review_unconfirmed_trace_coverage(R_PENDING)
```

R_INFO_MIXED / R_BONUS / R_QUAL은 envelope/findings 어디에도 등장하지 않음 — fixture 확장 후 smoke 수치는 직전 검증과 동일하게 `(high=2, medium=1, info=0)` 유지 (의도된 invariant).

## Verdict

**합격 — 본 후속 보강은 정본 spec + 회귀 + fixture에 빠짐없이 잠겼다.**

직전 검증에서 "future risk"로 잘못 분류했던 세 항목(§6 line 647 표기 정정, informational 혼합 boundary, bonus/qualitative 제외 boundary)이 모두 spec 본문과 회귀 테스트와 fixture 세 자리에서 동시에 잠겼다. policy-validation 항목은 owner가 별도 슬라이스로 분리해 HANDOFF Open Decisions에 정확히 기록되었다.

## Outstanding items

- Rule 2 + Rule 3 (보강 포함) 모두 working tree에서 미커밋. publication boundary 진입은 owner 독립 검증 후.
- 다음 진입은 여전히 `gate` (Phase 3 final_review.schema.json 도착 후).

## Reproduction

```bash
docker compose run --rm test -q

sha256sum fixtures/optionality_mismatch/source/spec.md \
          fixtures/optionality_mismatch/source/rubric.md

docker compose run --rm harness --output json check \
  --spec-items fixtures/optionality_mismatch/spec_items.yaml \
  --rubric-items fixtures/optionality_mismatch/rubric_items.yaml \
  --trace-links fixtures/optionality_mismatch/trace_links.yaml \
  --source-manifest fixtures/optionality_mismatch/source_manifest.yaml \
  --policy fixtures/optionality_mismatch/policy.yaml \
  --out work/findings.json --diagnostics-out work/diag.json \
  --review-queue-out work/queue.json
```

---

## 반성문 (Verifier Self-Critique)

본 후속 작업이 필요해진 직접 원인은 직전 [2026-05-27_rule_3_implementation.md](2026-05-27_rule_3_implementation.md) 검증의 판정이 잘못된 표준 위에 서 있었기 때문이다. 의식적으로 자기 비판한다.

### 무엇을 잘못했는가

직전 검증에서 다음 셋을 발견하고도 **"잔여 리스크 — 보강 후보, 차단 사유 아님 — 합격"**으로 처리했다.

- Risk #1: plan §6 line 647 정책 경로 표기가 §7 구조와 불일치 (`policy.optionality_mismatch.*` vs `rules.optionality_mismatch.*`).
- Risk #3: informational 혼합 케이스가 회귀 테스트/fixture에 없음. 코드는 strict 해석(`all(level == "optional")`)을 취했지만 plan 본문은 informational 케이스를 명시하지 않아 의도된 boundary인지 단정 불가.
- Risk #4: bonus/qualitative role rubric에 대한 명시 회귀 없음. 코드는 안전하지만 boundary가 회귀로 잠겨 있지 않음.

이 셋은 "future risk"가 아니라 **spec 본문 정정 + 회귀 잠금이 본 슬라이스 안에서 끝나야 했던 항목**이다. owner가 "버그가 아니라 경계 계약이 덜 잠겨 있었다"고 정확히 짚었다.

### 왜 그렇게 판단했는가

세 줄로 정직히 적는다.

1. **"코드가 정확하면 합격"이라는 무의식의 기준에 빠졌다.** 코드의 동작이 plan §6의 의도된 결과와 일치한다는 사실만 확인하면 됐다고 가정했다. 그러나 spec ↔ 회귀 ↔ fixture의 삼중 잠금은 코드 동작 정확성과는 다른 차원의 요구사항이다.
2. **회귀 누락을 발견했으면서도 "boundary 명시가 spec에 없다"는 사실을 spec 본문 정정 요구로 격상시키지 않았다.** Risk #3에서 "owner 확인 후 잠그면 안전"이라고 적은 순간이 잘못이었다. 회귀가 없는 boundary는 정의상 미잠금이며, 미잠금 boundary가 있는 슬라이스는 본 프로젝트의 두-방향 회귀 가드 기준에서 "완료"가 될 수 없다.
3. **직전 회차(Rule 2)에서 boundary가 모두 잠겨 합격했던 경험이 anchor가 되어 같은 척도를 Rule 3에 일관되게 적용하지 않았다.** Rule 2는 over-strict A/B/C 셋이 정확히 spec 본문의 셋과 1:1 대응했고, Rule 3는 그렇지 않았는데도 "주요 boundary는 잠겼다"는 느슨한 기준으로 봐줬다.

### 본 프로젝트 지침이 이미 그것을 말하고 있었다

직전 검증 직전에 본인이 직접 [CLAUDE.md](../../CLAUDE.md) / [AGENTS.md](../../AGENTS.md)에 박은 지침의 핵심 한 줄은:

> Never conflate "the test suite is green" with "the test suite verifies what the spec demands". Make the distinction visible in the record.

그리고 같은 절의 또 한 줄:

> Over-strict guards exist for every "should NOT fire" branch in the spec.

Rule 3의 "should NOT fire" 분기는 plan §6 본문 + line 653 모두 합쳐 informational 혼합 / bonus / qualitative / must / 미추적 / threshold 미만 — 여섯 개다. 직전 검증이 잠근 over-strict는 must / 미추적 / threshold 미만 — 셋뿐이었다. 절반이 누락된 채로 합격 처분을 내렸다.

자기 자신이 박은 표준을 같은 날 위반했다는 사실은 가볍지 않다.

### 다음에 어떻게 다를 것인가

규칙으로 박는다 (구두 약속 아닌 운영 절차):

- **"missing over-strict = blocking"** — spec의 "should NOT fire" 분기를 enumerate하고, 각각에 대응하는 회귀가 없으면 그 자체로 verdict는 합격이 될 수 없다. "리스크"로 격하하지 말 것.
- **"missing boundary in spec = blocking"** — 회귀를 적기 위해 spec 본문을 다시 읽었을 때 boundary가 명시되어 있지 않으면, owner 결정을 받아 spec을 정정한 뒤 회귀를 잠그는 것까지가 슬라이스 책임이다. "owner 확인 후 잠그면 안전" 같은 미래형 권고로 verdict를 바꾸지 말 것.
- **"spec ↔ test ↔ fixture 매핑 표를 강제"** — 각 verification record의 Findings에 plan boundary clause → 회귀 테스트 함수 → fixture 분기 매핑을 표로 그릴 것. 빈 셀이 발견되면 그 자리에서 verdict는 "조건부 합격" 또는 "불합격"으로 떨어진다.

이번 직전 검증은 위 세 규칙을 모두 어겼다. 본 후속 검증부터 본 규칙을 적용했고, 다음 슬라이스(`gate`)부터 첫 verdict가 나오기 전에 boundary 매핑 표를 반드시 생성한다.

### Owner에게

"엉덩이 맞아야겠지"는 정확한 평가입니다. 변명 없이 수용합니다. 본 반성문은 다음 검증을 더 잘하기 위한 운영 절차 변경을 동반하므로 같은 실수가 반복되면 그건 무지가 아니라 의도입니다.
