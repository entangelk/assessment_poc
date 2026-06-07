# 검증 기록 — extract source snapshot 자동 생성 (plan v1.32)

## Subject metadata

- 날짜: 2026-06-07
- 요청자: 프로젝트 소유자 (kdtyohan@gmail.com)
- 검증자: Claude (독립 검증)
- 대상 슬라이스: `extract`가 `--source-manifest` 생략 시 sibling `source_snapshot/`을 자동 생성하는 기능 + SDK runner 결정 문서 + plan v1.32 문서 갱신
- canonical spec 참조: `docs/implementation_plan_assessment_harness_poc_v1.md` v1.32 (§14 결정 항목 8, §15 변경 이력 v1.32, 명령 동작 단락); `schemas/source_manifest.schema.json`
- 검증 대상 소스: working tree, uncommitted (커밋 전). 변경 파일: `src/assessment_harness/cli.py`, `tests/test_cli_output_contract.py`, `docs/implementation_plan_...v1.md`, `docs/sdk_runner_decisions.md`(신규), `HANDOFF.md`, `README.md`, `docs/evaluation.md`, `CHANGELOG.md`, `docs/daily_logs/2026-06-07/work_log.md`(신규)

## Scope

검증한 표면:
1. Spec 계약 (plan v1.32 + source_manifest 스키마) — 내부 정합성
2. 구현 코드 (`cli.py`의 snapshot 생성 경로)
3. 회귀 테스트 (신규/수정 CLI 테스트)
4. Snapshot ↔ 원본 sha256 정합성 (fixture grounding)
5. 다운스트림 소비 정합성 (integrity grounding, README 워크플로)
6. 전체 테스트 스위트 + per-module 카운트 (evaluation 표 대조)
7. 결정 문서(`sdk_runner_decisions.md`)와 plan §8/§14의 정합성
8. 문서 핸드오프 정합성 (work_log 필수 섹션, CHANGELOG, README 문서맵)

## Methodology

- spec/스키마는 in-place 정독 후 boundary matrix 구성
- 코드는 `cli.py:609-776`, `models.py:97-125`, `agent_runners/integrity.py:55-89`, `agent_runners/mock.py:34-45` 정독
- 테스트는 변경 diff(`git diff tests/test_cli_output_contract.py`)와 신규 함수 정독
- 재현 명령:
  - `PYTHONPATH=src python3 -m pytest tests/test_cli_output_contract.py -k extract` → `8 passed`
  - `PYTHONPATH=src python3 -m pytest tests/test_cli_output_contract.py` → `110 passed`
  - `PYTHONPATH=src python3 -m pytest` → `279 passed`
  - 모듈별 `pytest tests/<m>.py` 7회 → 95/110/27/10/7/22/8
  - 직접 smoke: `extract --out-dir /tmp/snaptest/runs` (manifest 생략) → snapshot 생성 + `sha256sum` 원본 대조
  - 경계 smoke: `--out-dir runs` (상대 단일 컴포넌트)
  - `python3 -m py_compile src/assessment_harness/cli.py`, `git diff --check`

## Findings

### 1. Spec 계약 내부 정합성 — 통과

plan v1.32는 두 곳(명령 동작 단락 / §15 변경 이력)에서 동일하게 기술: `--source-manifest` 생략 시 `--out-dir`의 sibling `source_snapshot/`에 spec/rubric snapshot과 `manifest.yaml` 생성, `DOC_SPEC`(`candidate_spec`)/`DOC_RUBRIC`(`evaluator_rubric`) + 각 `sha256`, 명시 manifest 우선. §14 항목 8은 ✓로 read-only tool 정책 확정. 두 단락 간 모순 없음. 스키마(`source_manifest.schema.json`)의 `required`/`role` enum과 생성 문서가 일치.

### 2. 구현 코드 — 통과

- `cli.py:722-725` `_extract_source_manifest_path`: 명시 시 그 경로 반환, 아니면 생성 → 명시 우선 계약 정확.
- `cli.py:728-760` `_generate_extract_source_snapshot`: `out_dir.parent/source_snapshot`에 spec.md/rubric.md 복사, `DOC_SPEC`/`DOC_RUBRIC` + 복사본 기준 `sha256`로 manifest 구성, `validate("source_manifest", ...)` 통과 후 기록. snapshot 파일 기준으로 해시를 계산하므로 `load_source_snapshot`의 expected==actual 보장.
- `cli.py:613-614` 생성 manifest를 `load_source_snapshot`로 다시 읽어 integrity grounding에 사용 → 단일 grounding 소스.

### 3. 회귀 테스트 (boundary matrix) — 통과, 빈 셀 없음

| 계약 분기 | 테스트 | 방향 |
|---|---|---|
| manifest 생략 → snapshot 생성 (경로/스키마/sha/내용/DOC id) | `test_extract_mock_fixture_writes_validated_candidate_runs` | under-strict (fixture manifest fallback로 회귀하면 `manifest_path == tmp_path/source_snapshot/manifest.yaml` 단언이 실패) |
| manifest 명시 → snapshot **미생성**, 명시 우선 | `test_extract_explicit_source_manifest_takes_precedence` | over-strict (`assert not (tmp_path/source_snapshot/manifest.yaml).exists()` + `source_manifest_path == 명시경로`) |

수정 테스트는 (a) 생성 manifest의 `documents` 리스트를 정확 비교, (b) sha256을 snapshot 파일에서 재계산해 대조, (c) snapshot 내용이 fixture source와 동일함을 비교. 모든 계약 리터럴이 단언에 고정됨. 양방향 가드 모두 존재 — 빈 셀 없음.

### 4. Snapshot ↔ 원본 sha256 정합성 — 통과

직접 smoke에서 생성 `manifest.yaml`의 sha와 `sha256sum` 재계산값 일치:
- spec: `21a7cd6e...b947` (snapshot == fixture 원본)
- rubric: `d36b4762...ba91` (snapshot == fixture 원본)
`valid_run_count=2, invalid_run_count=0` → 생성 snapshot으로 integrity validated 확인.

### 5. 다운스트림 소비 정합성 — 통과

- `integrity.py`/`run_rule_zero`는 `document_id`·`sha256` 기반 grounding만 사용. `mock.py:40`의 `artifacts["source_manifest"]`(fixture manifest)는 extract 핸들러에서 소비되지 않음(grep으로 소비처 없음 확인) → 생성 snapshot 하나만 grounding으로 작동, 충돌 없음.
- README 워크플로 정합: `extract --out-dir work/runs`(manifest 생략) → `work/source_snapshot/manifest.yaml` 생성 → `verify`/final-review가 `--source-manifest work/source_snapshot/manifest.yaml` 참조. extract→verify 경로 일관(README:101-129).
- `check` 명령의 `--source-manifest` 필수 정책(`_check_missing_manifest`, README:56)은 extract 변경과 분리 유지됨.

### 6. 테스트 스위트 / 카운트 — 통과

- extract 8 / contract 110 / 전체 279 재현 일치.
- per-module 실측 95/110/27/10/7/22/8 = 279 → `docs/evaluation.md` 표 및 합계와 정확히 일치(278→279, contract 109→110 갱신 정확).
- `py_compile` 통과, `git diff --check` clean 재현.

### 7. 결정 문서 / 핸드오프 — 통과

- `sdk_runner_decisions.md`는 plan §8(read-only tool, runner collect 후 candidate emit, write 금지)·§14 미결정 항목(credential/sample/retention/limits)을 checklist로 정리. plan 결정과 모순 없음.
- `work_log.md`는 Goals/Completed work/Issues/Decisions/Next steps 필수 섹션 모두 충족. CHANGELOG에 v1.32 항목 2건 추가, README 문서맵 v1.31→v1.32 갱신 및 sdk_runner_decisions 링크 추가.

## Issues / Risks

차단 사유 아님(기능·계약 영향 없음), 그러나 기록:

1. **`project_id` 메타데이터 품질 nit** — `cli.py:738`은 `project_id = Path(args.spec).parent.name`. spec이 `.../source/spec.md`이면 값이 `"source"`가 된다(smoke로 확인). `SourceSnapshot.project_id`는 로드되지만 코드 어디서도 읽히지 않으므로(grep 확인) 기능적 영향 없음. 다만 생성 manifest의 식별자 의미가 약함. 차후 개선 후보.
2. **상대 단일 `--out-dir` 경계** — `--out-dir runs`이면 `Path("runs").parent == "."` 이므로 snapshot이 cwd에 생성됨(smoke 확인). plan의 "sibling of --out-dir" 명세와는 엄밀히 일치하므로 결함 아님. 다만 사용자가 의도치 않은 위치를 만날 수 있음.
3. **mock_fixture candidate vs snapshot 분리** — candidate는 fixture 고정, snapshot은 `--spec`/`--rubric` 인자 기반. 정상 워크플로(`--spec`=fixture source)에서는 내용 일치하나, 둘이 다른 파일을 가리키면 integrity가 invalid로 분류한다(grounding이 더 엄격해진 방향, 회귀 아님). 이 불일치 경계는 테스트되지 않음 — 엣지 케이스로 기록.
4. **생성 manifest 스키마 검증 실패 경로**(`cli.py:755-759`)는 정상 입력에서 도달 불가에 가깝다(해시는 항상 64 hex, `project_id`는 fallback 보장). 방어 코드로 무해하나 전용 테스트는 없음.

## Verdict

**합격 (pass).**

근거: 계약(plan v1.32)이 내부 정합적이고, 구현이 계약 리터럴(경로·DOC id·sha·명시 우선)을 정확히 반영하며, "생성/미생성" 양방향 분기가 각각 회귀 테스트로 고정되어 boundary matrix에 빈 셀이 없다. snapshot↔원본 sha 정합·integrity validated·README 워크플로 일관성을 독립 재현으로 확인했고, 보고된 테스트 카운트(8/110/279, per-module 포함)가 실측과 정확히 일치한다. 발견된 4건은 모두 기능·계약에 영향 없는 품질 nit/엣지로 차단 사유가 아니다.

## Outstanding items

- 작업은 working tree에 uncommitted 상태 — 커밋은 소유자 권한.
- 위 Issues 1~4는 차단 아님. 처리 여부는 소유자 결정(특히 `project_id` 의미 개선).

## Reproduction

```bash
cd /workspace/assessment_poc
PYTHONPATH=src python3 -m pytest tests/test_cli_output_contract.py -k extract   # 8 passed
PYTHONPATH=src python3 -m pytest tests/test_cli_output_contract.py             # 110 passed
PYTHONPATH=src python3 -m pytest                                               # 279 passed
python3 -m py_compile src/assessment_harness/cli.py && git diff --check

# snapshot 생성 + sha 정합 smoke
rm -rf /tmp/snaptest && mkdir -p /tmp/snaptest
PYTHONPATH=src python3 -m assessment_harness.cli --output json extract \
  --spec fixtures/clean_assignment/source/spec.md \
  --rubric fixtures/clean_assignment/source/rubric.md \
  --runner mock_fixture --fixture-dir fixtures/clean_assignment \
  --runs 2 --out-dir /tmp/snaptest/runs
sha256sum /tmp/snaptest/source_snapshot/spec.md fixtures/clean_assignment/source/spec.md
```
