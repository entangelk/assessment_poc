# Verification — `review` Draft Writer Slice (plan v1.18)

- 검증 일자: 2026-05-28
- 검증 요청자: Owner — "또 의심하고 검증해줘봐"
- 검증 수행자: AI (Claude Code, claude-opus-4-7)
- 검증 대상: plan v1.18 `review` draft writer 계약 + `review` 명령 구현 + 회귀/fixture — working tree, uncommitted
- 정본 spec 기준: `docs/implementation_plan_assessment_harness_poc_v1.md` v1.18 §5.6 (review draft writer 규칙, 534-547) + §15 v1.18 changelog + §5.6 canonical `target_key` 표(507-516, gate 슬라이스와 공유)
- 검증 대상 작업 출처: working tree, uncommitted. 베이스라인 HEAD = `0c89845` (gate 슬라이스 커밋, final_review.schema.json + [2026-05-28_gate_initial_slice.md](2026-05-28_gate_initial_slice.md) 포함).
- 직전 검증 기록: [2026-05-28_gate_initial_slice.md](2026-05-28_gate_initial_slice.md) — 그 기록(및 그 안의 자기비판)이 확정한 표준을 본 검증에 그대로 적용한다: "계약이 호명한 분기는 named 회귀로 잠겨야 하고, 빈 셀이면 verdict는 조건부 합격 또는 불합격."

## Scope

1. **계약 자기일관성** — v1.18 review 규칙이 gate 계약(canonical key, hold→pending)과 모순 없는가.
2. **Spec ↔ 구현** — review가 §5.6 canonical key만 emit하는가, payload 미복사, hold 고정, unknown/누락 거절.
3. **Round-trip 정확성 (핵심)** — review 출력 `target_key`가 gate의 최소-key 검사(`required == actual` exact-match)와 매칭 검사를 모두 통과하는가. 8개 finding type 전부.
4. **경계 매트릭스** — §5.6 review 분기의 "should fire" / "should NOT fire" 가 named 회귀에 매핑되는가. 빈 셀 적출.
5. **테스트 코드 audit** — 각 테스트가 계약을 실제로 잠그는가 (payload 미복사 over-strict, round-trip 공개 surface).
6. **Smoke + 문서 정합.**

## Methodology

- 계약: plan v1.18 §5.6 534-547 정독, §5.6 canonical 표(507-516)와 대조.
- 구현: [cli.py:601-682](../../src/assessment_harness/cli.py#L601-L682) `_cmd_review`/`_review_target_key_for_finding` 직접 대조. `FINDING_KEY_FIELDS`([cli.py:595-611](../../src/assessment_harness/cli.py#L595-L611))를 gate와 공유함을 확인.
- 회귀: `PYTHONPATH=src python3 -m pytest -q` → 152 passed 직접 실행.
- **독립 round-trip 재현**: 8개 finding type 전체를 담은 findings.json으로 `review`→`gate`를 직접 실행해 (a) 각 target_key가 canonical 집합과 **정확히** 일치(payload 무누출), (b) gate가 8건 모두 pending으로 수용하는지 측정. 추가로 미테스트 분기(canonical key field 누락)를 직접 실행.
- Smoke: `schema --command review` 직접 실행.

## Findings

### 1. 계약 자기일관성 — 모순 없음

§5.6 review 규칙(534-547): review는 final 판단자가 아닌 draft writer, 각 finding→canonical key + `action: hold`, payload 미복사, unknown type/누락 field→invalid_input, 빈 findings→빈 decisions→gate success. 이 모두가 gate 계약(531-533 blocking, 521-522 pending/hold)과 정합 — hold는 gate에서 pending(521-522), 빈 decisions는 gate success. **내부 모순 없음.**

### 2. Spec ↔ 구현 — 일치

- review가 gate와 **동일한** `FINDING_KEY_FIELDS`([cli.py:595-611](../../src/assessment_harness/cli.py#L595-L611))를 single source of truth로 사용 → key 표 drift 불가능 구조.
- `_review_target_key_for_finding`([cli.py:617-636](../../src/assessment_harness/cli.py#L617-L636)): canonical field만 복사(`target_key[field] = finding[field]`). message/evidence/본문은 루프 대상이 아니므로 구조적으로 누출 불가. §5.6 "payload 미복사"와 일치.
- unknown type → `fields is None` → `HarnessInputError`([cli.py:620-621](../../src/assessment_harness/cli.py#L620-L621)); 누락 field → `field not in finding`([cli.py:624-627](../../src/assessment_harness/cli.py#L624-L627)). 둘 다 invalid_input/exit2. §5.6 546과 일치.
- 전 decision `action: hold`([cli.py:660](../../src/assessment_harness/cli.py#L660)) 고정 — 자동 판단 없음.
- review가 생성 record를 final_review schema로 self-validate([cli.py:670 부근](../../src/assessment_harness/cli.py#L639-L682)) 후 기록 — 잘못된 draft 방출 방지.

### 3. Round-trip 정확성 — 8/8 검증 (핵심 합격 근거)

8개 finding type 전체 findings.json으로 직접 `review`→`gate` 실행:

```
PASS all8 review:  rc=0 decisions=8 keys_exact=True   (각 target_key == canonical 집합 정확히)
PASS all8 gate roundtrip: rc=0 status=pending_review pending_decision_count=8
PASS L6 key minimal: ['spec_id','type']  (mandatory_spec_bonus_only_traced가 bonus_rubric_ids/evidence 누출 안 함)
```

review가 emit한 key가 gate의 exact-match 최소검사(`required==actual`)와 매칭검사를 8종 모두 통과. 특히 `double_scored_spec`(4-field)와 `mandatory_spec_bonus_only_traced`(finding엔 `bonus_rubric_ids`/`evidence`가 있으나 key는 `type`+`spec_id`만) 모두 정확. **round-trip 무결.**

### 4. 경계 매트릭스 — **빈 셀 1개**

| # | 계약 분기 (§5.6) | 기대 | 직접실행 | 회귀 잠금 |
|---|---|---|---|---|
| 1 | finding→canonical key (payload 미복사) | 최소 key | ✓ | `test_review_command_writes_hold_draft...` (cli:487) — optionality+double_scored, message/evidence 넣어두고 key엔 미포함 assert |
| 2 | 전 decision action: hold | hold | ✓ | cli:487 (`==["hold","hold"]`), fixture:420 (`=={"hold"}`) |
| 3 | reviewer/inputs.findings_path 기록 | 기록 | ✓ | cli:539-540 |
| 4 | draft가 final_review schema 통과 | valid | ✓ | cli:538, fixture:419 |
| 5 | round-trip → gate pending | pending | ✓ | cli:556-569, fixture:426-439 (check→review→gate, pending=3) |
| 6 | 빈 findings → 빈 decisions → gate success | success | ✓ | `test_review_command_empty_findings_draft_gates_success` (cli:572) |
| 7 | unknown finding type → invalid (546) | exit2 | ✓ | `test_review_command_rejects_unknown_finding_type` (cli:604) |
| 8 | **canonical key field 누락 → invalid (546)** | exit2 | ✓ PASS | **없음** |
| 9 | schema --command review | introspection | ✓ | `test_schema_command_returns_review_contract` (cli:335) |

직접실행 결과 #8도 계약대로 정확히 동작(`rc=2, status=invalid_input, "finding 'optionality_mismatch' missing gate key field..."`). 그러나 **회귀 부재**. #8은 §5.6 546이 #7과 한 문장에서 함께 호명한 분기이고([cli.py:624-627](../../src/assessment_harness/cli.py#L624-L627))의 별도 코드 경로다. findings schema는 `rubric_id`/`spec_id`를 optional로 두므로(스키마 통과하나 key field 없는 finding이 실재 가능) **도달 가능한** 분기다. #7만 잠기고 #8은 미잠금 — 빈 셀.

### 5. 테스트 코드 audit — 잠긴 8개는 건전

- `test_review_command_writes_hold_draft...`([cli:487-569](../../tests/test_cli_output_contract.py#L487-L569)): finding에 `message`+`evidence`를 일부러 넣고 생성된 target_key가 `{type,rubric_id}` / 4-field뿐임을 직접 assert — "payload 미복사" over-strict 잠금. 이어서 gate까지 돌려 pending 확인 — round-trip을 한 테스트로 잠금.
- fixture `test_review_draft_for_orphan_fixture_keeps_gate_pending`([test_fixtures.py:384-439](../../tests/test_fixtures.py#L384-L439)): 실 check 산출 findings 3건 → review draft(all hold, key⊆{type,rubric_id}) → gate pending=3. "review는 자동 판단하지 않는다"는 안전 속성을 E2E로 잠금.
- 모든 review 테스트가 `_assert_envelope`/`validate("cli_output",...)`로 공개 envelope 검증. 적합.

### 6. Smoke + 문서 — 일치

```
$ schema --command review → status success, informational=[review_path,decision_count,input_error], next_actions=[]
$ pytest -q → 152 passed (147 → +5: schema/hold_draft/empty/unknown_type/fixture)
```

README([README.md:122-126 부근](../../README.md))·HANDOFF·CHANGELOG·work_log이 review를 "draft writer, all-hold, 사람이 편집 후 gate"로 정확히 기술. HANDOFF "Initial `review` draft writer is live ... does not auto-accept or rewrite artifacts" 주장은 코드/테스트와 일치.

## Issues / Risks

1. **[차단] 경계 매트릭스 빈 셀 1개 (#8)**: "canonical key field 누락 → invalid_input"이 §5.6 546에서 명시적으로 호명되고 [cli.py:624-627](../../src/assessment_harness/cli.py#L624-L627)에서 별도 경로로 강제되나 named 회귀가 없다. 코드 거동은 직접실행으로 정확함을 확인. unknown-type 형제 분기(#7)는 잠겼으므로 동일 헬퍼에 1 케이스 추가로 닫힌다. gate 슬라이스에 적용한 표준("계약 호명 분기 미잠금 = 차단")을 일관 적용한 판정.
2. **[계약 gap, 경미] review가 `findings_doc.status`를 검사하지 않음**: Rule 0 invalid 기원의 `{status: invalid_input, findings: []}`도 빈 draft→gate success가 된다. §5.6은 "빈 findings→success"만 규정하고 status를 침묵한다. check가 Rule 0 invalid를 exit2로 먼저 차단하므로 정상 흐름에선 도달 안 하나, review/gate 어느 단계도 status를 가드하지 않는 cross-cutting 공백이다. owner가 "invalid_input 기원 findings는 review가 거절해야 하는가"를 §5.6에 명문화할지 결정 권장(본 슬라이스가 새로 만든 결함은 아님).
3. **[경미] review가 기존 `review.yaml`을 무조건 덮어씀**([cli.py:639-682](../../src/assessment_harness/cli.py#L639-L682)): 사람이 편집한 draft 위에 review를 재실행하면 편집분이 조용히 사라진다. draft generator로선 자연스러우나, 편집 후 재생성 시나리오에 대한 경고/거절이 없다. 계약 침묵 — owner 판단.

## Verdict

**조건부 합격 (Conditional Pass).**

- **합격 측면**: 계약 자기일관성(§1), spec↔구현(§2, gate와 key 표 공유로 drift 불가 구조), round-trip 8/8 무결(§3 — 본 슬라이스의 핵심 안전 속성), 잠긴 8개 테스트 건전성(§5), smoke/문서 정합(§6). review가 "자동 판단 없는 draft writer"라는 핵심 계약은 코드·회귀·E2E 세 자리에서 견고하게 성립.
- **조건(차단 해소 요건)**: #8 "canonical key field 누락 → invalid_input"에 named 회귀 1건 추가. (#7 unknown-type 테스트와 동일 패턴, `_run_main` + findings에 key field 빠진 finding → exit2/`"missing gate key field"` assert.)
- Issues 2·3은 owner 결정 대상(계약 침묵)이며 본 슬라이스 신규 결함이 아니므로 차단 사유로 올리지 않는다.

gate 슬라이스를 합격시킬 때 쓴 척도("코드가 정확해도 계약 호명 분기가 회귀로 안 잠기면 조건부")를 review에 동일 적용한 결과다.

## Outstanding items

- 전부 working tree 미커밋. publication boundary 진입은 owner 결정.
- 검증자는 #8 회귀를 직접 추가하지 않는다(발견·보고만). owner가 지시하면 잠근 뒤 재검증.
- Issues 2(status 가드)·3(덮어쓰기)는 계약 명문화 여부 owner 대기.

## Reproduction

```bash
cd <repo>
PYTHONPATH=src python3 -m pytest -q                                   # 152 passed
PYTHONPATH=src python3 -m assessment_harness.cli --output json schema --command review

# round-trip 직접 재현: 8개 finding type findings.json 작성 후
#   review --findings <f> --out-dir <d> --reviewer t  → review.yaml(all hold, 최소 key)
#   gate --final-review <d>/review.yaml               → pending_review, pending=8
# 미테스트 분기: optionality_mismatch finding에서 rubric_id 제거 → review → exit2 invalid_input
```
