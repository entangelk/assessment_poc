# Verification — Audit Trace Schema Foundation

- 검증 일자: 2026-05-28
- 검증 요청자: Owner — "검증해줘"
- 검증 수행자: AI (Claude Code, claude-opus-4-7)
- 검증 대상: `schemas/agent_trace.schema.json` + `schemas.py` 등록 + `test_agent_runner_contract.py` 회귀 — working tree, uncommitted
- 검증 소스: HEAD = `a4286f4` (AgentRunner protocol foundation), 본 슬라이스는 그 위의 미커밋 작업분
- 정본 spec 기준:
  - `docs/implementation_plan_assessment_harness_poc_v1.md` v1.22 §5.4.1 (413-423, audit trace JSONL 예시 + raw trace retention 분리), §11 (1194, "audit trace는 schema validation을 통과"), §15 line 1530 (`agent_trace.schema.json` 신설 항목)
  - 표면 단일 작업자 주장: 작업로그 §"Audit Trace Schema Foundation" ([work_log:616-663](../daily_logs/2026-05-28/work_log.md#L616-L663))

## Scope

1. 작업 범위 분리: raw trace retention/redaction, 회복 정책, candidate↔trace cross-reference는 미반영 확인.
2. Spec ↔ 스키마: plan §5.4.1 5개 예시 이벤트가 schema로 모두 통과하는가, 각 이벤트의 필수/선택 필드가 plan과 일치하는가.
3. anyOf 경계: turn+role 이벤트와 finish 이벤트(`finish_reason`+`turns`+`tool_call_count`) 두 모드가 잠겨 있는가.
4. Under-strict 가드: `run_id` 누락, anyOf 미충족, enum 위반, 빈 문자열, 음수 turn이 거부되는가.
5. 등록: `SCHEMA_FILES["agent_trace"]`가 등록되어 `validate()`로 도달 가능한가.
6. 회귀 무손상: 168 passed (3 + 48 + 8 + 14 + 95).
7. 문서 일관성: HANDOFF "thirteen JSON Schemas" + 디렉토리 절 + Verification 카운트, CHANGELOG 신규 row, stale "twelve" 잔존 없음.

## Methodology

- 계약: plan §5.4.1 (413-423), §11 (1194), §15 (1530) 정독.
- 스키마: [agent_trace.schema.json](../../schemas/agent_trace.schema.json) 직접 정독.
- 테스트 audit: [test_agent_runner_contract.py:35,40-41](../../tests/test_agent_runner_contract.py#L35-L41) 추가분 정독.
- **독립 재현(8 probe)**:
  - plan §5.4.1의 5개 이벤트(system/agent tool_call/tool result/agent tool_call/finish)를 직접 validate.
  - rejection probe 6건: missing run_id, missing turn+role (role only), finish without turns, bad role enum, empty run_id, negative turn.
- 회귀 직접 재현:
  - `PYTHONPATH=src python3 -m pytest tests/test_agent_runner_contract.py -q` → **3 passed**.
  - `PYTHONPATH=src python3 -m pytest -q` → **168 passed**.
  - `pytest --collect-only -q` → 3 + 48 + 8 + 14 + 95 = 168 일치.
- 워킹트리 스코프: `git status --short` — 신규 = `schemas/agent_trace.schema.json`; 수정 = `schemas.py`, `tests/test_agent_runner_contract.py`, HANDOFF/CHANGELOG/work_log. `base.py`/`mock.py`/`cli.py`/`rules.py`/`models.py`/fixture 일체 미수정.
- 문서 일관성: `rg -n "twelve JSON|12 JSON|twelve schemas|12 schemas" HANDOFF.md README.md CHANGELOG.md docs/implementation_plan_assessment_harness_poc_v1.md src tests` → 매치 없음 (verification 기록 안의 역사적 인용은 별도, 직접 검증함).

## Findings

### 1. 작업 범위 — 작업자 선언과 일치

`git status --short`로 직접 확인. 변경분:
- 신규: `schemas/agent_trace.schema.json` (1개)
- 수정: `src/assessment_harness/schemas.py`(등록 한 줄), `tests/test_agent_runner_contract.py`(+2 줄, +1 함수), HANDOFF.md, CHANGELOG.md, work_log.md
- `base.py`/`mock.py`/`cli.py`/`rules.py`/`models.py`/fixture 일체 미수정 ✓.

- raw trace retention/redaction: 도입 없음 ✓ (raw_trace는 여전히 schema 없이 in-memory tuple로만 반환).
- 회복 정책 (`blocked_by_runner_error` 등): 미반영 ✓.
- candidate↔trace cross-reference (`agent_run_id` 매칭): 미반영 ✓ — 본 schema는 단일 이벤트 shape만 검증.

**정합.**

### 2. Spec ↔ 스키마 — plan §5.4.1 5개 예시 모두 통과

독립 재현 결과 ([agent_trace.schema.json](../../schemas/agent_trace.schema.json) 직접 호출):

| # | plan §5.4.1 이벤트 형태 | 핵심 필드 | validate 결과 |
|---|---|---|---|
| 1 | system turn | `run_id, turn:0, role:system, content_ref` | PASS |
| 2 | agent tool_call | `run_id, turn:1, role:agent, tool_call:{name,args}` | PASS |
| 3 | tool result | `run_id, turn:1, role:tool, name, result_ref` | PASS |
| 4 | agent tool_call (반복) | `run_id, turn:2, role:agent, tool_call:{name,args}` | PASS |
| 5 | finish | `run_id, finish_reason, turns, tool_call_count` | PASS |

스키마 필드 vs plan 매핑:
- `run_id` (required, minLength 1) — 모든 이벤트가 carry ✓.
- `turn` (integer ≥0), `role` (enum `system/agent/tool`) — 이벤트 1-4에 등장 ✓.
- `content_ref`, `result_ref`, `name` (각 string minLength 1, optional) — plan 예시와 매핑 ✓.
- `tool_call.{name, args}` (둘 다 required) — 이벤트 2, 4와 매핑 ✓.
- `finish_reason` (string minLength 1), `turns` (≥0), `tool_call_count` (≥0) — 이벤트 5와 매핑 ✓.
- `additionalProperties: true` — 향후 확장 안전 ✓.

**정합.**

### 3. anyOf 경계 — 두 모드 잠금 OK

[agent_trace.schema.json:34-37](../../schemas/agent_trace.schema.json#L34-L37):
```json
"anyOf": [
  { "required": ["turn", "role"] },
  { "required": ["finish_reason", "turns", "tool_call_count"] }
]
```

직접 재현 — 두 분기 분리 정상 동작:
- `{run_id:r, role:system}` (turn 없음) → `"is not valid under any of the given schemas"` 거부.
- `{run_id:r, finish_reason:c, tool_call_count:1}` (turns 없음) → `"is not valid under any of the given schemas"` 거부.

**정합.**

### 4. Under-strict 가드 — 독립 6 probe 전부 거부

| 입력 | 기대 거부 사유 | 직접 재현 결과 |
|---|---|---|
| `{turn:0, role:system}` (run_id 누락) | `'run_id' is a required property` | ✓ |
| `{run_id:r, role:system}` (turn 누락) | `not valid under any of the given schemas` | ✓ |
| `{run_id:r, finish_reason:c, tool_call_count:1}` (turns 누락) | anyOf 미충족 | ✓ |
| `{run_id:r, turn:0, role:reviewer}` (enum 위반) | `'reviewer' is not one of [...]` | ✓ |
| `{run_id:'', turn:0, role:system}` (빈 run_id) | `'' is too short` | ✓ |
| `{run_id:r, turn:-1, role:system}` (음수 turn) | `is less than the minimum of 0` | ✓ |

### 5. 회귀 audit — 양방향 잠김 OK + 부수 정합

추가된 두 assert:
- [test:35](../../tests/test_agent_runner_contract.py#L35) `all(validate("agent_trace", event) == [] for event in result.audit_trace)` — mock의 2개 이벤트(system turn + finish) 모두 통과(직접 재현). plan §5.4.1 두 모드 each 1건.
- [test:40-41](../../tests/test_agent_runner_contract.py#L40-L41) `test_agent_trace_schema_rejects_unattributed_event` — `{finish_reason:"complete"}`는 run_id 누락 + anyOf 미충족 둘 다 위반, errors non-empty.

**소견 (보강 여지, 비차단)**: line 35의 `all(...)`은 빈 audit_trace에 대해 vacuous true. 현재 mock은 항상 2개 이벤트를 반환하므로 즉시 위험은 없지만, 향후 runner가 `audit_trace=()`을 반환하는 분기에서 검증이 침묵으로 통과될 수 있음. `len(result.audit_trace) > 0` 가드를 함께 두면 더 안전.

### 6. 회귀 무손상 — 직접 재현 OK

- `pytest -q` → **168 passed**, 0 failed.
- 카운트 167 → 168 (+1 신규 rejection 회귀) 정합.
- 기존 167개 모두 통과 = `base.py`/`mock.py`/`cli.py`/`rules.py` 미수정 결과와 정합.

### 7. 문서 일관성 — OK

- HANDOFF [line 17](../../HANDOFF.md#L17): "thirteen JSON Schemas" ✓.
- HANDOFF [line 201](../../HANDOFF.md#L201): `id_map.schema.json` / `semantic_verifications.schema.json` / `agent_trace.schema.json` 포함 명시 ✓.
- CHANGELOG: 신규 row("Audit trace schema foundation") 추가, 범위 선언("Raw trace retention/redaction and runner failure recovery remain later slices") 정합 ✓.
- 직접 재현 stale grep: `twelve JSON|12 JSON|twelve schemas|12 schemas` — 라이브 문서/소스/테스트에 매치 없음(과거 verification 기록 안의 인용은 정상) ✓.

## Issues / Risks

1. **(소견, 비차단)** 스키마가 bare `{run_id, turn, role}` 이벤트(payload 없음)를 허용. plan §5.4.1 5개 예시는 모두 turn+role 이벤트에 `content_ref` / `tool_call` / `name+result_ref` 중 하나의 payload를 동반하지만, 스키마는 role별 payload required 조건이 없음. 특히 `role:tool` 이벤트가 `name`이나 `result_ref` 없이도 통과. **Spec-silent-but-schema-permissive 갭** — plan이 role별 payload를 명시적으로 강제하지 않으므로 즉시 차단은 아니나, 향후 audit consumer 코드(verifier/compact)가 payload 없는 tool 이벤트를 만났을 때 안전한지가 명시되지 않음. 다음 슬라이스에서 (a) plan에 role별 required payload 명시 + 스키마에 oneOf/conditional 도입 또는 (b) plan에 "bare turn+role 이벤트도 허용" 명시 중 결정 필요.
2. **(소견, 비차단)** plan §11 line 1194 "**모든 candidate의 `agent_run_id`가 audit trace에 존재해야 한다**"의 cross-reference 검증은 본 스키마(단일 이벤트 검증)로는 잠글 수 없음. 작업자도 work_log §Decisions에 "candidate-to-trace cross-reference checks remain later slices"로 명시. 정합 — 구조적으로 candidate schema 도입 시점에 함께 들어와야 하는 검증이며 본 슬라이스 범위 밖.
3. **(보강 여지)** [test:35](../../tests/test_agent_runner_contract.py#L35) `all(...)`이 빈 시퀀스에 vacuous true. 향후 회복 분기 runner가 audit_trace=()을 반환할 때 검증이 침묵 통과할 위험. `assert len(result.audit_trace) > 0` 동반 잠금 권장.
4. **(소견)** raw trace는 schema 부재. 작업자가 plan §5.4.1 line 423 ("raw trace 저장 계약은 Phase 2 진입 전 retention/redaction 정책과 함께 확정")에 맞춰 의도적으로 미반영 — 정합.

## Verdict

**조건부 합격(Conditional pass).**

근거:
- 작업자 선언 범위(`agent_trace.schema.json` + 등록 + 회귀 2건 + 문서)를 정확히 그 범위만큼 수행 ✓.
- plan §5.4.1 5개 예시 이벤트가 schema로 모두 통과 — 독립 8 probe로 직접 재현 ✓.
- anyOf 두 모드 분리 잠금 + under-strict 6 probe 전부 거부 ✓.
- 회귀 168 passed 직접 재현 ✓.
- 비범위 선언(raw trace retention/redaction, 회복 정책, cross-reference)이 변경분에 부재 ✓.
- 단, **§Issues 1 (role별 payload required 조건이 plan-silent + schema-permissive)**가 다음 슬라이스 진입 전 결정 필요한 contract gap으로 남음. 본 슬라이스가 데이터 생성/소비 코드를 추가하지 않고 mock의 2개 이벤트만 통과시키므로 즉시 잘못된 산출은 없음.

판정을 "조건부"로 둔 이유는 plan §5.4.1 예시가 보여주는 role-payload 패턴을 스키마가 약속하지 않아 향후 audit consumer 구현 시 boundary가 모호해질 수 있다는 점. CLAUDE.md "Spec-silent-but-code-enforced is a contract gap"의 역방향 변형(spec-silent-but-schema-permissive)이지만 같은 종류의 boundary 미잠금. 본 슬라이스 자체에서 거부할 사유는 없음.

## Outstanding Items

- 워킹트리 미커밋. owner 인가 후 commit/push.
- 다음 trace/runner 슬라이스 진입 시 결정 필요 항목:
  - role별 payload 강제 여부(스키마에 conditional/oneOf 도입 vs plan에 "bare turn+role 허용" 명시)
  - candidate schema 도입 + `agent_run_id` cross-reference 검증
  - 회복 정책 (`blocked_by_runner_error` + finish_reason 분기 + 회귀)
  - raw trace retention/redaction 정책 + (필요 시) raw_trace schema

## Reproduction

```bash
cd <repo>
PYTHONPATH=src python3 -m pytest tests/test_agent_runner_contract.py -q   # → 3 passed
PYTHONPATH=src python3 -m pytest -q                                        # → 168 passed
PYTHONPATH=src python3 -m pytest --collect-only -q | tail -6               # → 3 + 48 + 8 + 14 + 95 = 168
git status --short                                                          # → agent_trace.schema.json 신규 + 5 수정 파일만
rg -n "twelve JSON|12 JSON|twelve schemas|12 schemas" \
   HANDOFF.md README.md CHANGELOG.md \
   docs/implementation_plan_assessment_harness_poc_v1.md src tests           # → 라이브 매치 없음

# plan §5.4.1 5 예시 + 6 rejection probe 독립 재현:
PYTHONPATH=src python3 -c "
from assessment_harness.schemas import validate
for e in [
  {'run_id':'r','turn':0,'role':'system','content_ref':'p'},
  {'run_id':'r','turn':1,'role':'agent','tool_call':{'name':'r','args':{}}},
  {'run_id':'r','turn':1,'role':'tool','name':'r','result_ref':'w'},
  {'run_id':'r','turn':2,'role':'agent','tool_call':{'name':'p','args':{}}},
  {'run_id':'r','finish_reason':'complete','turns':7,'tool_call_count':12},
]: assert validate('agent_trace', e) == []
for bad in [
  {'turn':0,'role':'system'}, {'run_id':'r','role':'system'},
  {'run_id':'r','finish_reason':'c','tool_call_count':1},
  {'run_id':'r','turn':0,'role':'reviewer'},
  {'run_id':'','turn':0,'role':'system'},
  {'run_id':'r','turn':-1,'role':'system'},
]: assert validate('agent_trace', bad) != []
print('all probes OK')
"
```
