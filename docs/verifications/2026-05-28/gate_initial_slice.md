# Verification — Initial `gate` Slice & Final-Review Finding Mapping (plan v1.16)

- 검증 일자: 2026-05-28
- 검증 요청자: Owner (kdtyohan@gmail.com)
- 검증 수행자: AI (Claude Code, claude-opus-4-7)
- 검증 대상: plan v1.16 final-review→finding 매핑 계약 + `gate` 첫 수직 조각 (schema, `gate` 명령, CLI 계약/fixture 회귀) — working tree, uncommitted
- 정본 spec 기준: `docs/implementation_plan_assessment_harness_poc_v1.md` v1.16 §5.5 / §5.6 / §6 Rule 1·2·3·L1·L5·L6 / §8.1
- 검증 대상 작업 출처: working tree, uncommitted (git status: `M cli.py, schemas.py, test_cli_output_contract.py, test_fixtures.py, plan, README, HANDOFF, CHANGELOG`; `?? schemas/final_review.schema.json, docs/daily_logs/2026-05-28/`)
- 직전 검증 기록: [2026-05-27_rule_3_boundary_tightening.md](2026-05-27_rule_3_boundary_tightening.md) — 그 기록의 자기비판(§반성문)이 본 검증에 적용할 표준을 명시한다: "missing over-strict = blocking", "spec↔test↔fixture 매핑 표 강제, 빈 셀이 발견되면 verdict는 조건부 합격 또는 불합격". 본 검증은 `gate` 첫 verdict 전에 boundary 매핑 표를 먼저 만들겠다는 그 약속을 그대로 이행한다.

## Scope

검증 surface:

1. **계약 자기일관성** — plan v1.16 §5.6 finding-key 표 + §6 각 Rule의 severity/blocking 위상 + §8.1 exit code가 서로 모순 없는가.
2. **Spec ↔ 구현 리터럴 일치** — finding type 문자열, target_key 필드, blocking 집합, exit code, status 문자열이 코드에 paraphrase 없이 그대로 나타나는가.
3. **경계 매트릭스 (lock list)** — §5.6/§6의 모든 "should fire" / "should NOT fire" 분기가 named 회귀 테스트에 매핑되는가. 빈 셀 적출.
4. **테스트 코드 audit** — 각 신규 테스트가 계약 절을 실제로 잠그는가 (under/over-strict 양방향, 공개 surface assert).
5. **Fixture grounding** — `orphan_scored_rubric` E2E 경로가 실제 check 산출물에서 동작하는가.
6. **Schema 자기발견 + smoke** — `schema --command gate` introspection과 envelope 수치 직접 재측정.
7. **문서 정합성** — README/HANDOFF/CHANGELOG/work_log 주장이 구현과 일치하는가.

## Methodology

- 계약: plan v1.16 §5.5(424-440), §5.6(442-543, 특히 신규 499-533), §6 Rule 1·2·3·L1·L5·L6(659-757), §8.1(900-958) 전 구간 정독. finding type별 severity/blocking 위상을 §6에서 직접 재도출해 §5.6 blocking 집합과 대조.
- 구현: [cli.py:589-870](../../src/assessment_harness/cli.py#L589-L870) `_cmd_gate` 및 보조 함수 직접 대조. [final_review.schema.json](../../schemas/final_review.schema.json) draft 2020-12 구조 확인.
- 회귀: `PYTHONPATH=src python3 -m pytest tests/test_cli_output_contract.py tests/test_fixtures.py -q` (27 passed) 및 `python3 -m pytest -q` (134 passed) 직접 실행.
- **미테스트 분기 독립 재현**: 회귀가 잠그지 않은 계약 분기 9개를 임시 입력으로 직접 `gate` 실행해 exit/status를 측정(아래 Findings §3 표 "직접실행" 열). 코드 동작 정확성과 회귀 잠금 여부를 분리해 판정.
- Smoke: `PYTHONPATH=src python3 -m assessment_harness.cli --output json schema --command gate` 직접 실행.
- 필드명 grounding: check가 emit하는 Finding 필드([rules.py:50-67](../../src/assessment_harness/rules.py#L50-L67) 및 각 finding 생성부)와 `FINDING_KEY_FIELDS`([cli.py:595-611](../../src/assessment_harness/cli.py#L595-L611)) 1:1 대조.

## Findings

### 1. 계약 자기일관성 — 모순 없음

§5.6 finding-key 표(507-516)의 8개 type, §6 각 Rule의 결과 type/severity, §5.6 blocking 집합(530-533)을 교차 대조:

| finding type | §6 Rule / severity | §5.6 blocking(confirmed) | accept 시 거동 |
|---|---|---|---|
| `possible_orphan_scored_rubric_item` | R1 / high prov | → 승급 `orphan_scored_rubric_item` blocking | 승급(530-533, 664) |
| `unconfirmed_trace_coverage` | R1 / medium prov | → 승급 `orphan_scored_rubric_item` blocking | 승급(524-526) |
| `orphan_bonus_rubric_item` | R1 / informational | 비차단(668) | confirm only |
| `uncovered_must_spec_item` | R2 / medium | 비차단(532) | confirm only |
| `optionality_mismatch` | R3 / high | **blocking**(531) | confirm→fail |
| `double_scored_spec` | L1 / medium | 비차단(532) | confirm only |
| `bonus_grades_mandatory_only` | L5 / medium | 비차단(532) | confirm only |
| `mandatory_spec_bonus_only_traced` | L6 / high | **blocking**(531) | confirm→fail |

blocking 집합 = {`orphan_scored_rubric_item`(R1 승급형), `optionality_mismatch`(R3), `mandatory_spec_bonus_only_traced`(L6)}. §6의 "차단 대상: confirmed에서만 예"(666, 690-691, 738)와 정합. Rule 2/L1/L5의 "차단 아니오"(680, 703, 721)와도 정합. **내부 모순 없음.**

### 2. Spec ↔ 구현 리터럴 일치 — 일치

- `FINDING_KEY_FIELDS` ([cli.py:595-611](../../src/assessment_harness/cli.py#L595-L611)) 8개 항목이 §5.6 표(507-516)와 type·필드 모두 정확히 일치. `double_scored_spec`만 4-필드(`type, spec_id, scored_rubric_id, bonus_rubric_id`)인 것까지 일치.
- `BLOCKING_CONFIRMED_FINDING_TYPES` ([cli.py:589-593](../../src/assessment_harness/cli.py#L589-L593)) = §5.6 blocking 집합(531)과 3개 정확히 일치.
- 승급 로직 [cli.py:664-688](../../src/assessment_harness/cli.py#L664-L688): `possible_orphan_scored_rubric_item`/`unconfirmed_trace_coverage` → type `orphan_scored_rubric_item`, severity `high`, `decision_status` `confirmed`. §6 line 664 / §5.6 524-526과 일치.
- exit code: pending→0([cli.py:814](../../src/assessment_harness/cli.py#L814)), fail→1([cli.py:840](../../src/assessment_harness/cli.py#L840)), invalid_input→2([cli.py:701-715](../../src/assessment_harness/cli.py#L701-L715)). §8.1(900-958) 및 §5.6(521-522)과 일치.
- **필드명 grounding (silent-mismatch 위험 점검)**: check가 emit하는 Finding 필드가 key 필드와 어긋나면 매칭이 조용히 실패한다. [rules.py:50-67](../../src/assessment_harness/rules.py#L50-L67)의 `to_dict`와 각 생성부(657/675/638/730/788/848/948/1029) 대조 결과 8개 type 모두 key 필드를 top-level로 보유 — `_finding_key`([cli.py:619-633](../../src/assessment_harness/cli.py#L619-L633))가 canonical 필드만 추출하므로 `optionality_mismatch`/`mandatory_spec_bonus_only_traced`의 추가 `evidence`/`bonus_rubric_ids`는 key에서 무시됨. **매칭 silent-fail 위험 없음.**

### 3. 경계 매트릭스 — **빈 셀 다수 (핵심 finding)**

§5.6/§6의 분기를 lock list로 펼치고 회귀 테스트 매핑. "직접실행"은 본 검증이 임시 입력으로 직접 측정한 결과(코드 거동), "회귀 잠금"은 named 테스트 존재 여부.

| # | 계약 분기 (조항) | 기대 | 직접실행 | 회귀 잠금 테스트 |
|---|---|---|---|---|
| 1 | accept R1 possible_orphan → 승급 blocking (664) | exit1 fail | ✓ | `test_gate_closes_orphan_scored_fixture...` (fixtures:310) |
| 2 | accept R1 unconfirmed_trace → 승급 blocking (524) | exit1 fail | ✓ | `test_gate_accept_promotes_rule_one...` (cli:412) |
| 3 | accept R3 optionality → confirm blocking (531) | exit1 fail | ✓ PASS | **없음 (override만 잠김)** |
| 4 | accept L6 mandatory_bonus_only → confirm blocking (531) | exit1 fail | ✓ PASS | **없음** |
| 5 | accept R2 uncovered_must → 비차단 success (532) | exit0 success | ✓ | `test_gate_accepts_nonblocking...` (cli:504) |
| 6 | accept L1 double_scored → 비차단 success (532) | exit0 success | ✓ PASS | **없음** |
| 7 | accept L5 bonus_grades → 비차단 success (532) | exit0 success | ✓ PASS | **없음** |
| 8 | override → dismissed 비차단 (527) | exit0 success | ✓ | `test_gate_override_dismisses...` (cli:460) |
| 9 | missing decision → pending (521) | exit0 pending | ✓ | `test_gate_missing_finding_decision...` (cli:380) |
| 10 | `hold` → pending (522, 527) | exit0 pending | ✓ PASS | **없음** |
| 11 | `rerun_requested` → pending (522, 527) | exit0 pending | ✓ PASS | **없음** |
| 12 | stale decision (no match) → invalid (519,781) | exit2 invalid | ✓ | `test_gate_rejects_stale...` (cli:546) |
| 13 | 중복 decision → invalid (519,775) | exit2 invalid | ✓ PASS | **없음** |
| 14 | non-minimal key: payload 필드 → invalid (500,768) | exit2 invalid | ✓ | `test_gate_rejects_non_minimal...` (cli:573) |
| 15 | non-minimal key: 필수 필드 누락 → invalid (768) | exit2 invalid | ✓ PASS | **없음** |
| 16 | unknown finding type → invalid (647-648) | exit2 invalid | ✓ PASS | **없음** |
| 17 | final_review schema invalid → invalid (722-724) | exit2 invalid | — | **없음** |
| 18 | findings.json 읽기 실패 → invalid (729-734) | exit2 invalid | — | **없음** |
| 19 | findings.json schema invalid → invalid (736-742) | exit2 invalid | — | **없음** |
| 20 | findings.json 내부 key 중복 → invalid (749-753) | exit2 invalid | — | **없음** (+계약 silent, 아래 §Issues) |

직접실행 9건(#3,4,6,7,10,11,13,15,16) 전부 계약과 일치 — **코드 거동은 전 분기 정확**. 그러나 회귀가 잠그지 않은 계약 분기가 **11개** (#3,4,6,7,10,11,13,15,16,17,18,19,20 중 named 테스트 없는 것). 특히:

- **blocking 집합 under-strict 미잠금**: blocking 3종 중 직접 confirm 경로(승급 아님)인 #3 optionality / #4 L6가 fail로 잠겨 있지 않다. `BLOCKING_CONFIRMED_FINDING_TYPES`에서 둘 중 하나를 제거해도 현행 스위트는 녹색이다. (#1/#2는 승급형 `orphan_scored_rubric_item`만 잠금.)
- **"비차단" 명시 분기 미잠금**: §5.6 532는 "Rule 2/L1/L5 confirmed는 exit1 아님"을 명시한다. 셋 중 R2(#5)만 잠겼고 L1(#6)/L5(#7)는 미잠금. L1을 실수로 blocking 집합에 넣어도(over-block) 스위트는 녹색.
- **계약이 명시적으로 이름 붙인 분기 미잠금**: `hold`/`rerun_requested`(522,527)와 중복 decision(519)은 계약 본문이 직접 호명한 분기인데 회귀 없음.

직전 검증 자기비판이 박은 규칙("missing over-strict = blocking … 빈 셀이면 verdict는 조건부 합격 또는 불합격") 그대로, 이 빈 셀들은 차단 사유다.

### 4. 테스트 코드 audit — 잠긴 7개는 건전

- 모든 gate 테스트가 `_assert_envelope`([test_cli...:29-33](../../tests/test_cli_output_contract.py#L29-L33)) 또는 `validate("cli_output", ...)`로 공개 envelope을 cli_output schema에 대해 검증 — 내부 헬퍼가 아닌 caller-소비 surface를 assert. 적합.
- `test_gate_accept_promotes_rule_one...`([cli:412-458](../../tests/test_cli_output_contract.py#L412-L458)): finding payload에 `message`/`evidence`를 넣어두고 target_key는 `{type, rubric_id}`만으로 승급을 끌어냄 — "최소 key로 payload 복사 없이 식별" under-strict를 정확히 잠금. 승급 결과 type/severity/decision_status 3개 모두 assert.
- `test_gate_override_dismisses...`([cli:460-502](../../tests/test_cli_output_contract.py#L460-L502)): optionality_mismatch override → success, `dismissed_finding_count==1` — over-strict(검토된 override가 차단하지 않음) 잠금.
- `test_gate_rejects_non_minimal...`([cli:573-616](../../tests/test_cli_output_contract.py#L573-L616)): `message` 복사본 주입 → exit2 + `"not minimal"` — payload-copy 거절 잠금.
- fixture E2E([test_fixtures.py:310-381](../../tests/test_fixtures.py#L310-L381)): check 산출 findings 집합을 `{possible_orphan, unconfirmed_trace, orphan_bonus}`로 먼저 assert한 뒤 R2 accept / R1·R3 override → exit1, `(blocking=1, confirmed=1, dismissed=2)` 직접 잠금. 본 검증이 동일 수치 재현(아래 §6).
- 단, §3에서 적출한 빈 셀들은 테스트 코드 건전성과 무관하게 **존재하지 않는 테스트**의 문제다.

### 5. Fixture grounding — 동작 확인

`orphan_scored_rubric` fixture로 check→final_review→gate E2E가 실제로 도는 것을 회귀 + 직접 재현 모두 확인(§6). check가 medium `unconfirmed_trace_coverage`(R1)와 informational `orphan_bonus`(R3)를 함께 내고, gate가 R2 accept를 high confirmed `orphan_scored_rubric_item`로 승급, 나머지 override→dismissed 처리. fixture source manifest sha 재계산은 본 슬라이스가 fixture 본문을 수정하지 않았으므로 직전 검증 결과를 승계(별도 재계산 불요).

### 6. Schema 자기발견 + smoke — 일치

```
$ PYTHONPATH=src python3 -m assessment_harness.cli --output json schema --command gate
status success
next ['complete_final_review', 'fix_final_review', 'revise_assessment']
exit1 "confirmed blocking finding exists after final review."
```

`schema --command gate`가 next_actions 3종과 exit code 설명을 노출 — 코드의 `COMMAND_CONTRACTS["gate"]`([cli.py:494-517](../../src/assessment_harness/cli.py#L494-L517))와 일치. work_log가 보고한 fixture 수치 `(blocking_count=1, confirmed=1, dismissed=2)`를 pytest 재실행으로 직접 확인(불일치 없음).

### 7. 문서 정합성 — 일치

CHANGELOG v1.16 항목, HANDOFF "Initial finding-level `gate` is implemented", README 갱신 모두 구현/테스트와 일치. HANDOFF가 인용한 fixture 수치(blocking=1, confirmed=1, dismissed=2)는 §6에서 재현 확인. work_log의 "27/134 통과", "schema smoke" 주장 모두 재현됨.

## Issues / Risks

1. **[차단] 경계 매트릭스 빈 셀 11개** (§3 표). 코드 거동은 직접실행으로 전부 정확함을 확인했으나, 다음 계약 분기가 named 회귀로 잠겨 있지 않다:
   - blocking 직접-confirm 경로: `optionality_mismatch` accept→fail(#3), `mandatory_spec_bonus_only_traced` accept→fail(#4) — **under-strict 가드 부재**.
   - 비차단 명시 분기: `double_scored_spec`(#6), `bonus_grades_mandatory_only`(#7) accept→success — **over-block 회귀 부재**.
   - 계약이 호명한 분기: `hold`/`rerun_requested`→pending(#10,11), 중복 decision→invalid(#13).
   - key 검증 분기: 필수 필드 누락(#15), unknown type(#16).
   - 입력 무결성: final_review schema invalid(#17), findings 읽기 실패(#18), findings schema invalid(#19), findings 내부 key 중복(#20).
2. **[계약 gap, 경미] findings.json 내부 key 중복 거절이 spec-silent** ([cli.py:749-753](../../src/assessment_harness/cli.py#L749-L753)). §5.6은 *decision* 중복만 invalid로 규정(519). check가 같은 canonical key를 두 번 emit할 일은 없어 방어적 코드이나, 계약이 침묵하는 거절이므로 §5.6에 한 줄 명문화하거나 제거 판단 필요.
3. **[단순성, 경미] `gate --policy` 인자 미사용** ([cli.py:986](../../src/assessment_harness/cli.py#L986)). `_cmd_gate`는 policy를 읽지 않는다(gate는 규칙을 돌리지 않음). CLAUDE.md §2(투기적 코드 금지) 위반 소지 — 제거 또는 향후 용도 명문화 권장.
4. **[설계 관찰, 비차단] 모든 provisional finding이 decision을 받아야 success 도달.** informational `orphan_bonus_rubric_item`조차 미결정 시 pending(521 "아직 decision이 없는 provisional finding은 최종 판정을 닫을 수 없다"). 계약 본문과 일치하며 fixture가 이를 override로 시연 — 의도된 거동으로 판단, 결함 아님.

## Verdict

> **2026-05-28 후속 재검증으로 합격 승급.** 아래 조건부 합격은 plan v1.17 보강 전 1차 판정이다. 보강 결과는 본 문서 말미 [§Remediation Re-verification](#remediation-re-verification-2026-05-28-plan-v117)를 참조.

**조건부 합격 (Conditional Pass).**

근거:
- **합격 측면**: 계약 자기일관성(§1), spec↔구현 리터럴 일치(§2, 필드명 silent-mismatch 위험 포함), 잠긴 7개 테스트의 건전성(§4), fixture/smoke 수치 재현(§5,6), 문서 정합(§7) 모두 통과. 회귀 미잠금 분기 9개를 본 검증이 직접 실행한 결과 **코드 거동은 전 분기 계약과 일치** — 알려진 동작 결함 없음.
- **조건(차단 해소 요건)**: §3의 빈 셀 중 최소한 계약이 명시적으로 호명한 분기 — `optionality_mismatch`/`mandatory_spec_bonus_only_traced` accept→fail (#3,#4), L1/L5 accept→비차단 (#6,#7), `hold`/`rerun_requested`→pending (#10,#11), 중복 decision→invalid (#13) — 에 대응하는 named 회귀를 추가해야 합격으로 승급한다. 입력 무결성(#17–19)과 key 검증(#15,16) 분기도 함께 잠그길 권고한다.

직전 검증 자기비판이 박은 규칙("missing over-strict = blocking", "빈 셀이면 조건부 합격/불합격")을 본 슬라이스에 일관 적용한 결과다. 코드가 정확하다는 사실만으로 "합격 with risks"로 처분하지 않는다 — 그것이 그 반성문이 금지한 정확한 실패 양식이다.

## Outstanding items

- 본 슬라이스 전부 working tree에서 미커밋. publication boundary 진입은 owner 결정 사항.
- §Issues 1의 회귀 보강은 본 검증이 직접 수정하지 않는다(검증자는 결함을 발견·보고하고 owner가 다음 조치를 결정). owner가 보강을 지시하면 별도 작업으로 잠근 뒤 재검증.
- §Issues 2(계약 silent), 3(`--policy` 미사용)은 owner 판단 대기.

## Reproduction

```bash
cd /workspace/assessment_poc

# 회귀
PYTHONPATH=src python3 -m pytest tests/test_cli_output_contract.py tests/test_fixtures.py -q
PYTHONPATH=src python3 -m pytest -q

# schema 자기발견
PYTHONPATH=src python3 -m assessment_harness.cli --output json schema --command gate

# 미테스트 분기 직접 재현: 임시 findings.json + final_review.yaml 작성 후
#   gate --final-review <review.yaml> 실행, exit/status 측정.
#   확인 분기: hold/rerun→pending(0), 중복/unknown/필드누락→invalid(2),
#   optionality/L6 accept→fail(1), L1/L5 accept→success(0).
```

---

## Remediation Re-verification (2026-05-28, plan v1.17)

- 재검증 요청자: Owner — "보강 완료 되었는지 검증해줘"
- 재검증 대상: 1차 조건부 합격의 차단 사유(§3 빈 셀 11개 + §Issues 2·3)를 닫는 보강분 — working tree, uncommitted
- 정본: plan **v1.17** §5.6 / §15 v1.17 changelog

### 무엇이 바뀌었나 (직접 확인)

1. **plan v1.17 승급 + §5.6 명문화** ([plan:514-518](../implementation_plan_assessment_harness_poc_v1.md#L514-L518)): `findings.json` 내부 같은 canonical key 중복을 `invalid_input`/exit `2`로 명문화 — 1차 Issue 2(spec-silent) 해소. v1.16/v1.17 changelog 추가([plan:1283-1299](../implementation_plan_assessment_harness_poc_v1.md#L1283-L1299)).
2. **투기적 `gate --policy` 제거** — Issue 3 해소: cli.py 파서에서 제거([cli.py](../../src/assessment_harness/cli.py)에 `gate --policy` 부재, `check --policy`만 잔존), plan 예시 2곳(171·1014 부근) 및 README에서 삭제. 잔존 언급은 v1.17 changelog의 "제거함" 설명 1곳뿐.
3. **회귀 +13 케이스** — `check`/`schema`/`report`/`gate` 행위 불변(cli.py gate 로직 미수정, `--policy` 1줄만 제거).

### 경계 매트릭스 — 빈 셀 0 (재확인)

1차 §3에서 적출한 빈 셀이 모두 named·건전 회귀로 잠겼다. 핵심 가드 건전성 직접 audit:

| 1차 빈 셀 | 보강 테스트 | 가드 방향 건전성 |
|---|---|---|
| #3 optionality accept→fail / #4 L6 accept→fail | `test_gate_accepts_direct_blocking_findings_with_exit_one` ([cli:604-645](../../tests/test_cli_output_contract.py#L604-L645)) | **parametrize 2종**, `blocking_findings[0]["type"]==finding["type"]` + `blocking_count==1` assert. blocking 집합에서 둘 중 하나 제거 시 즉시 실패 — 진짜 under-strict |
| #6 L1 / #7 L5 accept→nonblocking | `test_gate_accepts_l1_l5_as_confirmed_nonblocking_findings` ([cli:647-688](../../tests/test_cli_output_contract.py#L647-L688)) | **parametrize 2종**, `blocking_count==0` + success assert. 둘 중 하나를 blocking에 잘못 넣으면 실패 — 진짜 over-block 가드 |
| #10 hold / #11 rerun → pending | `test_gate_hold_and_rerun_requested_keep_pending_review` ([cli:691-709](../../tests/test_cli_output_contract.py#L691-L709)) | **parametrize 2종**, blocking이 될 `optionality_mismatch`에 hold/rerun을 걸어 short-circuit 증명 |
| #13 중복 decision | `test_gate_rejects_duplicate_finding_decisions` (cli:739) | `"duplicate decisions" in input_error` |
| #15 필드 누락 / #16 unknown type | cli:798 / cli:812 | exit2 + `"not minimal"` |
| #17 final_review schema invalid | cli:826 (`inputs:{}`로 required `findings_path` 누락) | exit2 invalid |
| #18 findings 파일 부재 / #19 findings schema invalid | cli:851 / cli:865 | `"cannot read findings"` / `"schema validation failed"` |
| #20 findings 내부 중복 key | `test_gate_rejects_duplicate_finding_keys_in_findings_input` (cli:897) | `"duplicate gate target keys"` — §5.6 신규 계약 잠금 |

### 실 환경 재현

```
$ PYTHONPATH=src python3 -m pytest -q        →  147 passed (1차 134 → +13)
$ PYTHONPATH=src python3 -m pytest -k gate    →  20 passed (parametrize 전개 포함)
```

+13 분포: direct_blocking ×2, l1_l5 ×2, hold/rerun ×2, duplicate_decision/missing_field/unknown_type/invalid_final_review_schema/missing_findings_file/invalid_findings_schema/duplicate_finding_keys 각 1 = 13. 정확히 일치. gate 로직 무변경 재확인 위해 1차 직접실행 9분기 재측정 — 9/9 계약 일치 유지.

### 재검증 Verdict

**합격 (Pass).** 1차 조건부 합격의 차단 사유(경계 매트릭스 빈 셀 11개, Issue 2 spec-silent, Issue 3 투기 인자)가 spec·회귀·문서 세 자리에서 모두 닫혔다. blocking 3종·nonblocking 3종이 각각 under-strict/over-block 양방향으로 잠겼고, 입력 무결성 분기 전부 named 회귀로 잠겼다. 잔여 Issue 4(모든 provisional이 decision을 받아야 success 도달)는 1차에서 계약 일치·의도된 거동으로 판정했으므로 차단 아님.

### 재검증 Outstanding

- 전부 working tree 미커밋. publication boundary 진입은 owner 결정.
- final_review.schema.json은 minimal-key를 강제하지 않고 코드가 강제하는 설계 유지(계약 명시) — 다음 슬라이스 `review` 명령 도착 시 동일 계약 위에서 구성.
