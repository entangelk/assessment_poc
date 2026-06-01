# Verification: Phase 2 Compacting Helper + Publication Mirror Boundary (2026-06-01)

## Subject metadata

- **Date**: 2026-06-01
- **Requester**: Owner (kdtyohan@gmail.com) — "AI가 작업한거 검증하고 의심해줘"
- **Verifier**: Claude (independent audit)
- **Target slice**:
  1. (docs) publication mirror boundary 재정의 — "안정화된 문서/이동 문서" 구분 제거, 전체 문서를 개발·publication copy freeze 이후 1회만 미러링. `docs/daily_logs/2026-06-01/work_log.md` 를 baseline 으로 기록. `publication_plan_v1.md` §7b / §6.5 / 변경이력, `HANDOFF.md` publication notes 갱신.
  2. (code) Phase 2 union compacting helper 신설 — `compact_validated_candidates` (`src/assessment_harness/compacting.py`), `schemas/compacting.schema.json`, `tests/test_compacting.py`, `schemas.py`/`__init__.py`/`test_models.py` 등록.
- **Canonical spec reference**: `docs/implementation_plan_assessment_harness_poc_v1.md` v1.30 — §5.0 Canonical ID/id_map (181-212), §5.1 Compacted Spec Item (214-242), §5.2 Compacted Rubric Item (244-278), §5.3 Compacted Trace Link (280-328), §5.4 integrity_status 모델 (398-424), §3 compacting 비분류 원칙 (59/143/145), §9 Phase 2 완료 기준 (1124-1158). 정책 키: `compacting.identity_basis.{spec_item,rubric_item,trace_link}`. 스키마: `compacting.schema.json`, 기존 `candidates.schema.json` / `id_map.schema.json`.
- **Publication spec reference**: `publication_plan_v1.md` §7b (bilingual timing), §6.5.
- **Source of work verified**: working tree, uncommitted (`git status`: M CHANGELOG/HANDOFF/publication_plan/schemas.py/__init__.py/test_models.py; ?? docs/daily_logs/2026-06-01, schemas/compacting.schema.json, src/.../compacting.py, tests/test_compacting.py).

## Scope

1. compacting helper 동작 정확성 — union 그룹핑, canonical ID, support/identity_basis/variants, id_map, trace remap.
2. §5.x 계약 ↔ helper/schema 리터럴 일치, 계약 자체 내부 정합성(run vs candidate framing).
3. `compacting.schema.json` ↔ §5.1-5.3 필수 필드 / 기존 `id_map.schema.json` 와의 정합성.
4. boundary matrix 완전성 (`test_compacting.py` 가 모든 fire / not-fire 분기를 잠그는가).
5. 문서 측 정량·정성 주장 정확성 (테스트 수, 스키마 수, 미러링 경계, 잔여 모순 표현).

## Methodology

- 코드 정독: `compacting.py` 전체(292 lines), `compacting.schema.json`, `test_compacting.py`, `id_map.schema.json`, `candidates.schema.json`, `schemas.py` SCHEMA_FILES.
- 계약 정독: plan §5.0-5.4, §9 Phase 2 (end-to-end, 발췌 아님).
- 동작 확인: `python3 -m pytest` (전체) 및 `git diff` 로 문서 변경분 검토.
- 문서 주장 재계산: 테스트 수 / 스키마 수 / 미러링 baseline / 잔여 "frozen·안정화" 표현 grep.

## Findings

### F1. compacting helper — 테스트된 분기에서 기능적으로 정확 (PASS)

- `compact_validated_candidates` 는 spec/rubric 을 먼저 그룹핑하여 canonical `S{n}`/`R{n}` 부여 후 trace link 의 run-local `rubric_id`/`spec_ids` 를 canonical 로 remap (`compacting.py:41-62`, 237-259) — §5.0 line 199 "먼저 compacting → canonical ID → 이후 remap" 순서와 일치.
- support(`total_valid_runs`/`found_in_runs`), `identity_basis`, `variants`, `id_map`(canonical_id/entity_type/run_refs) 모두 생성 (`materialize_groups` 209-223, `materialize_id_map` 226-234). §3 "자동 채택/분류 없음, support/variants/identity_basis 보존" 원칙 준수 — 모든 validated candidate 가 variant 로 보존되고 winner 선택 없음.
- 전체 스위트 `204 passed`(27 agent-runner / 48 cli / **4 compacting** / 8 fixture / 22 model / 95 rule) — HANDOFF "204 tests pass … 4 compacting" 주장 재현됨.

### F2. [BLOCKING — 계약 내부 불일치] `validated` 소비 단위가 run인지 candidate인지 spec이 자기모순, helper가 침묵으로 candidate 단위 선택

- plan은 **run 단위**로 서술: §5.4 line 403 "`compact`는 **validated run만** 소비한다", line 422 "validated 외 status는 compacting 단계에서 제외", §9 line 1151 "Rule 0에 실패한 **run**은 … compacting 대상에서 제외".
- 그러나 `integrity_status` enum 자체는 **candidate-entry 단위** 필드(`candidates.schema.json:39-52`, candidate_base). helper는 entry 단위로 필터(`compacting.py:174-180` — `entry.get("integrity_status") == "validated"`).
- 결과: 한 run이 spec candidate는 `validated`, trace candidate는 `invalid_reference` 인 혼합 상태일 때 helper는 그 run의 validated entry만 부분 소비한다. 이는 §5.4 "validated **run**만 소비" 의 run-단위 독해와 다른 해석을 **침묵으로 확정**한 것이다.
- CLAUDE.md "Spec-silent-but-code-enforced is a contract gap" 에 해당 — spec이 run/candidate 단위를 명시 통일하지 않았고 code가 한쪽을 골랐다. **계약을 candidate 단위(현 구현) 또는 run 단위 중 하나로 reconcile** 후 진행해야 한다. (현 구현이 더 granular하고 실용적이나, 결정은 Owner/계약의 몫.)

### F3. [HIGH] `total_valid_runs` 분모를 "validated candidate 를 1개 이상 가진 run 집합"으로 추론 — §5.3 의 run-단위 분모와 어긋날 수 있음

- §5.3 line 321: "`total_valid_runs`는 **invalid run을 제외한 전체 분모**". 즉 분모는 *유효 run 전체 수*.
- helper(`compacting.py:88-92`)는 모든 섹션의 validated candidate 들의 `agent_run_id` 합집합 크기로 계산. 즉 "validated candidate 가 하나도 없는 유효 run"은 분모에서 누락된다.
- helper 입력(`candidate_runs`, entry별 integrity_status)에는 **권위 있는 유효-run 목록이 없다.** 따라서 모든 유효 run이 항상 ≥1 validated candidate 를 갖는다는 가정이 깨지면 분모가 과소계상되어 support 비율이 부풀려진다. F2 와 동일 뿌리(run vs candidate)이며, 분모는 review 판단(low_support 등 §6 finding)에 직접 쓰이므로 영향이 더 크다. → 입력 계약에 유효-run 집합을 별도로 받거나, 분모 정의를 candidate 기반으로 계약에 명문화해야 한다.

### F4. [MEDIUM] compacted trace link 가 §5.3 정의 필드 `sources` / `reviewed_by` / `reviewed_at` 를 산출하지 않음

- §5.3 (302-310)은 compacted trace link 의 일부로 `sources`(provenance, `kind: agent_run` + run_id), `reviewed_by: null`, `reviewed_at: null` 을 명시한다(Phase 0/2 에서 null).
- helper 의 trace link 는 `proposed_item` deepcopy + remap 뿐(`compacting.py:251-259`)이라 위 세 필드를 생성하지 않으며, `compacting.schema.json` 의 `compacted_trace_link`(64-93)도 이들을 properties/required 에 포함하지 않는다(`additionalProperties:true` 로 허용만).
- provenance 는 별도 `id_map.run_refs` 로 부분 보존되나, §5.3 가 link entry 자체에 요구한 `sources`/review audit 필드는 누락. helper-level foundation 범위로 의도된 deferral 일 수 있으나 **spec ↔ schema/code 의 명시적 deviation 이므로 surface 필요**(계약 축소 또는 후속 보강 명문화).

### F5. [MEDIUM] `id_map` 의 두 거처(home)가 형태 불일치 — 잠재 통합 결함

- 기존 standalone `id_map.schema.json` 은 `{"id_map": [...]}` **wrapper 객체**를 요구(7-13행, `test_models.py` 도 wrapper 로 검증).
- 신설 compacting 출력의 `id_map` 은 **bare array**(`compacting.py:68-70`, `compacting.schema.json:21-24`).
- 두 곳에 `id_map_entry` 정의가 중복되며(형태 자체는 동일: canonical_id/entity_type enum/run_refs minItems1 — **모순은 아님**), compacting 출력의 `id_map` 값을 그대로 `id_map.schema.json` 으로 검증하면 wrapper 부재로 실패한다. `compact` CLI 미구현이라 현재는 latent 하나, id_map 산출물의 canonical 거처가 어디인지(독립 파일 vs compacting 번들) 결정·문서화 필요.

### F6. [LOW] spec identity key 가 라벨 "source" 대신 `source_ref.document_id` 사용

- §5.1 identity_basis 라벨은 `"source+section+normalized_text"` 이고 §5.1 예시는 `source: README.md` 와 `source_ref.document_id: DOC_SPEC` 를 **별도 필드**로 둔다.
- helper `_spec_identity_key`(`compacting.py:262-271`)는 `source_ref.document_id` 우선, 없으면 `item.source` fallback. 라벨이 가리키는 `source` 필드와 다른 필드를 키로 삼는 침묵 재해석. document_id 가 더 안정적이라 실무상 타당하나 라벨과의 불일치는 명문화 권장.

### F7. [HIGH — boundary matrix 미충족] variants/evidence-quote-remap/trace-drop 분기에 회귀 lock 부재

§5.x 의 "fire" 분기 중 다음이 `test_compacting.py` 에서 미잠금(CLAUDE.md: untraced branch = blocking):
- **variants 가 "동일성으로 판정됐으나 표현이 약간 다른 원본"을 보존**(§5.1/5.2/5.3 의 variants 존재 이유): 현 union 테스트(`test_compacting.py:114-146`)는 run 간 **완전히 동일한** text 를 병합할 뿐이다. `_normalize_text`(291)는 whitespace collapse + casefold 만 하므로, §5.2 예시처럼 단어("the") 가 추가된 description 은 **병합되지 않고 분리**된다 — 즉 spec 의 variants 예시는 helper 로 재현 불가하며, "정규화 후 동일하지만 raw 가 다른" 진짜 variant 경로는 **테스트가 전혀 없다.**
- **evidence_quote 의 spec_id remap**(`compacting.py:254-258`): 어떤 테스트도 remap 후 `evidence_quotes[].spec_id` 가 canonical 로 바뀌었는지 assert 하지 않는다.
- **trace link 가 unmapped rubric/spec 참조 시 None 으로 drop**(`compacting.py:248-249`): 미테스트이며, **drop 이 침묵(§3 의 review_queue 보존 원칙과 충돌 가능)** 인지도 spec-silent. validated trace link 가 invalid 처리된 item 을 참조하면 조용히 사라진다.

→ 위 셀들이 비어 있으므로 helper slice 의 test 차원은 "조건부".

### F8. [LOW — 문서 정확성] HANDOFF 의 "(plan v1.4 / §9 / §10.2)" 인용 오류

- `HANDOFF.md:29` 신설 줄이 compacting foundation 을 "(plan v1.4 / §9 / §10.2)" 로 인용. 그러나 (a) plan 현재 버전은 **v1.30**이고 이번 작업은 plan 버전을 bump 하지 않았다(implementation_plan diff 없음) — "v1.4" 는 명백한 오기. 다른 HANDOFF 항목은 도입 버전(v1.26/v1.28/v1.30)을 정확히 인용한다. (b) §10.2 는 "Agent Runner 계약 테스트" 인데 compacting 테스트는 독립 `test_compacting.py` 로 §10.2 소속이 아니다. → 인용 정정 필요(예: "plan §9 Phase 2 / §5.0-5.3").

### F9. 문서 미러링 경계 재정의 — 정확 (PASS)

- `publication_plan_v1.md` §7b 에서 "moving vs stabilizing(안정화)" 이분 제거, "all docs … after development and publication copy both freeze" 로 단일화(diff 확인). §6.5/변경이력 v1.2 항목도 동일 방향, 2026-06-01 work_log baseline 명시.
- `HANDOFF.md:42` "Publication docs drafted, not frozen" + `decisions.md` "frozen → 11-vignette draft" 정정. baseline 일자(2026-06-01) 일관.
- 잔여 모순 grep: `HANDOFF.md:182/188` 의 "frozen" 은 **Rule 리터럴 pair("frozen in plan vX")** 로 문서 안정화와 무관 — 모순 아님. line 1 / line 51 의 "on finalize / §6.5 flip" 은 새 방향과 일치.
- 정량 주장 재확인: 스키마 14→15(`schemas/` 15개 파일·SCHEMA_FILES 15개 일치), 테스트 200→204 + "4 compacting" 모두 재현. CHANGELOG 신규 행 내용 정확.

## Issues / Risks

| # | Severity | 내용 |
|---|---|---|
| F2 | Blocking | spec 의 run-단위 "validated run 소비" vs helper 의 candidate-entry 단위 필터 — 계약 내부 불일치를 침묵 확정 |
| F3 | High | `total_valid_runs` 분모를 candidate 존재 기반으로 추론 → 유효 run 과소계상 가능, support 비율 왜곡 |
| F7 | High | variants(다른 raw)·evidence_quote remap·trace drop 분기 회귀 lock 부재 (boundary matrix 미충족) |
| F4 | Medium | compacted trace link 가 §5.3 의 `sources`/`reviewed_by`/`reviewed_at` 미산출 |
| F5 | Medium | `id_map` bare array(compacting) vs wrapper(standalone schema) 형태 불일치, canonical 거처 미정 |
| F6 | Low | spec identity key 가 라벨 "source" 대신 `source_ref.document_id` 사용 |
| F8 | Low | HANDOFF "plan v1.4 / §10.2" 오기 |

## Verdict

- **문서 미러링 경계 slice: 합격(PASS).** "안정화 문서" 구분 제거·단일 미러링·baseline 기록이 일관되고 정량 주장 정확, 잔여 모순 표현 없음. (F8 인용 오기만 정정 권장.)
- **Phase 2 compacting helper slice: 조건부 합격(CONDITIONAL PASS).** 테스트된 경로에서 기능적으로 정확하고 `204 passed` 이나, (1) F2 의 run-vs-candidate 계약 불일치를 침묵 해결, (2) F7 의 variants/evidence-quote/trace-drop boundary lock 부재, (3) F3 분모 의미·F4/F5 계약↔스키마 deviation 이 미해결. CLAUDE.md 기준 "untraced branch / spec-silent-code-enforced" 는 full pass 를 막는다 — green bar 만으로 합격 처리 불가.

**조건:** F2(계약 단위 reconcile) + F3(분모 정의 명문화) + F7(3개 회귀 추가) 해결 시 합격으로 승격. F4/F5 는 "helper foundation 범위에서 의도적 deferral" 임을 계약/HANDOFF 에 명문화하면 risk 로 강등 가능.

## Outstanding items

- 작업 전체가 uncommitted. 위 조건 해결 여부에 따라 commit 전 보강 필요.
- 본 기록은 결함을 수정하지 않음(CLAUDE.md: verifier 는 침묵 수정 금지) — 다음 조치는 Owner 결정.

## Reproduction

```
python3 -m pytest -q                      # 204 passed
python3 -m pytest tests/test_compacting.py -q
git diff HANDOFF.md docs/publication_plan_v1.md CHANGELOG.md src/assessment_harness/schemas.py
ls schemas/ | wc -l                       # 15
grep -niE 'frozen|stabiliz|안정화' HANDOFF.md docs/publication_plan_v1.md
# 계약 대조: plan §5.0(199), §5.3(302-310,321), §5.4(403,422); compacting.py:88-92,174-180,251-259
```

---

## Re-verification (round 2, 2026-06-01) — 외부 수정분 독립 재검증

- **Requester**: Owner — "수정했다는데 다시 검증해줘. 내가 선택할 사항을 마음대로 했는지, 테스트·코드 자체 적합성도 봐줘."
- **Verifier**: Claude (independent). **Source**: working tree, uncommitted. **Suite**: `207 passed` (compacting **7**).
- **Granularity 사실 확인 (영향 평가의 전제)**: `agent_runners/integrity.py:157-169` `_with_integrity_status` 가 한 run의 모든 candidate에 **동일 status를 일괄** 부여한다. 따라서 실제 파이프라인 출력에는 mixed-status run이 존재할 수 없고, F2/F3 수정은 *정상 입력에서 동작이 바뀌지 않는* 계약 정합·하드닝이다(회귀 위험 0). live 오산이 아니라 계약 모호성 해소였다는 1라운드 성격 규정과 일치.

### 항목별 판정

- **F2 (run-level 소비) — 해결(PASS).** `_validated_run_id`(compacting.py:104-126)가 run의 모든 섹션 entry가 `validated` + well-formed + 단일 run_id 일 때만 그 run을 유효로 인정. `_iter_validated_candidates` 가 `agent_run_id in valid_run_ids` 로 gate(221). mixed-status run 통째 제외를 `test_..._excludes_mixed_status_run_as_one_unit`(185-197)가 **판별력 있게** 잠금 — 구 per-entry 로직이면 spec/rubric 이 비지 않아 이 테스트가 실패한다(2방향 guard 성립). **방향 선택은 임의가 아님**: plan §5.4(403) "validated **run**만 소비", §9(1151) "Rule 0 실패 **run** 제외" 가 run-level 을 명시 — 유일한 spec-정합 방향.
- **F3 (분모) — 해결(PASS).** `total_valid_runs = len(valid_run_ids)`(259) = 완전 유효 run 수. split 테스트(216-219)가 `total_valid_runs:2 / found_in_runs:["run_1"]` 로 분모≠분자 관계를 고정. 단, 이 split 케이스 자체는 구·신 구현 모두 2를 주어 *분모 수정만을* 판별하진 않는다 — 실판별은 mixed/exclude 테스트가 담당. 분모 정의도 §5.3(321) "invalid run 제외 전체 분모" 와 일치하는 유일 방향.
- **F7 (boundary lock 3종) — 해결(PASS).** ① raw variant: `test_..._preserves_raw_variants`(226-248) 가 whitespace/case 만 다른 두 raw text 가 1개 entry로 병합되며 variants에 **원문 그대로** 2건 보존됨을 확인(정규화-equal·raw-different 경로, 1라운드 미커버 분기). ② evidence_quote spec_id remap: single-run 테스트(110)가 canonical "S1" 로 remap 확인. ③ unmapped trace: `_remap_trace_link` 가 `CompactingInputError` raise(297-306), `test_..._rejects_unmapped_trace_references`(251-258)가 잠금. silent drop 제거됨.
- **F4 (trace provenance) — 해결(PASS).** trace link 에 `sources`(kind:agent_run+run_id), `reviewed_by:null`, `reviewed_at:null` 산출(materialize 264-270), 스키마 `compacted_trace_link.required` 에 셋 추가(66-76) + `source` $def enum 정의(103-114). reviewed_* 를 trace_link 에만 둔 것은 §5.3 와 일치. `sources` 를 spec/rubric item 에도 부여한 것은 plan §Phase3(1171, override 가 spec/rubric/trace `sources` 갱신)과 정합 — 과확장 아님.
- **F5 (id_map 거처) — 의도적 이월(ACCEPTED).** compacting 출력 `id_map` 은 bare array 유지하되, `test_..._unions`(132)가 `validate("id_map", {"id_map": compacted["id_map"]})==[]` 로 standalone wrapper 스키마와의 호환을 잠금. 파일 출력 계약(id_map.yaml wrapper)은 compact CLI slice 로 이월을 work_log/HANDOFF 에 명시. 단일 slice 범위 결정으로 타당.
- **F8 (문서 인용) — 해결(PASS).** HANDOFF:29 가 "plan v1.30 §5.0 / §9" 로 정정되고 신동작(mixed 제외/분모/CompactingInputError)을 정확히 기술. work_log 에 schema cross-`$ref` → local `$defs` 오프라인 수정 경위까지 기록.

### 신규 지적 (이번 수정으로 발생/잔존)

- **N1 (Low, cleanup): `compacting.schema.json:115-125` `id_map_document` $def 는 어디서도 `$ref` 되지 않는 orphan.** wrapper 검증은 standalone `id_map` 스키마로 수행하므로 이 def 는 dead. 제거하거나 top-level `id_map` 을 이 def 로 묶어 일원화 권장(기능 영향 없음).
- **N2 (Owner 판단거리, 결함 아님): unmapped trace reference 시 "전체 compaction hard-fail" 선택.** 유효 run 내부의 dangling 참조는 Rule 0(invalid_reference)에서 이미 걸러져 실입력에선 발생 불가하므로 방어적 guard 이고, 프로젝트 B5(fail-loud) 원칙과 정합 → 저위험. 다만 "해당 link 만 격리(review_queue) vs 전체 실패" 는 본래 Owner 선택지였다. 현재는 review_queue 미구현이라 fail-loud 가 합리적 잠정값이고 CLI slice 이월이 기록됨. **방향 자체는 합리적·기록됨**이나, 추후 review_queue 도입 시 "격리"로 바꿀지는 Owner 가 확정할 것.

### 종합 판정

- **compacting helper slice: 합격(PASS).** 1라운드 조건(F2 계약단위 reconcile · F3 분모 명문화 · F7 3-lock)이 모두 spec-정합 방향으로 충족되고, 판별력 있는 2방향 회귀로 잠겼다. 코드 자체 검토(결정성·deepcopy 비파괴·redundant-but-harmless per-entry gate·run-uniform 전제)에서 신규 결함 없음. 남은 것은 N1(미사용 def 정리)과 F5/N2 의 CLI-slice 이월뿐 — 모두 비차단.
- **임의 결정 점검 결과**: F2/F3/F4(reviewed_*)는 spec 명문에 따른 유일 방향, F4(sources 확장)·F7(remap)·F5 이월은 spec/원칙 정합. 유일한 진짜 선택지는 N2(hard-fail vs 격리)였고 합리적 잠정 선택 + 기록 완료. **Owner 권한을 침범한 임의 결정 없음.**
- **권고**: 커밋 전 N1 1줄 정리 권장(선택). 그 외 합격.

---

## Re-verification (round 3, 2026-06-01) — compact CLI orchestration 부분 검증

- **Requester**: Owner — "다음 작업(compact CLI) 부분 검증. 마음대로 결정한 것·테스트/코드 적합성 봐줘."
- **Verifier**: Claude (independent). **Source**: working tree, uncommitted (M cli.py, test_cli_output_contract.py, README/HANDOFF/case_study/work_log/CHANGELOG; helper foundation은 88e14bf 로 커밋됨).
- **Canonical scope**: plan v1.30 §8 CLI 계약(898-1080, compact/check usage 1027-1045), §4 review_queue(141), §5.x compacted 산출물, `review_queue.schema.json`.
- **Suite**: `211 passed`. 파일별 재집계 — cli 52 / agent-runner 27 / compacting 7 / fixtures 8 / models 22 / rules 95 = 211 (주장과 일치, CLI 48→52 +4).

### PASS 항목 (독립 재현)

- **산출물**: `_cmd_compact`(cli.py:477-)가 `spec_items.yaml` / `rubric_items.yaml` / `trace_links.yaml` / wrapper형 `id_map.yaml` / `review_queue.json` 5종 출력. 출력 전 `validate("compacting", …)` 및 `validate("review_queue", …)` 로 **쓰기 전 스키마 검증**(방어적). envelope 도 `_build_envelope→_ensure_envelope_valid`(1293)로 cli_output 검증. 테스트가 spec_items/trace_links/id_map 스키마 통과를 직접 assert.
- **통합(가장 중요)**: `test_compact_output_feeds_existing_check_flow` 가 clean_assignment 를 compact→check 로 흘려 `provisional_medium_count==2, blocking 0` 확인. **원본 fixture 를 직접 check 해도 동일(2 medium / 0 blocking)** 임을 재현 — compacting+canonical-ID remap 이 deterministic check 결과를 **변형하지 않음**을 입증. 스모크 단언은 정확.
- **review_queue**: `--review-queue-in` 보존 후 `invalid_run` append, 출력 순서 `[기존, invalid_run]` 잠금. `invalid_run` 은 `review_queue.schema.json:25` enum 에 **이미 정식 포함**(이번에 스키마 미수정) — 신규 임의 type 아님. 제외 run 의 `related_runs:["run_2"]` 식별 정확. §4(141) "무결성 실패로 제외된 후보" 기록 요구와 정합.
- **CLI↔helper run 유효성 일관성**: CLI `_candidate_run_statuses/_ids`(느슨) vs helper `_validated_run_id`(엄격) — `load_validated(…, "candidates")` 가 입력단에서 candidate_id/agent_run_id/shape 를 강제하므로 schema-valid 입력에서 두 판정이 일치(silent-drop 없음).
- **schema --command compact**: 계약·informational 10필드·exit code·next_actions 노출, 테스트로 잠금.

### 신규 지적

- **C1 [MEDIUM — 문서화된 CLI 계약 이탈 + Owner 결정거리]**: 구현은 `compact --candidates <files...>` 인데 **plan §8(1027-1034)은 `compact --runs-dir work/runs`** 로 명시(extract `--out-dir work/runs` → compact `--runs-dir` 흐름). `--review-queue-in/out` 도 §8 에 없음. 프로젝트 원칙은 **plan = SoT**(decisions C2)인데, README 는 `--candidates` 로 갱신되어 **SoT(§8)와 구현/README 가 어긋난다.** extract 미구현이라 runs-dir 생산자가 아직 없어 `--candidates` 가 실용적 잠정값인 건 합리적이나, **문서화된 시그니처를 침묵으로 바꾼 것**이라 surface 대상이다. → §8 을 `--candidates`(+queue 플래그)로 개정하든지, `--runs-dir` 로 맞추든지 Owner 가 확정해야 함. (이번 "마음대로 결정" 점검의 핵심 항목.)
- **C2 [LOW — 단일 진실원 위반]**: `valid_run_count`/`excluded_run_count`/invalid_run 판정을 CLI 가 helper `_validated_run_id` 재사용 없이 자체 loose 로직으로 **중복 구현**. schema-valid 입력에선 일치하나, 추후 helper 의 run-validity 정의가 바뀌면 envelope 카운트·review_queue 가 helper 실제 compaction 과 **드리프트**할 수 있다. 단일 predicate 재사용 권장.
- **C3 [LOW]**: compact 를 `--review-queue-in=직전출력` 으로 재실행하면 `entry_id="invalid_run_{index}"` 가 **중복 append**(스키마가 entry_id 유일성 미강제). append 모델은 요청대로지만 재실행 시 중복 entry_id 리스크.
- **C4 [LOW]**: `_load_review_queue` 가 기존 queue 의 `review_queue` 리스트만 보존하고 다른 top-level 키는 누락(generated_at 은 재생성). additionalProperties 허용 필드의 round-trip 손실.

### 종합 판정 (compact CLI slice)

- **합격(PASS, 부분 범위).** 산출물·스키마·통합(compact→check 무변형)·review_queue 보존/append 가 정확하고 판별력 있는 테스트로 잠겼다. 코드 자체에 기능 결함 없음.
- **단, C1 은 비차단이나 미해결 계약 이탈**: plan §8 이 SoT 인 프로젝트에서 문서화된 `--runs-dir` 시그니처를 `--candidates` 로 바꾼 것은 Owner 가 §8 개정 또는 플래그 변경으로 확정해야 한다. 나머지 C2~C4 는 정리 권고(비차단).

---

## Re-verification (round 4, 2026-06-01) — C1~C4 수정 독립 재검증

- **Requester**: Owner — "다시 검증해줘 (C1~C4 고쳤음)."
- **Verifier**: Claude (independent). **Source**: working tree, uncommitted. **Suite**: `214 passed`, 파일별 CLI 55 / agent-runner 27 / compacting 7 / fixtures 8 / models 22 / rules 95 = 214 (주장 일치). `py_compile` OK.

### 항목별 판정

- **C1 (CLI 계약 이탈) — 해결(PASS).** `compact` 이 plan §8 canonical `--runs-dir`(cli.py `_compact_candidate_paths`)를 1차 입력으로 추가, `*/candidates.yaml` + `*.candidates.yaml` 정렬 glob. `--candidates` 는 저수준 보조 입력으로 유지, **동시 지정 시 invalid_input/exit 2** 로 거부. plan §8 은 원래 `--runs-dir` 라 **구현이 이제 SoT 와 일치 — 플랜 수정 불필요**(`git diff` 상 implementation_plan 무변경, 정확). README:85-99 / HANDOFF:30 / work_log 가 "공식=runs-dir, 보조=candidates" 로 일치 갱신. **work_log:149 에 Owner confirmation 기록** → 더 이상 침묵 결정 아님. 테스트 `test_compact_cli_accepts_plan_canonical_runs_dir`(runs/run_001/candidates.yaml glob), `..._rejects_runs_dir_and_candidates_together`(exit 2) 가 잠금. 독립 탐침으로 추가 경계 확인: neither→"requires --runs-dir or --candidates", empty runs-dir→"no candidate artifacts found", both→exit 2 (모두 argparse crash 아닌 구조화 envelope).
- **C2 (단일 진실원) — 해결(PASS).** helper `_validated_run_id` → public `validated_candidate_run_id`(compacting.py:104, 로직 불변) 로 노출하고 CLI `_invalid_run_review_entries` / `_valid_candidate_run_count` 가 **동일 predicate 재사용**. 이제 envelope `valid_run_count`·`excluded_run_count`·review_queue invalid_run 판정·helper `total_valid_runs` 가 한 정의에서 파생 → 드리프트 제거. (`_candidate_run_statuses/_ids` 는 queue 의 설명용 metadata 로만 잔존, 유효성 결정에는 미사용 — 적절.)
- **C3 (중복 append) — 해결(PASS).** `_append_review_queue_entries` 가 기존 entry_id 집합과 대조해 중복 entry_id skip. `test_..._does_not_duplicate_existing_invalid_run_entry`(기존 invalid_run_1 재투입 → count 1 유지) 가 잠금. idempotent 재실행에서 정확.
- **C4 (metadata 보존) — 해결(PASS).** `_load_review_queue` 가 `dict(payload)` 로 top-level 키 전부 보존 후 `review_queue` 만 list 복사로 정규화. (이후 `generated_at` 은 의도적으로 현재시각 재기록 — 정상.)

### 잔여 관찰 (비차단, 신규 1건)

- **R4-1 [LOW, 견고성]**: dedup 키인 `entry_id="invalid_run_{index}"` 가 **위치 기반**이다. 의도된 idempotent 재실행(동일 입력 + 직전 queue)에선 정확하나, *서로 다른 candidate 집합*에 직전 queue 를 재투입하면 같은 index 의 의미상 다른 invalid_run 이 동일 entry_id 충돌로 skip 될 수 있다. 문서화된 파이프라인에선 비현실적 시나리오라 비차단이나, 추후 entry_id 를 candidate_path/run_id 기반 content id 로 바꾸면 더 견고. (선택 개선.)
- **R4-2 [INFO]**: plan §8 본문은 `--candidates` 를 명시하지 않는다(README/HANDOFF/work_log 에만 보조 입력으로 기술). Owner 가 "보조·비공식" 으로 확정했으므로 모순은 아니나, §8 에 "수동/저수준 대체 입력" 한 줄 추가하면 SoT 자기완결성↑. (선택.)

### 종합 판정

- **compact CLI slice + C1~C4 follow-up: 합격(PASS).** 4개 지적이 모두 spec-정합 방향으로 해결되고 판별력 있는 회귀 + 독립 경계 탐침으로 확인됨. C1 은 Owner confirmation 까지 기록되어 임의 결정 잔존 없음. 코드 자체 신규 결함 없음.
- **임의 결정 점검**: `--candidates` 보조 유지·동시거부·runs-dir glob 레이아웃 모두 Owner 승인 또는 spec-정합. **Owner 권한 침범한 미기록 결정 없음.**
- 잔여 R4-1/R4-2 는 선택적 개선이며 커밋을 막지 않는다.

---

## Re-verification (round 5, 2026-06-01) — extract CLI (mock_fixture) 슬라이스 검증

- **Requester**: Owner — "다음 작업(extract) 검증. Option A(mock_fixture 전용)대로 구현."
- **Verifier**: Claude (independent). **Source**: working tree, uncommitted (M cli.py 외 8파일; 직전 compact slice 는 4fe9f92 로 커밋됨).
- **Canonical scope**: plan v1.30 §8 extract usage(1020-1028), §5.4 integrity 모델, §5.4.1 agent_trace(426-433), §9 Phase 2 작업/완료기준(1136-1158), §13(1292). 스키마: `candidates`, `agent_trace`.
- **Suite**: `219 passed`, CLI 60 / 나머지 일치. `py_compile` OK.

### PASS 항목 (독립 재현)

- **무결성 우회 없음(핵심)**: extract 가 `normalize_result_candidates` → `classify_deep_candidate_run_integrity(candidates, audit_trace, snapshot)` 를 **실제로 실행**해 분류 결과(`integrity.candidates`)를 기록 — `validated` 를 블라인드 스탬프하지 않는다. §5.4 staged 모델 준수.
- **end-to-end 파이프라인**: 직접 `extract(clean_assignment, runs=3) → compact --runs-dir → check` 실행 → compact `total_valid_runs:3, found_in_runs:[run_001,002,003]`, check `blocking 0 / medium 2` (원본 fixture 직접 check 와 동일). **구현된 전 구간이 의미 보존하며 일관 동작.**
- **산출물 레이아웃**: `run_###/candidates.yaml` + `agent_trace.audit.jsonl` + `agent_trace.raw.jsonl`. 테스트가 candidates→`candidates` 스키마, audit event 각각→`agent_trace` 스키마 통과를 assert. compact `*/candidates.yaml` glob 과 호환(테스트 + 수동 확인).
- **run_id 재작성 정합**: mock 은 결정적이라 동일 산출 → `_with_extract_run_id` 가 candidates 와 audit/raw trace 의 run_id 를 `run_{index}` 로 **일괄 재작성 후** 분류 → 귀속(candidate.agent_run_id ↔ audit run_id) 일치 유지, N-run support 정확. 테스트로 잠금.
- **§8 시그니처 보존**: `--spec/--rubric/--runner/--runs/--out-dir` 유지(§8 그대로), `--source-manifest/--fixture-dir/--policy` 는 **additive**. compact C1 식 치환-이탈 아님.
- **fail-loud 경계(독립 탐침 전부 invalid_input/exit 2, argparse crash 아님)**: `--runs 8/0`→"between 1 and 7", `--runner claude_sdk`→"real SDK runners are deferred"(조용한 stub 아님), mock+`--fixture-dir` 누락→거부, spec 파일 부재→거부, fixture 에 source_manifest 없고 `--source-manifest` 미지정→명확 거부. `--runs` 1..7 은 §9(최대 7) 정합, 기본 3 정합.
- **--source-manifest optional 결정**: deep 분류는 snapshot grounding 이 필요한데 §8 예시엔 `--source-manifest` 가 없다 → 필수로 만들면 계약 drift. optional 로 두고 mock 은 `--fixture-dir/source_manifest.yaml` 기본 사용. **유일하게 합리적 방향이고 Owner 가 인지·기록함 → 임의 결정 아님.**
- `schema --command extract` 계약(informational 8필드·exit 0/2/3·fix_input) 테스트로 잠금.

### 지적

- **E1 [MEDIUM — boundary 미충족]: extract 의 invalid-run 분기에 회귀 lock 부재.** invalid_run_count 단언은 happy-path `== 0`(test:1557) 뿐이다. 직접 reference_integrity 를 mock extract 하면 **valid 0 / invalid 1 + `integrity_errors.json` 생성**(기능 정상 확인)이지만, 이 "실패 격리" 경로 — 무결성 모델의 존재 이유 — 를 잠그는 테스트가 없다. 실패 fixture 로 `invalid_run_count>0` / `integrity_status != validated` / `integrity_errors.json` 산출을 단언하는 회귀 추가 필요(under-strict guard).
- **E2 [LOW — 계약 명칭]**: 실패 run 에 `integrity_errors.json`(ad-hoc) 을 쓴다. plan 의 canonical 무결성 산출물은 `integrity_diagnostics.json`(§5.4:422)이고 제외 사유는 compact 가 review_queue `invalid_run` 으로 이미 기록. `integrity_errors.json` 을 extract-local 디버그 산출물로 문서화하거나 integrity_diagnostics 계약에 맞출지 정리 권장.
- **E3 [LOW — forward-looking 부채]**: `_with_extract_run_id` 가 **모든 runner** 에 대해 run_id 를 `run_{index}` 로 덮어쓴다. 결정적 mock 엔 필수·정확하나, 실제 SDK runner 도입 시 real run 의 고유 run_id(SDK trace 상관·provenance)를 파괴하므로 **mock 전용으로 분기해야 한다.** 현재 mock 만 허용이라 latent.
- **E4 [INFO — 해석 주의]**: mock 은 동일 fixture 를 N회 replay → support 가 인위적 N/N(found_in_runs run_001..N). 파이프라인 배선/데모용으로 타당하나 실제 agent 합의가 아님. 실제 divergence 는 real runner 필요(이미 deferral·문서화됨).
- **E5 [INFO]**: plan §8 본문이 mock_fixture/`--fixture-dir`/`--source-manifest` 경로를 명시하지 않음(README/HANDOFF/work_log 에만). R4-2 와 동일하게 §8 한 줄 보강 시 SoT 자기완결성↑(선택).

### 종합 판정

- **extract CLI(mock_fixture) 슬라이스: 합격(PASS).** 무결성 분류를 실제 수행하고 end-to-end 파이프라인이 의미 보존하며, 모든 거부 경계가 fail-loud 로 독립 확인됨. Option A·`--source-manifest` optional·claude_sdk 거부 모두 합의/§8-정합/기록됨 → **임의 결정 없음.**
- **단 E1(실패-격리 경로 무테스트)은 비차단이나 커밋 전 보강 권장** — CLAUDE.md 기준 "untested fire branch". E2~E5 는 선택 정리/주의.
- 다음 선택지(verify 를 mock 먼저 닫기 vs 여기서 커밋)는 Owner 결정 사항. 커밋 시 E1 회귀 1개 추가를 권한다.

---

## Re-verification (round 6, 2026-06-01) — E1~E3 수정 독립 재검증

- **Requester**: Owner — "E1~E3 고쳤대, 다시 검증."
- **Verifier**: Claude (independent). **Source**: working tree, uncommitted (M cli.py / integrity_diagnostics.schema.json 외). **Suite**: `220 passed`, CLI 61. `py_compile` OK.

### 항목별 판정

- **E1 (invalid-run 회귀) — 해결(PASS).** `test_extract_mock_fixture_isolates_invalid_run_with_diagnostics`(test:1641) 가 reference_integrity 를 mock extract → `valid_run_count==0`, `invalid_run_count==1`, candidates 의 integrity_status 가 `!= {"validated"}`, `summary.high>0`, diagnostics 非빈, **그리고 `validate("integrity_diagnostics", diagnostics)==[]` 로 생성 payload 의 스키마 통과까지 잠금**. under-strict guard 성립.
- **E2 (canonical 무결성 산출물) — 해결(PASS).** 실패 run 이 `integrity_diagnostics.json`(ad-hoc `integrity_errors.json` 제거; 테스트가 `not integrity_errors.json.exists()` 단언) 을 쓰고, payload(`diagnostics[]`+`summary{total,high,…}`)가 `integrity_diagnostics.schema.json` 구조와 부합. `candidate_run_integrity_error` 를 enum 에 추가(스키마 diff 확인)하여 비-rule_zero 에러 fallback 을 정식화. **독립 탐침**: reference_integrity extract 의 실제 diagnostics 코드가 `duplicate_spec_id`/`dangling_rubric_reference`/`evidence_quote_*` 등 8종으로 정확히 추출되고 전부 enum 에 존재(`_extract_integrity_error_code` 가 `rule_zero/<code>:` 에서 `<code>` 분리). emitted rule_zero 코드 ⊆ enum (MISSING none).
- **E3 (run_id rewrite mock 전용) — 해결(PASS).** `_with_extract_run_id`→`_with_mock_extract_run_id`, 호출부가 `if isinstance(runner, MockFixtureRunner):` 로 gate. 현재 mock 만 허용이라 동작 동일하나, 실제 SDK runner 도입 시 고유 run_id 보존 — latent debt 해소. candidate.agent_run_id ↔ audit run_id 귀속 일치는 유지(round 5 확인分 불변).

### E4/E5 — Owner 정보성 유보 (타당)

- E4(mock N회 replay = 인위적 N/N support)·E5(plan §8 mock 경로 미기재)는 구현 변경 없이 정보성 유지. mock 한정·SDK pending 이 이미 문서화돼 있고 §8 보강은 별도 SoT 개정 작업으로 미루는 판단 — 합리적, 기록됨.

### 잔여 관찰 (비차단·선택)

- **R6-1 [LOW, parity]**: extract 는 candidates.yaml / agent_trace.*.jsonl / integrity_diagnostics.json 을 **쓰기 전 스키마 검증 없이** 기록한다(compact 는 compacting/review_queue 를 쓰기 전 validate). E1 이 reference_integrity 의 diagnostics 를 사후 검증하고 enum+fallback 설계로 invalid code 가 사실상 불가능하므로 위험은 미미하나, fail-loud parity 를 위해 extract 도 산출물 validate-before-write 를 두면 일관적. (선택.)

### 종합 판정

- **extract CLI(mock_fixture) 슬라이스 + E1~E3 follow-up: 합격(PASS).** 3개 지적이 모두 해결되고, E1 은 스키마 검증까지 포함한 판별력 있는 회귀로 잠겼으며, E2 의 diagnostics 코드 granularity·enum 정합을 독립 탐침으로 확인. E3 은 forward debt 해소. **임의 결정 잔존 없음** (E4/E5 유보는 Owner 기록).
- 커밋 가능 상태. R6-1 만 선택적 후속이며 차단 아님.
- 본 검증 문서는 라운드 1~6 누적 audit trail 로, round 5 의 E1~E3 지적은 본 라운드에서 "해결"로 종결됨 — 커밋 시 이 문서를 함께 포함하면 follow-up note 가 이미 반영된 상태다.

---

## Re-verification (round 7, 2026-06-01) — R6-1 parity follow-up

- **Requester**: Owner — "R6-1만 남았는데 어떻게 생각하니." Owner accepted the fail-loud parity cleanup.
- **Verifier**: Codex follow-up. **Source**: working tree, uncommitted.
- **Scope**: extract-generated artifact validation before write: `candidates.yaml`, `agent_trace.audit.jsonl`, and run-local `integrity_diagnostics.json`.

### 판정

- **R6-1 — 해결(PASS).** `extract` now validates generated candidates with `validate("candidates", ...)`, audit trace events with `validate("agent_trace", ...)`, and run-local diagnostics with `validate("integrity_diagnostics", ...)` before writing artifacts. On generated candidate schema failure it returns structured `invalid_input` / exit `2` and does not write `run_###/candidates.yaml`.
- Added `test_extract_validates_generated_candidates_before_write`, which builds a malformed mock fixture, verifies the structured rejection, and asserts `candidates.yaml` was not written.

### Verification

- `python3 -m py_compile src/assessment_harness/cli.py src/assessment_harness/__init__.py`
- `python3 -m pytest tests/test_cli_output_contract.py::test_schema_command_returns_extract_contract tests/test_cli_output_contract.py::test_extract_mock_fixture_writes_validated_candidate_runs tests/test_cli_output_contract.py::test_extract_mock_fixture_output_feeds_compact_runs_dir tests/test_cli_output_contract.py::test_extract_mock_fixture_isolates_invalid_run_with_diagnostics tests/test_cli_output_contract.py::test_extract_validates_generated_candidates_before_write tests/test_cli_output_contract.py::test_extract_mock_fixture_rejects_unknown_runner tests/test_cli_output_contract.py::test_extract_rejects_runs_outside_plan_limit -q` → 7 passed.
- `python3 -m pytest tests/test_cli_output_contract.py tests/test_agent_runner_contract.py tests/test_compacting.py tests/test_models.py -q` → 118 passed.
- `python3 -m pytest -q` → full suite passed.
- `python3 -m pytest --collect-only -q` → 221 tests collected: agent-runner 27, CLI 62, compacting 7, fixtures 8, models 22, rules 95.

### Final Verdict

- **extract CLI(mock_fixture) slice: 합격(PASS).** E1~E3 and R6-1 are closed. E4/E5 remain informational/optional only. No blocking or conditional items remain for this slice.
