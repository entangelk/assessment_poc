# Verification — `review` Safety Guards Follow-up (plan v1.19)

- 검증 일자: 2026-05-28
- 검증 요청자: Owner — "다시 검증해봐줘"
- 검증 수행자: AI (Claude Code, claude-opus-4-7)
- 검증 대상: plan v1.19 `review` status guard + overwrite guard + 직전 검증의 빈 셀(known type missing key field) 보강 — working tree, uncommitted
- 정본 spec 기준: `docs/implementation_plan_assessment_harness_poc_v1.md` v1.19 §5.6 (review draft 규칙 537-562) + §15 v1.19 changelog
- 직전 검증 기록: [2026-05-28_review_draft_writer.md](2026-05-28_review_draft_writer.md) — 그 기록의 조건부 합격 사유(빈 셀 #8 missing key field)와 Issues 2(status 가드)·3(overwrite)를 본 보강이 직접 닫는다.

## Scope

1. **계약 보강 정합성** — v1.19 §5.6에 추가된 status guard / overwrite guard / versioning boundary가 명확하고 자기일관적인가.
2. **Spec ↔ 구현** — status는 whitelist인가(invalid_input뿐 아니라 모든 비허용 status 거절), overwrite 검사가 write 전에 일어나는가, `--force` 동작.
3. **경계 매트릭스** — 직전 빈 셀 #8 + 신규 status/overwrite 분기가 양방향 named 회귀로 잠겼는가.
4. **회귀 무손상** — 기존 round-trip / gate 계약이 status·overwrite 보강으로 깨지지 않았는가.
5. **테스트 코드 audit** — 각 보강 테스트가 계약을 실제로(공개 surface, 양방향) 잠그는가.
6. **Smoke + diff hygiene + 문서.**

## Methodology

- 계약: plan v1.19 §5.6 537-562, §15 v1.19 changelog 정독.
- 구현: [cli.py:639-687](../../src/assessment_harness/cli.py#L639-L687) `_cmd_review` 직접 대조 (status guard [652-660](../../src/assessment_harness/cli.py#L652-L660), overwrite guard [712-718](../../src/assessment_harness/cli.py#L712-L718)).
- 회귀: `pytest tests/test_cli_output_contract.py tests/test_fixtures.py` (49 passed), `pytest` 전체 (156 passed) 직접 실행.
- **독립 재현**: whitelist 동작(`internal_error` 거절 / `success`·`provisional_findings` 허용), overwrite 3분기(없음→write, 있음+no force→거절, 있음+force→덮어씀), review→gate round-trip 유지를 직접 측정.
- Smoke: `schema --command review` / `schema --command gate`, `git diff --check`.

## Findings

### 1. 계약 보강 정합성 — 명확·자기일관

v1.19 §5.6(537-562)이 세 규칙 추가:
- **status guard**: "`findings.json`의 `status`는 `success` 또는 `provisional_findings`여야 한다. ... `status: invalid_input` ... 승격하지 않는다. 이 검사는 `review`에서 수행한다. `gate`는 ... 수동 복구/감사 흐름을 과도하게 차단하지 않는다." — whitelist로 표현. review가 가드하고 gate는 status-agnostic으로 남긴다는 역할 분리가 명시됨.
- **overwrite guard**: "`<out-dir>/review.yaml`이 이미 있으면 기본적으로 ... `invalid_input`/exit `2` ... 재생성하려면 `--force`."
- **versioning boundary**: 자동 versioning은 보류, caller가 새 `--out-dir`로 분리 — 직전 Issue 3의 "보류" 결정이 계약에 박힘.

직전 검증 Issues 2·3이 owner 결정(안전장치 추가)으로 §5.6에 명문화됨. 모순 없음.

### 2. Spec ↔ 구현 — 일치 (whitelist 구조 확인)

- **status guard** [cli.py:652](../../src/assessment_harness/cli.py#L652): `if findings_doc.get("status") not in {"success", "provisional_findings"}`. **whitelist** — `invalid_input`, `internal_error`, status 누락(None) 모두 거절. blocklist(`== invalid_input`)가 아님을 직접 확인 → 미래 status도 기본 거절되는 안전한 방향.
- 순서: read → findings schema validate → status guard → decision 생성. status는 schema-valid 이후 검사 (findings enum에 4 status 존재하므로 schema는 통과).
- **overwrite guard** [cli.py:712](../../src/assessment_harness/cli.py#L712): `if review_path.exists() and not args.force`. `write_text` **직전**에 검사 — 기존 파일을 읽거나 건드리지 않고 거절. `--force`는 `store_true`로 파서에 추가됨.
- 직전 슬라이스의 round-trip 로직(canonical key, all hold)은 무변경 — status/overwrite는 그 앞뒤에 추가된 가드일 뿐.

직접 재현:
```
PASS internal_error status rejected (whitelist): rc=2 invalid_input
PASS success-status-with-findings allowed: rc=0 decisions=1
PASS overwrite guard: first=0 second=2 (already exists) force=0
PASS review->gate roundtrip pending: rc=0 pending_review
```

### 3. 경계 매트릭스 — 직전 빈 셀 + 신규 분기 전부 잠김

| 분기 (§5.6 v1.19) | 기대 | 직접실행 | 회귀 |
|---|---|---|---|
| **#8 known type, canonical key field 누락 → invalid (직전 빈 셀)** | exit2 | ✓ | `test_review_command_rejects_known_finding_missing_key_field` (cli:760) — `"missing gate key field"` assert, unknown-type와 메시지로 구별 |
| unknown finding type → invalid | exit2 | ✓ | `test_review_command_rejects_unknown_finding_type` (cli:725) `"unknown finding type"` |
| status `invalid_input` → reject | exit2 | ✓ | `test_review_command_rejects_invalid_input_findings_status` (cli:620) `"findings.status"`, 빈 findings+invalid_input |
| status `success`/`provisional_findings` → allow | 진행 | ✓ | empty(success, cli:588) / round-trip·fixture(provisional) |
| review.yaml 없음 → write | success | ✓ | 다수 |
| review.yaml 있음 + no force → reject | exit2 | ✓ | `test_review_command_refuses_to_overwrite_existing_draft_without_force` (cli:648) |
| review.yaml 있음 + `--force` → overwrite | success | ✓ | `test_review_command_force_overwrites_existing_draft` (cli:694) |

직전 검증의 단일 차단 사유(#8)와 두 owner-결정 Issues가 모두 named 회귀로 잠겼다. **차단성 빈 셀 0.**

### 4. 회귀 무손상

- gate 계약 무변경 — `schema --command gate` smoke `status=success` 유지, gate 테스트 전부 green.
- 49 focused / 156 full passed (직전 152 → +4: missing_key_field / status_reject / overwrite_forbidden / force_overwrite). collect 분포 CLI 41·fixture 8·model 12·rule 95 = 156, work_log 보고와 일치.
- `git diff --check` clean.

### 5. 테스트 코드 audit — 보강 4건 모두 건전

- **missing key field** (cli:760): findings schema가 `rubric_id` optional임을 이용해 `optionality_mismatch` finding에서 rubric_id를 빼고 → exit2 + `"missing gate key field"`. unknown-type(`fields is None`)과 **별도 코드 경로**(`field not in finding`)를 메시지로 구분해 잠금.
- **status reject** (cli:620): 빈 findings + `invalid_input` status → 거절. 빈 findings + `success`(cli:588)는 **허용**되므로, 이 둘이 함께 "빈 findings 자체가 아니라 status가 판단 기준"임을 양방향으로 고정. Rule 0 누수 시나리오(직전 Issue 2)를 정확히 잠금.
- **overwrite forbidden** (cli:648): 실제 review로 draft 생성 → 사람이 `"human edited draft"`로 덮어씀 → 재실행(no force) → exit2 + `"already exists"` + **사람 편집분이 보존됨을 직접 assert**(`read_text() == "human edited draft\n"`). 단순 exit code가 아니라 "편집분 비파괴"라는 핵심 안전 속성을 잠금.
- **force overwrite** (cli:694): `"old draft"` 사전 배치 → `--force` → success + `"old draft" not in` 내용. force의 under-strict 가드.
- 모든 테스트 `_assert_envelope`로 cli_output schema 검증.

## Issues / Risks

1. **[경미, 비차단] status reject 회귀가 enum을 부분 표본만 잠금.** 거절 대상 status는 `invalid_input`·`internal_error`(+미래 status) 2+종인데 회귀는 `invalid_input` 1종만 사용([cli 테스트에 `internal_error` 리터럴 없음] 확인). 코드가 whitelist(`not in {...}`)라 `internal_error`도 거절됨을 직접 재현으로 확인했으나, **만약 누군가 whitelist를 blocklist(`== "invalid_input"`)로 리팩터하면 현행 테스트는 녹색인 채 `internal_error`/status-누락이 누수**된다. 권고: `test_review_command_rejects_invalid_input_findings_status`를 `@pytest.mark.parametrize`로 `internal_error`(및 status 누락)까지 확장해 whitelist-ness를 잠글 것. — 계약이 명시적으로 호명한 거절 케이스(`invalid_input`)와 허용 양쪽(success/provisional)은 이미 잠겨 있어 **차단 사유는 아님**.
2. **[관찰, 비차단] gate는 여전히 status-agnostic.** v1.19가 의도적으로 review에만 status 가드를 두고 gate는 수동 복구 경로로 남김(§5.6 명시, owner 결정). 따라서 손으로 만든 `invalid_input`-기원 final_review를 gate에 직접 넣으면 status는 검사되지 않는다 — 계약대로의 의도된 거동. 결함 아님.

## Verdict

**합격 (Pass).**

직전 검증의 단일 차단 사유(빈 셀 #8 missing key field)와 두 owner-결정 Issues(status 누수, overwrite 비파괴)가 plan v1.19 계약 + 양방향 named 회귀 + 직접 재현 세 자리에서 모두 닫혔다. status guard는 안전한 whitelist 구조이고, overwrite guard는 "사람 편집분 비파괴"를 테스트가 직접 잠근다. gate 계약은 무손상.

Issue 1(internal_error 미표본)은 **차단으로 올리지 않는다** — 직전 라운드들에서 차단 처리한 것은 "계약이 호명한 분기가 코드에 있으나 회귀가 전무"한 경우였다. 여기서는 계약이 호명한 거절 케이스(`invalid_input`)와 허용 양쪽이 모두 잠겼고, 남은 것은 동일 whitelist 식을 다른 enum 값으로 한 번 더 표본하는 강화일 뿐이다. 이를 "조건부"로 떨어뜨리면 차단 기준이 인플레되어 직전 자기비판이 경계한 일관성을 오히려 해친다. 따라서 합격 + 강화 권고로 둔다.

## Outstanding items

- 전부 working tree 미커밋. publication boundary는 owner 결정.
- Issue 1(status reject parametrize)은 강화 권고 — owner가 원하면 1줄 parametrize로 추가 가능. 검증자는 직접 수정하지 않음.

## Reproduction

```bash
cd <repo>
PYTHONPATH=src python3 -m pytest tests/test_cli_output_contract.py tests/test_fixtures.py -q   # 49 passed
PYTHONPATH=src python3 -m pytest -q                                                            # 156 passed
PYTHONPATH=src python3 -m assessment_harness.cli --output json schema --command review
git diff --check

# 직접 재현: status whitelist (internal_error 거절 / success 허용),
#   overwrite 3분기 (없음→0, 있음+no force→2 "already exists", 있음+--force→0),
#   review→gate round-trip pending 유지.
```
