# Verification — AgentRunner Protocol Foundation (Phase 2 entry)

- 검증 일자: 2026-05-28
- 검증 요청자: Owner — "다음 검증해줘"
- 검증 수행자: AI (Claude Code, claude-opus-4-7)
- 검증 대상: AgentRunner protocol + AgentRunResult dataclass + MockFixtureRunner + 회귀 — working tree, uncommitted
- 검증 소스: HEAD = `1383d08` (Phase 2 contract schemas), 본 슬라이스는 그 위의 미커밋 작업분
- 정본 spec 기준:
  - `docs/implementation_plan_assessment_harness_poc_v1.md` v1.22 §7 (804-862, 패키지 구조 + agent_runners 역할 분리), §9 (1118-1132, AgentRunner protocol 정의 + 회복 정책), §11 (1192-1196, contract test 요구), §15 v2 changelog (1490, 1532)
  - 표면 단일 작업자 주장: 작업로그 §"AgentRunner Protocol Foundation"

## Scope

1. 작업 범위 분리: 작업자가 명시한 비범위(SDK credential, tool side-effect, orchestrator, compact/verify, raw trace retention) 변경 부재 확인.
2. Spec ↔ 구현: `AgentRunner.run(spec_path, rubric_path, tools, max_turns, policy) -> AgentRunResult` 시그니처가 plan §9 line 1120과 글자 그대로 일치.
3. Spec ↔ 구현 — 파일 레이아웃: `agent_runners/base.py`, `agent_runners/mock.py` 위치/역할 일치(plan §7 line 810-814).
4. 회귀 audit: 두 신규 테스트가 protocol 만족 + 결정적 replay + 산출물 schema validity를 잠그는가.
5. 회귀 무손상: 전체 스위트(작업자 주장 167 passed = 2 agent-runner / 48 CLI / 8 fixture / 14 model / 95 rule).
6. 문서 일관성: HANDOFF Verification 카운트(165 → 167), HANDOFF Pending implementation 수정, 디렉토리 구조 + Tests 절 갱신, CHANGELOG 신규 row.

## Methodology

- 계약: plan §7 804-862, §9 1118-1132, §11 1192-1196 정독.
- 구현: [base.py](../../src/assessment_harness/agent_runners/base.py), [mock.py](../../src/assessment_harness/agent_runners/mock.py), [__init__.py](../../src/assessment_harness/agent_runners/__init__.py) 직접 정독.
- 테스트 audit: [test_agent_runner_contract.py:1-38](../../tests/test_agent_runner_contract.py#L1-L38) 본문 정독.
- 회귀 직접 재현:
  - `PYTHONPATH=src python3 -m pytest tests/test_agent_runner_contract.py -q` → **2 passed**.
  - `PYTHONPATH=src python3 -m pytest -q` → **167 passed**.
  - `pytest --collect-only -q` → 2 + 48 + 8 + 14 + 95 = 167 일치.
- 워킹트리 스코프: `git status --short` — 신규 = `src/assessment_harness/agent_runners/`, `tests/test_agent_runner_contract.py`; 수정 = HANDOFF/CHANGELOG/work_log 셋. `cli.py`/`rules.py`/`models.py`/`schemas.py`/fixture/`config` 일체 미수정.

## Findings

### 1. 작업 범위 — 작업자 선언과 일치

`git status --short`로 직접 확인. 신규 파일은 `agent_runners/` 디렉토리(`__init__.py`, `base.py`, `mock.py`)와 `tests/test_agent_runner_contract.py`뿐. 수정 파일은 문서 3개(HANDOFF/CHANGELOG/work_log). `cli.py`/`rules.py`/`models.py`/`schemas.py`/`config/policy.yaml`/`schemas/` 일절 미수정.

- SDK credential: 도입 없음 ✓ (mock은 자격 증명을 사용하지 않음).
- tool side-effect: `tools: Sequence[Any]` 시그니처만 있고 실제 tool은 미정의 ✓.
- orchestrator: 미작성 ✓ (`cli.py`에 `extract`/`run` 등 신규 sub-command 없음).
- compact / verify: 미작성 ✓.
- raw trace retention: 정책/저장 코드 없음 ✓ (`raw_trace`는 in-memory tuple로만 반환).

**정합.**

### 2. Spec ↔ run() 시그니처 — 글자 그대로 일치

plan §9 line 1120:
> `AgentRunner` protocol 정의 (framework-agnostic; `run(spec_path, rubric_path, tools, max_turns, policy) -> AgentRunResult`)

[base.py:35-43](../../src/assessment_harness/agent_runners/base.py#L35-L43):
```python
def run(
    self,
    spec_path: Path,
    rubric_path: Path,
    tools: Sequence[Any],
    max_turns: int,
    policy: Mapping[str, Any],
) -> AgentRunResult:
```

5개 매개변수 이름·순서, 반환 타입 모두 일치. `Protocol` + `@runtime_checkable` 사용으로 [test:16](../../tests/test_agent_runner_contract.py#L16) `isinstance(runner, AgentRunner)` 런타임 체크 가능. **정합.**

### 3. Spec ↔ 파일 레이아웃

plan §7 line 810-814 + 860:
```
agent_runners/
  base.py            # AgentRunner protocol (framework-agnostic)
  mock.py            # Phase 2: fixture YAML을 결정적으로 반환하는 fake runner (protocol contract test 전용)
```
plan 본문: "mock.py는 fixture YAML을 결정적으로 반환하는 fake runner로, protocol contract test 전용이며 실제 평가에는 사용하지 않는다 (manual.py는 Phase 0/1의 사람 입력용, mock은 Phase 2의 contract 분리 증명용으로 역할이 다르다)."

구현:
- [agent_runners/base.py](../../src/assessment_harness/agent_runners/base.py): 위치/역할 일치 ✓.
- [agent_runners/mock.py:12-17](../../src/assessment_harness/agent_runners/mock.py#L12-L17): docstring에 "This runner proves the orchestration boundary is not tied to a specific SDK. It is not a candidate generator and should not be used for real assessment extraction." — plan 본문과 실질 동일 표현 ✓.
- `manual.py`는 본 슬라이스에서도 미작성(Phase 0/1 입력 경로 그대로 `cli.py` 직접 로딩) — 분리 원칙 유지 ✓.

### 4. Spec ↔ Implementation — 의미적 갭(소견, 비차단)

#### 4-A. mock이 반환하는 artifacts는 candidate 형태가 아님

plan §5.4 (377-396)은 candidate artifact 형태를 정의:
```yaml
spec_item_candidates:
  - candidate_id: SC1
    proposed_item: { id: S1, text: ..., requirement_level: must, source_ref: ... }
    agent_runner: claude_agent_sdk
    agent_run_id: "run_2026-05-25T00:00:00Z_a1b2"
    integrity_status: pending_check
```

[mock.py:34-38](../../src/assessment_harness/agent_runners/mock.py#L34-L38)은 fixture의 `spec_items.yaml`(compacted 형태)을 그대로 `artifacts["spec_items"]`에 담는다. `spec_item_candidates` 키도, `candidate_id`/`proposed_item`/`agent_runner`/`agent_run_id`/`integrity_status`도 없음. plan §5.4가 정의한 candidate shape은 본 슬라이스에서 보장되지 않음.

[test:33-35](../../tests/test_agent_runner_contract.py#L33-L35)는 spec_items/rubric_items/trace_links 스키마만 validate — candidate 스키마 미존재(아직 `spec_item_candidates.schema.json` 없음).

**소견**: 작업자 본인이 work_log §Decisions에서 "The mock remains test-only and is not a real assessment extraction path"라고 명시했으므로 의도된 단순화. **다만 contract test 자체가 "framework portability"를 잠그지는 못함** — 실제 SDK runner가 candidate를 어떤 shape으로 반환해야 하는지 protocol이 명시하지 않고 있어, 본 슬라이스의 contract test를 통과하는 두 번째 framework runner(plan 본문 "Codex/Gemini 등 두 번째 framework 연동")가 출력 형태에서 자유롭게 달라질 수 있음. 다음 슬라이스에서 (a) candidate schema 등록 + (b) `AgentRunResult.artifacts`에 candidate shape을 요구하는 contract 잠금이 필요. **본 슬라이스는 "protocol type boundary"라는 최소 목표만 잠그고 있으며 작업자가 이를 선언했으므로 차단 아님**, 그러나 향후 결정 사항으로 추적.

#### 4-B. `AgentRunResult.status` 필드는 plan 미명시

[base.py:21-22](../../src/assessment_harness/agent_runners/base.py#L21-L22):
```python
status: str
finish_reason: str
```

plan §9 line 1129는 "audit trace의 `finish_reason`에 사유 기록"만 언급. `status`는 plan 어디에도 정의되지 않음. [mock.py:77-78](../../src/assessment_harness/agent_runners/mock.py#L77-L78)는 둘 다 `"complete"`로 동일 값 설정 — **현재 두 필드 의미 중복**. 향후 (예: `status="error"` + `finish_reason="max_turns_exceeded"`) 분리될 수 있겠으나 본 슬라이스에서 둘의 의미 차이가 잠겨 있지 않음.

**소견**: 비차단. plan에 명시된 단일 필드(`finish_reason`)는 잠겼고, `status`는 미명시 확장. 향후 plan §5.4 `integrity_status` enum과의 매핑 또는 `status` 의미를 plan에 명시할지 결정 필요.

#### 4-C. 회복 정책(plan §9 line 1129) 미반영

plan: "max_turns 초과, tool error, schema-invalid output은 run 단위로 격리하고 audit trace의 `finish_reason`에 사유 기록. `integrity_status: blocked_by_runner_error`로 표시."

본 슬라이스 mock은 happy path만 구현 — max_turns 초과/tool error 분기 없음. 회귀도 happy path 1건만 잠금.

**소견**: 작업자가 명시적으로 "Phase 2 최소 슬라이스"로 범위 한정. 비차단. 실제 SDK runner 추가 시 회복 정책 + 회귀가 함께 들어와야 함. 추적 필요.

#### 4-D. audit_trace schema 부재

plan §15 line 1530: "`cli_output.schema.json`, `agent_trace.schema.json` 추가." 또한 plan §11 line 1194: "audit trace는 schema validation을 통과하고, 모든 candidate의 `agent_run_id`가 audit trace에 존재해야 한다."

`agent_trace.schema.json`은 `schemas/` 디렉토리에 미존재 (`ls schemas/` — 12개 그대로). [mock.py:47-60](../../src/assessment_harness/agent_runners/mock.py#L47-L60)는 audit_trace를 dict tuple로 생성하지만 schema validation 없음. [test:36](../../tests/test_agent_runner_contract.py#L36)는 `result.audit_trace[-1]["finish_reason"] == "complete"`만 잠그고 전체 schema는 잠그지 않음.

**소견**: 비차단. plan §15에 "추가" 항목으로 등록은 되어 있으나 등록 시점이 본 슬라이스에 명시되지 않음. 다음 슬라이스에서 candidate schema와 함께 도입 필요.

### 5. 테스트 audit — under-strict 가드 OK, over-strict는 자명한 happy path 1건

**Under-strict (계약 위반이 회귀로 잡히는가)**:

| 잠긴 경계 | 테스트 위치 | 검증 |
|---|---|---|
| `MockFixtureRunner`가 `AgentRunner` protocol 만족 | [test:11-16](../../tests/test_agent_runner_contract.py#L11-L16) | `assert isinstance(runner, AgentRunner)` — `runtime_checkable` 기반 |
| 결정적 replay로 result identity 보존 | [test:29-32](../../tests/test_agent_runner_contract.py#L29-L32) | `run_id`, `runner_name`, `status`, `finish_reason` 잠금 |
| 산출물이 schema-valid | [test:33-35](../../tests/test_agent_runner_contract.py#L33-L35) | spec_items/rubric_items/trace_links 세 schema validate empty error list |
| trace metadata 존재 | [test:36-37](../../tests/test_agent_runner_contract.py#L36-L37) | audit_trace의 마지막 entry `finish_reason`, raw_trace의 첫 entry `fixture_dir` |

**Over-strict**: 별도 테스트 없음. happy path 1건이 그 자체로 over-strict 가드 역할(잘못된 path였다면 실패) — Plan §9 회복 정책 분기가 미구현이므로 over-strict 가드 부재가 정당함.

직접 재현 — `pytest tests/test_agent_runner_contract.py -q` **2 passed**.

### 6. 회귀 무손상 — 직접 재현 OK

- `pytest -q` → **167 passed**, 0 failed.
- 카운트 165 → 167 (+2 agent-runner) 정합.
- 기존 165개 모두 통과 = 기존 코드 미수정 결과와 정합.

### 7. 문서 일관성 — OK

- HANDOFF [Current Status](../../HANDOFF.md): "AgentRunner protocol foundation is live" 한 줄 추가, 기존 Pending implementation에서 "real SDK runners, framework tools, orchestrator workflows" 명시적으로 잔존 항목으로 옮김 ✓.
- HANDOFF [Implementation Decisions](../../HANDOFF.md): "Phase 0 held `agent_runners/` and `tools/` out of scope. Phase 2 has now started with only the `AgentRunner` protocol and deterministic mock replay" — 이전 결정 갱신 ✓.
- HANDOFF [Project Structure](../../HANDOFF.md): `agent_runners/base.py` `agent_runners/mock.py` 항목 추가 ✓.
- HANDOFF [Verification](../../HANDOFF.md): 165 → 167, "2 agent-runner contract" 카운트 반영 ✓.
- CHANGELOG: 신규 row 추가 — 범위 선언 그대로 정합 ✓.

## Issues / Risks

1. **(소견, 비차단)** Mock이 반환하는 artifacts는 candidate(`spec_item_candidates`)가 아닌 compacted 형태(`spec_items`/`rubric_items`/`trace_links`). plan §5.4가 정의한 candidate shape이 잠겨 있지 않음. 두 번째 framework runner 추가 시 출력 형태 일관성이 자동 보장되지 않음.
2. **(소견, 비차단)** `AgentRunResult.status` 필드는 plan 미명시. 현재 `finish_reason`과 의미 중복. 향후 plan §5.4 `integrity_status` 매핑 또는 의미 분리 명시 필요.
3. **(소견, 비차단)** plan §9 line 1129 회복 정책(max_turns 초과 → `finish_reason` 사유 + `integrity_status: blocked_by_runner_error`) 미반영. 본 슬라이스 범위 밖이라 정당하지만 실제 runner 슬라이스에서 동반 진입 필요.
4. **(소견, 비차단)** `agent_trace.schema.json`이 plan §15 line 1530에 신설 항목으로 등록되어 있으나 본 슬라이스에서 추가되지 않음. mock의 audit_trace가 schema validation을 받지 않음. plan §11 line 1194 "audit trace는 schema validation을 통과"가 protocol 자체 차원에서 잠겨 있지 않음.
5. **(보강 여지)** `manual.py` 미작성 — plan §7 line 860에서 mock과 역할 분리를 명시했으나, 본 슬라이스 범위 밖이며 Phase 0/1 입력 경로는 현재도 작동하므로 비차단.

## Verdict

**조건부 합격(Conditional pass).**

근거:
- 작업자 선언 범위(protocol type boundary + 결정적 mock + 회귀 2건)를 정확히 그 범위만큼 수행 ✓.
- plan §9 line 1120의 5-매개변수 시그니처 글자 그대로 일치 ✓.
- 비범위 선언(SDK/tool/orchestrator/compact/verify/raw retention) 모두 변경분에 부재 ✓.
- 회귀 167 passed 직접 재현 ✓.
- 단, **contract test가 잠그는 것이 "protocol type boundary"에 한정**되며, candidate shape / audit_trace schema / 회복 정책은 다음 슬라이스로 미뤄짐. 본 슬라이스가 "framework portability contract test"의 일부에 해당하며 plan §11 line 1193 "mock runner로 contract test 작성, PoC에서는 protocol 분리만 확인" 조항과 정합 — plan은 의도적으로 "분리만"이라고 명시. 따라서 plan-vs-구현 모순은 없음.

판정을 "합격(무조건)"이 아닌 "조건부 합격"으로 둔 이유는, 다음 runner 슬라이스 진입 시 §Issues 1~4가 함께 잠겨야 framework portability 주장이 실증적으로 닫힌다는 점을 기록으로 남기기 위함. 본 슬라이스 자체에서 거부할 사유는 없음.

## Outstanding Items

- 워킹트리 미커밋. owner 인가 후 commit/push.
- 다음 runner 슬라이스 진입 시 결정 필요 항목(작업자도 명시):
  - SDK credential 전달 방식
  - tool side-effect 정책(read-only / propose-tools / batch runner)
  - candidate schema 등록 + `AgentRunResult.artifacts` shape 잠금
  - `agent_trace.schema.json` 도입 + audit_trace schema validation
  - 회복 정책 (`integrity_status: blocked_by_runner_error`, `finish_reason` 분기) 구현 + 회귀
  - orchestrator/`extract` CLI sub-command
  - raw trace retention 정책

## Reproduction

```bash
cd /workspace/assessment_poc
PYTHONPATH=src python3 -m pytest tests/test_agent_runner_contract.py -q     # → 2 passed
PYTHONPATH=src python3 -m pytest -q                                          # → 167 passed
PYTHONPATH=src python3 -m pytest --collect-only -q | tail -6                 # → 2 + 48 + 8 + 14 + 95 = 167
git status --short                                                            # → agent_runners/, test_agent_runner_contract.py 신규 + 문서 3개 수정만
ls schemas/ | wc -l                                                           # → 12 (변동 없음)
```
