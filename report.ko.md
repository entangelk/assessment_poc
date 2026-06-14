<p align="center">
  <a href="./report.md"><img src="https://img.shields.io/badge/Language-EN-6B7280?style=for-the-badge" alt="English"></a>
  <a href="./report.ko.md"><img src="https://img.shields.io/badge/Language-KO-111111?style=for-the-badge" alt="한국어"></a>
</p>
<p align="center"><sub>Switch language / 언어 전환</sub></p>

# Assessment Harness PoC 결과 보고서

작성일: 2026-06-14 KST  
대상: `examples/deskhive_assignment`, `examples/pulse_assignment`  
산출물: 반복 실행 결과는 `work/poc_report_runs/run{1,2,3}/...` 아래에 보관했다.

## 결론

`examples/`의 두 샘플은 현재 프로젝트의 검증 방식으로 정상 실행된다. 동일한 공식 흐름을 3회 반복했을 때 두 샘플 모두 같은 finding 분포를 재현했고, Rule 0 reference integrity 진단은 전 회차에서 0건이었다.

이 결과는 "assessment design 자체를 검토한다"는 PoC 목적에 맞다. `check`는 후보자의 합격/불합격을 직접 내리지 않고 `provisional_findings`를 생성하며, 안전한 기본 final review 초안 때문에 `gate`는 `pending_review`로 멈춘다. 즉 현재 결과는 실패가 아니라 "사람 검토가 필요한 설계 리스크를 안정적으로 찾아냈다"는 의미다.

단, 이번 검증은 live LLM extraction이 아니다. `deterministic_extraction` runner와 `mock_fixture` semantic verifier를 사용한 offline wiring/grounding 검증이다. real SDK runner는 프로젝트 문서상 아직 deferred scope다.

## 검증 방법

각 샘플마다 아래 흐름을 3회 반복했다.

```bash
PYTHONPATH=src python3 -m assessment_harness.cli extract \
  --spec examples/<sample>/spec.md \
  --rubric examples/<sample>/rubric.md \
  --runner deterministic_extraction \
  --runs 3 \
  --policy config/policy.yaml \
  --out-dir work/poc_report_runs/runN/<sample>/runs

PYTHONPATH=src python3 -m assessment_harness.cli compact ...
PYTHONPATH=src python3 -m assessment_harness.cli verify ...
PYTHONPATH=src python3 -m assessment_harness.cli check ...
PYTHONPATH=src python3 -m assessment_harness.cli report ...
PYTHONPATH=src python3 -m assessment_harness.cli review ...
PYTHONPATH=src python3 -m assessment_harness.cli gate ...
PYTHONPATH=src python3 -m assessment_harness.cli materialize-review ...
```

추가 확인:

- `PYTHONPATH=src python3 -m assessment_harness.cli schema --command check --output json`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q -p no:cacheprovider`
- DeskHive: `python3 scripts/show_symptoms.py`
- Pulse: `go version` 확인

## 3회 반복 결과

### DeskHive

| 회차 | extract | check | high | medium | info | findings | Rule 0 diagnostics | gate |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 1 | success, valid_run_count=3 | provisional_findings | 3 | 11 | 0 | 14 | 0 | pending_review, pending=14 |
| 2 | success, valid_run_count=3 | provisional_findings | 3 | 11 | 0 | 14 | 0 | pending_review, pending=14 |
| 3 | success, valid_run_count=3 | provisional_findings | 3 | 11 | 0 | 14 | 0 | pending_review, pending=14 |

Finding type 분포는 세 회차 모두 동일했다.

| Type | Count | 해석 |
|---|---:|---|
| `unconfirmed_trace_coverage` | 7 | Phase 0 semantic status가 아직 human accepted가 아니므로 정상적인 provisional coverage 경고 |
| `possible_orphan_scored_rubric_item` | 1 | R5의 trace quote가 spec과 verbatim 일치하지 않도록 의도적으로 심은 신호 |
| `uncovered_must_spec_item` | 1 | AI usage log가 must spec인데 scored rubric coverage가 없음 |
| `optionality_mismatch` | 1 | optional dashboard panel이 10점 scored rubric으로 잡힘 |
| `double_scored_spec` | 1 | CTO report가 scored와 bonus 양쪽에서 추적됨 |
| `bonus_grades_mandatory_only` | 2 | bonus rubric이 이미 required work를 보상함 |
| `mandatory_spec_bonus_only_traced` | 1 | must spec이 bonus-only로만 커버됨 |

DeskHive 코드베이스 직접 재현도 README/spec와 일치했다. `scripts/show_symptoms.py`는 B1 `inf`, B2 freeze 6일 미반영, B3 free+paid pass 합산, B4 KST 월경계 불일치, B5 항상 `H1` 추천을 재현했다.

### Pulse

| 회차 | extract | check | high | medium | info | findings | Rule 0 diagnostics | gate |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 1 | success, valid_run_count=3 | provisional_findings | 2 | 7 | 1 | 10 | 0 | pending_review, pending=10 |
| 2 | success, valid_run_count=3 | provisional_findings | 2 | 7 | 1 | 10 | 0 | pending_review, pending=10 |
| 3 | success, valid_run_count=3 | provisional_findings | 2 | 7 | 1 | 10 | 0 | pending_review, pending=10 |

Finding type 분포는 세 회차 모두 동일했다.

| Type | Count | 해석 |
|---|---:|---|
| `unconfirmed_trace_coverage` | 6 | Phase 0 semantic status가 아직 human accepted가 아니므로 정상적인 provisional coverage 경고 |
| `possible_orphan_scored_rubric_item` | 1 | R4가 malformed line을 nonzero exit으로 요구해 spec의 skip-and-continue와 충돌 |
| `optionality_mismatch` | 1 | optional windowing이 15점 scored rubric으로 잡힘 |
| `orphan_bonus_rubric_item` | 1 | Prometheus bonus가 spec에 없는 항목이며 informational로만 기록됨 |
| `uncovered_must_spec_item` | 1 | malformed input "must not crash"가 qualitative-only coverage에 머묾 |

Pulse reference solution은 문서상 핵심 요구와 대체로 맞는다. 다만 현재 환경에는 Go toolchain이 없어 `go test ./...`와 `go run`은 실행하지 못했다. `README.md`와 `notes.md`가 이미 이 제한을 밝히고 있으므로 문서와 상태는 일치하지만, "Go reference solution 실행 검증 완료"라고 주장하면 안 된다.

## 결과가 의도와 맞는지

맞다.

DeskHive는 복잡한 maintenance assignment에서 Rule 1, Rule 2, Rule 3, L1, L5, L6를 모두 건드리도록 설계되어 있고, 실제 결과도 그 분포를 안정적으로 재현했다. R5 non-verbatim trace, R8 optional scored item, RB1 must-but-bonus-only, R7/RB2 double scoring이 기대한 finding으로 나타났다.

Pulse는 다른 언어/다른 과제 유형에서 DeskHive와 다른 branch를 보여주도록 설계되어 있고, 실제 결과도 그렇게 나왔다. 특히 `orphan_bonus_rubric_item` informational branch와 qualitative-only Rule 2 boundary가 DeskHive와 다른 신호로 확인됐다.

Rule 0 diagnostics가 모든 회차에서 0건인 것도 중요하다. 즉 finding들은 source grounding이나 schema/reference 깨짐 때문에 생긴 것이 아니라, compacted artifact가 유효한 상태에서 설계상 검토 포인트로 발생한 것이다.

## 발견한 리스크와 주의점

1. **Live SDK runner 검증은 아니다.**  
   현재 `deterministic_extraction`은 rubric의 `Traceable spec quote` 힌트에서 후보를 만드는 offline stand-in이다. 이 보고서는 샘플과 harness pipeline의 재현성 검증이지, 실제 LLM runner 품질 검증이 아니다.

2. **Semantic verifier는 conservative mock이다.**  
   이번 실행의 `semantic_verification_count`는 0이고 report에도 semantic verification proposal이 없다. 그래서 `unconfirmed_trace_coverage`가 남는 것은 정상이다.

3. **DeskHive 문서 표현에 작은 혼선 가능성이 있다.**  
   candidate spec은 B1에 대해 finite number를 요구하지만, codebase business rules는 no-usage case의 표현으로 `null` 가능성을 언급한다. spec을 canonical로 보면 문제는 작지만, 공개 샘플에서는 후보자/평가자 혼선을 줄이려면 표현을 맞추는 편이 좋다.

4. **Pulse reference solution은 이 환경에서 실행 검증하지 못했다.**  
   `go version`이 `/bin/bash: line 1: go: command not found`로 실패했다. Go가 설치된 환경에서 `go test ./...`, `go run . testdata/events.csv`, `go run . --json testdata/events.csv`를 다시 확인해야 한다.

5. **Pulse public CLI surface 테스트가 더 있으면 좋다.**  
   코드와 테스트데이터는 spec과 대체로 맞지만, file-vs-stdin 동등성, stderr skipped-count, JSON output이 `testdata/expected.json`과 일치하는지, text output shape 같은 public surface는 현재 테스트로 강하게 잠겨 있지 않다.

6. **Review queue 경로는 구분해서 해석해야 한다.**  
   `check --review-queue-out`은 DeskHive에서 lint safeguard queue 2건을 만들지만, Phase 2 `compact`/`verify`의 통합 queue는 이번 정상 실행에서 비어 있다. 현재 README가 경고하듯 Phase 0 check queue를 통합 queue 경로에 직접 쓰지 않는 구조다.

## 최종 판단

`examples/`는 PoC 데모용 샘플로 적절하게 세팅되어 있다. 세 번 반복한 공식 workflow가 동일한 결과를 냈고, finding 분포도 샘플 문서가 의도한 설계 신호와 맞는다.

보고서/포트폴리오 문맥에서는 다음처럼 표현하는 것이 안전하다.

> The examples validate the deterministic harness workflow and demonstrate stable assessment-design findings across two different assignment archetypes. They do not yet validate live LLM extraction quality; real SDK runners remain future work.
