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
