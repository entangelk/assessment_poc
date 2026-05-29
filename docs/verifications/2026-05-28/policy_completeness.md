# Verification — Phase 0 Policy Completeness (plan v1.20)

- 검증 일자: 2026-05-28
- 검증 요청자: Owner — "이거 검증해줘"
- 검증 수행자: AI (Claude Code, claude-opus-4-7)
- 검증 대상: plan v1.20 `--policy` 필수화 + `rules.optionality_mismatch.weight_threshold` 완전성 가드 — working tree, uncommitted
- 정본 spec 기준: `docs/implementation_plan_assessment_harness_poc_v1.md` v1.20 §8(905-911 신설 단락) + §15 v1.20 changelog(1313-1322)
- 베이스라인: HEAD = `a56bf1e` (review draft safety guards) — 직전 [2026-05-28_review_safety_guards.md](2026-05-28_review_safety_guards.md) 합격분 위에 본 슬라이스가 올라옴.
- 닫히는 open decision: [2026-05-27_rule_3_boundary_tightening.md](2026-05-27_rule_3_boundary_tightening.md)이 별도 슬라이스로 분리했던 "Rule 3 policy completeness — missing policy yields structured invalid input". HANDOFF Open Decisions에서 항목이 실제로 제거되었음을 diff에서 확인.

## Scope

1. 계약 변경: §8 신설 단락(905-911)의 `--policy` 필수화 + threshold 완전성 요구가 자기일관적인가, 기존 §6 Rule 3 본문(threshold가 정상/위반 경계 기준)과 정합인가.
2. Spec ↔ 구현: 두 분기(`provide_policy` vs `fix_input`)가 코드에서 메시지·next_action으로 구별되는가.
3. 경계 매트릭스: contract-named 두 분기 + 회귀 무손상.
4. 회귀 무손상: 기존 check/review/gate 흐름이 깨지지 않는가 (160 passed).
5. 테스트 audit + smoke + 문서.

## Methodology

- 계약: plan v1.20 §8 905-911, §15 1313-1322 정독.
- 구현: [cli.py:103-104](../../src/assessment_harness/cli.py#L103-L104) `args.policy` 가드 + [cli.py:380-400](../../src/assessment_harness/cli.py#L380-L400) `_check_missing_policy` + [cli.py:403-412](../../src/assessment_harness/cli.py#L403-L412) `_validate_check_policy` 직접 대조.
- 회귀: 직접 실행 `pytest tests/test_cli_output_contract.py tests/test_fixtures.py` → **53 passed**, `pytest` 전체 → **160 passed**.
- **독립 재현**: validator의 모든 입력 형태(8 케이스)를 직접 실행해 outcome 일치 확인.
- Smoke: `schema --command check` (provide_policy 노출 직접 측정), gate/review schema (회귀 무손상), `git diff --check`.

## Findings

### 1. 계약 정합성 — 정합

§8 905-911가 `--source-manifest` 필수화와 같은 구조로 작성됨: argparse `required=True`를 쓰지 않고 정상 envelope으로 복구 가능하게 두는 패턴. 두 분기를 명확히 분리:
- `--policy` 인자 누락 → next_action **`provide_policy`**
- policy 파일의 `rules.optionality_mismatch.weight_threshold` 누락 → next_action **`fix_input`**

§6 Rule 3과 정합: Rule 3은 threshold로 경계 판정(`weight >= rules.optionality_mismatch.weight_threshold`)하므로 threshold 없이는 Rule 3가 발화 불가능 — 정책 누락=실리적 비활성화. v1.20은 이를 silent suppression이 아닌 structured invalid_input으로 전환. 직전 [rule_3_boundary_tightening](2026-05-27_rule_3_boundary_tightening.md)이 별도 슬라이스로 미뤘던 결정이 그 슬라이스 보고대로 닫힘. **모순 없음.**

### 2. Spec ↔ 구현 — 분기 명확히 구별

| 구현 위치 | 입력 | 출력 |
|---|---|---|
| [cli.py:103-104](../../src/assessment_harness/cli.py#L103-L104) → [cli.py:380-400](../../src/assessment_harness/cli.py#L380-L400) `_check_missing_policy` | `args.policy is None` | exit2, next_action=`provide_policy`, `"--policy is required"` |
| [cli.py:113-114](../../src/assessment_harness/cli.py#L113-L114) → [cli.py:403-412](../../src/assessment_harness/cli.py#L403-L412) `_validate_check_policy` 후 `_check_invalid_input` | policy doc에 threshold 부재 | exit2, next_action=`fix_input`, `"rules.optionality_mismatch.weight_threshold"` |

`_check_missing_policy`는 `_check_invalid_input`을 호출한 뒤 `result.envelope["next_actions"]`를 `provide_policy`로 **명시적으로 덮어쓴다** ([cli.py:391-397](../../src/assessment_harness/cli.py#L391-L397)) — 두 분기가 절대 같은 next_action으로 떨어지지 않도록 구조화.

`_validate_check_policy`는 4가지 결함 형태를 한 `or` 식으로 흡수: `rules` 누락(`get→None`), `rules` non-dict(`isinstance` false), `optionality_mismatch` 누락(`get→None`), `optionality_mismatch` non-dict, `weight_threshold` 부재. 모두 동일 메시지로 raise → 동일 envelope. 정의된 outcome("`rules.optionality_mismatch.weight_threshold` 누락 → fix_input")으로 단일 수렴.

### 3. 경계 매트릭스 — 두 명명 분기 모두 잠김

| # | 계약 분기 (§8 905-911) | 기대 | 직접실행 | 회귀 |
|---|---|---|---|---|
| 1 | `--policy` 누락 → exit2 + `provide_policy` + `"--policy is required"` | ✓ | PASS | `test_check_without_policy_returns_invalid_input` ([cli:264-303](../../tests/test_cli_output_contract.py#L264-L303)) — exit2, next=`provide_policy`, message, **추가로 findings.json 파일에도 `Rule 3` 힌트 포함 assert** |
| 2 | policy 필수 field 누락 → exit2 + `fix_input` + threshold 언급 | ✓ | PASS | `test_check_policy_missing_rule_three_threshold_returns_invalid_input` ([cli:307-349](../../tests/test_cli_output_contract.py#L307-L349)) — `{rules: {}}` 입력, exit2, next=`fix_input` (≠ provide_policy), `"rules.optionality_mismatch.weight_threshold"` in message |
| 3 | 완전한 policy → 정상 진행 | ✓ | PASS | 기존 모든 check 픽스처 테스트(clean/orphan/bonus/uncovered/optionality) 통과 |
| 4 | `schema --command check`에 `provide_policy` 노출 | ✓ | smoke PASS | `test_schema_command_returns_check_contract` ([cli:368-378](../../tests/test_cli_output_contract.py#L368-L378))이 `provide_policy`를 enumerate 목록에 포함시켜 직접 assert |
| 5 | 기존 18개 check 호출 회귀 무손상 | ✓ | 160 passed | 픽스처 헬퍼 `_run_check`가 `--policy` 동봉, `_write_minimal_grounded_fixture`도 policy.yaml 생성([cli:1484-1499](../../tests/test_cli_output_contract.py#L1484-L1499)) |

직접 재현으로 validator의 8개 입력 형태가 전부 계약대로 outcome 도출 확인:

```
PASS no --policy at all          : provide_policy
PASS policy file missing on disk : fix_input
PASS policy empty doc {}         : fix_input
PASS rules missing               : fix_input
PASS rules present empty {}      : fix_input
PASS optionality_mismatch != dict: fix_input
PASS optionality dict no threshold: fix_input
PASS complete policy             : proceeds (review_unconfirmed_trace_coverage next)
```

계약은 두 outcome만 명명(`provide_policy` / `fix_input`)하고, 4종의 결함 형태는 단일 outcome으로 수렴. 테스트가 두 명명 outcome을 message로 구별해 잠근 위에 위 매핑이 코드/probe로 검증됨.

### 4. 회귀 무손상

- `schema --command check` smoke: `status=success`, `provide_policy in next_actions_types: True`.
- `schema --command gate` / `schema --command review` smoke: 둘 다 `status=success` — 직전 합격 슬라이스 무손상.
- 53 focused / 160 full passed (a56bf1e 158 → +2 focused, +2 full... 실제는 직전 158 → +2 = 160; focused 49→53 = +4 — focused는 새 2 + 기존 1 갱신 + check_missing_input 갱신 등 추가 영향). 분포 CLI 45·fixture 8·model 12·rule 95 = 160, work_log 보고와 일치.
- `git diff --check` clean.

### 5. 테스트 audit — 두 신규 + 갱신 1건 건전

- **`test_check_without_policy_returns_invalid_input`** ([cli:264](../../tests/test_cli_output_contract.py#L264)): 인자 누락 시 exit2/`provide_policy`뿐 아니라 stdout envelope과 **findings.json 파일** 양쪽에 Rule 3 hint가 들어가는지 함께 잠금 — caller agent가 envelope만 보든 파일만 보든 동일 recovery 신호를 받음을 보장.
- **`test_check_policy_missing_rule_three_threshold_returns_invalid_input`** ([cli:307](../../tests/test_cli_output_contract.py#L307)): docstring이 "schema-valid policy without Rule 3's threshold is invalid for Phase 0 check, not an instruction to suppress Rule 3"로 의도를 명문화 — 직전 open decision의 결론을 회귀로 박음. next_action이 `fix_input`인 것을 직접 assert해 #1과 message로 구별.
- **`test_check_missing_input_returns_invalid_input`** ([cli:145+](../../tests/test_cli_output_contract.py#L145)) 갱신: `--policy`가 필수가 되었으므로 임시 policy.yaml을 추가해 원래 목적(manifest 경로 해석)을 그대로 유지. 회귀 무손상의 자연스러운 후속 갱신.
- `_write_minimal_grounded_fixture` 헬퍼에 policy.yaml 동봉 — fixture-based 회귀 일관성.

### 6. 문서

- HANDOFF Open Decisions에서 "Rule 3 policy completeness" 항목 **실제로 제거됨** ([HANDOFF.md diff line 94](../../HANDOFF.md)). Active Decisions에 `--policy is a required check input` 신규 등재. 직전 보고와 일치.
- CHANGELOG v1.20 entry 정확.
- work_log Problem/Cause/Resolution/Outcome 4-section + owner decision rationale 기록 — "generated YAML will usually be prepared by a caller AI" 같은 의사결정 근거 보존.
- README는 §8 § 909 단락이 직접 인용되는 핵심 변경이 아니므로 본 슬라이스에 큰 갱신 불요(`--source-manifest`처럼 별도 항목 추가는 향후 선택사항).

## Issues / Risks

1. **[경미] validator 내부 4결함 형태가 동일 outcome으로 수렴.** rules 누락 / rules non-dict / optionality 누락 / optionality non-dict / threshold 부재가 한 메시지로 떨어진다. 테스트는 한 입력 형태(`{rules: {}}`)만 사용. 정의된 계약 outcome("필수 field 누락 → fix_input")은 이 단일 표본으로 잠겨 있고, 직접 재현으로 8/8 통과 확인. 누군가 validator를 단순화해 일부 결함 형태가 다른 outcome으로 떨어지게 만들면 현행 테스트는 녹색일 수 있음 — **차단 아님**, 권고: parametrize 1줄로 다양한 결함 shape 잠금.
2. **[관찰] `_check_invalid_input`가 기본 next_actions에 finding-review 종류를 prefil할 수 있음.** `_check_missing_policy`는 결과의 next_actions를 통째로 덮어써 단일 `provide_policy`만 남김([cli.py:391-397](../../src/assessment_harness/cli.py#L391-L397)) — 의도된 명시적 덮어쓰기. 비대칭이 아니라 일관 — manifest 누락 경로와 같은 패턴.

## Verdict

**합격 (Pass).**

직전 [rule_3_boundary_tightening](2026-05-27_rule_3_boundary_tightening.md)이 별도 슬라이스로 분리했던 open decision이 plan v1.20 §8 신설 단락 + 양방향 named 회귀(provide_policy / fix_input message로 구별) + validator 8/8 직접 재현 + HANDOFF Open Decisions 항목 실제 제거 + 회귀 무손상으로 닫혔다. Rule 3가 조용히 비활성화되는 경로가 caller agent에게 구조화된 복구 정보(provide_policy)와 함께 차단된다.

Issue 1은 명명 outcome이 모두 잠긴 상태에서 implementation defensive depth를 추가 표본화하자는 강화 권고 — 직전 합격 라운드에서 internal_error 권고를 같은 이유로 차단 처리하지 않은 것과 동일 척도.

## Outstanding items

- 전부 working tree 미커밋. publication boundary는 owner 결정.
- 권고(Issue 1): validator 입력 shape parametrize — owner가 원하면 1 케이스 추가로 더 견고해짐. 검증자가 직접 수정하지 않음.
- Phase 1 manual real-assignment smoke 진입은 owner 판단대로 자연스러운 다음 단계.

## Reproduction

```bash
cd /workspace/assessment_poc
PYTHONPATH=src python3 -m pytest tests/test_cli_output_contract.py tests/test_fixtures.py -q   # 53 passed
PYTHONPATH=src python3 -m pytest -q                                                            # 160 passed
PYTHONPATH=src python3 -m assessment_harness.cli --output json schema --command check          # provide_policy 노출
git diff --check                                                                               # clean

# 직접 재현: validator 8개 결함 shape + 1개 정상 shape
#   1) --policy 없음            → exit2 provide_policy
#   2) 파일 없음/{}/rules 없음/{}/non-dict/threshold 없음 → exit2 fix_input
#   3) 완전한 policy            → exit0 정상 진행
```

---

## Strengthening Applied (2026-05-28, owner-authorized follow-up)

Owner가 §Issues 1 강화 권고를 진행 지시 → 본 검증자가 직접 처리.

### 변경

`test_check_policy_missing_rule_three_threshold_returns_invalid_input`을 `pytest.mark.parametrize`로 4 shape 잠금:

| id | policy doc | 도달 코드 경로 |
|---|---|---|
| `empty_doc` | `{}` | `_validate_check_policy` (rules 누락) |
| `rules_missing` | `{"other": 1}` | `_validate_check_policy` (rules 누락) |
| `rules_empty` | `{"rules": {}}` | `_validate_check_policy` (optionality 누락) |
| `threshold_missing` | `{"rules": {"optionality_mismatch": {"other": 1}}}` | `_validate_check_policy` (threshold 부재 — 계약 명명 케이스) |

4 케이스 모두 동일 outcome assert: exit2 / `fix_input` / `"rules.optionality_mismatch.weight_threshold" in input_error`.

### 강화 중 부수적 발견

본 검증 §3에서 "독립 재현 8/8 PASS"로 적었던 `optionality_mismatch != dict (string)` shape를 parametrize에 포함하자 message 분기가 다르게 떨어져 실패. 추적 결과 이 shape는 `_validate_check_policy`에 도달하지 못하고 policy **schema validation**(load_policy 내부)에서 먼저 거절되어 다른 메시지를 낸다. 직전 verification §3 probe에서 exit code와 next_action만 측정해서 같은 outcome으로 보였지만, 메시지 단위로 보면 다른 경로다.

결론: `_validate_check_policy`의 `isinstance(optionality, dict)` 분기는 실제로 **unreachable defensive guard** (정상 입력 경로로는 도달 불가, 직접 함수 호출로만 도달). parametrize에서 이 shape를 제거하고 docstring에 "shapes the policy schema already rejects are not covered here because they never reach this validator"로 명문화. 본 verification record §Issues에 별도 항목으로 surface하지 않은 이유: 동작 정확성에는 영향 없고(여전히 fix_input/exit2), 강화로 인해 코드 의도가 더 명확해진 결과이기 때문.

### 재실행

- `pytest tests/test_cli_output_contract.py tests/test_fixtures.py -q`: **56 passed** (53 → +3 parametrize 케이스)
- `pytest -q`: **163 passed** (160 → +3)
- `pytest --collect-only -k policy_missing_rule_three`: 4 ids 확인 (`empty_doc`, `rules_missing`, `rules_empty`, `threshold_missing`)
- HANDOFF Verification 카운트 동시 갱신 (160 → 163, CLI 45 → 48).

### 재검증 Verdict

**합격 (Pass) 유지.** 강화 권고가 그대로 적용되었고 부수 발견(unreachable defensive branch)은 docstring으로 보존. 코드 의도와 회귀가 더 명확해진 상태로 본 슬라이스 publication 가능.
