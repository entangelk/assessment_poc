<p align="center">
  <a href="./evaluation.md"><img src="https://img.shields.io/badge/Language-EN-6B7280?style=for-the-badge" alt="English"></a>
  <a href="./evaluation.ko.md"><img src="https://img.shields.io/badge/Language-KO-111111?style=for-the-badge" alt="한국어"></a>
</p>
<p align="center"><sub>Switch language / 언어 전환</sub></p>

# 평가 — 측정값

> **Moving snapshot.** 이 프로젝트는 활발히 개발 중이므로, 아래의 모든 수치는
> rule·fixture·테스트가 진화하면서 함께 바뀐다. 여기 적힌 숫자는 날짜가 박힌
> 스냅샷이며 **실제 실행에서 재계산한 값이지, 받아 적은 값이 아니다.** 각 표에는
> 재현 명령이 함께 실려 있다. *형태와 동작*(어떤 fixture가 어떤 finding을
> 일으키는지, 어떤 입력이 어떤 순서로 거부되는지)을 안정적인 주장으로 보고,
> *수치*는 "스냅샷 날짜 기준으로 참"으로 받아들이면 된다.
>
> **Snapshot:** 2026-06-07 · plan v1.32 · Python 3.12.3 · direct `pytest`
> (`PYTHONPATH=src`). 정본 개발 환경은 Docker(`python:3.11-slim`)다.
> [재현](#reproduction) 참고.

## 테스트 스위트

`279 passed` (전체 스위트, 이 스냅샷 기준).

| Test module | Count | Locks |
|---|---:|---|
| `tests/test_rules.py` | 95 | Rule 0–3 + lint L1/L5/L6, 각각 under-strict + over-strict guard 포함 |
| `tests/test_cli_output_contract.py` | 110 | envelope/exit-code 계약, `schema` introspection, `extract`/`compact`/`verify`, semantic-verification 소비, `review`/`gate`/`materialize-review` 분기 |
| `tests/test_agent_runner_contract.py` | 27 | runner protocol, candidate schema, normalization, staged + deep integrity |
| `tests/test_tools.py` | 10 | framework-neutral read-only source/rubric tools |
| `tests/test_compacting.py` | 7 | compacting helper union, id_map lineage, run 제외, trace-reference remapping |
| `tests/test_models.py` | 22 | YAML/schema loader, source-snapshot sha256, span 접근 |
| `tests/test_fixtures.py` | 8 | grounded end-to-end fixture 동작 |
| **Total** | **279** | |

모든 rule branch는 **양방향**으로 잠겨 있다(원래 버그가 테스트를 다시 실패시킬 수
있고, *동시에* 정상 케이스를 잘못 잡는 과교정도 실패한다). 이는 `CLAUDE.md` /
`AGENTS.md`에 기술된 이 프로젝트의 회귀 규율이다.

## grounded fixture에 대한 `check` 동작

각 행은 해당 fixture의 자체 `policy.yaml`과 `source_manifest.yaml`을 사용한 실제
`check` 실행이며 `--output json` 기준이다. 수치는 envelope에서 곧장 가져온
provisional finding count `(high, medium, informational)`다.

| Fixture | status | exit | (high, med, info) | review_queue | exercises |
|---|---|---:|---|---:|---|
| `clean_assignment` | `provisional_findings` | 0 | (0, 2, 0) | 0 | automation baseline — `unconfirmed_trace_coverage` 2건 (link pending) |
| `orphan_scored_rubric` | `provisional_findings` | 0 | (1, 1, 1) | 0 | Rule 1 세 branch 모두 (orphan scored / unconfirmed / orphan bonus) |
| `uncovered_must_spec` | `provisional_findings` | 0 | (1, 5, 0) | 1 | Rule 2 coverage gap, bonus-only must에서 L5/L6 co-firing |
| `optionality_mismatch` | `provisional_findings` | 0 | (2, 1, 0) | 0 | Rule 3 optional-only scored weight가 threshold 이상 |
| `bonus_misuse` | `provisional_findings` | 0 | (1, 5, 1) | 2 | lint L1/L5/L6 + Rule 2 중첩, mutual-exclusion 경계 포함 |
| `reference_integrity` | `invalid_input` | 2 | — | — | Rule 0가 입력을 실패시킴: `high_integrity_count=9` (8개 distinct code; `evidence_quote_missing_for_spec_id`가 두 번 발생) |

관찰된 `next_actions`(중복 제거) — agent-consumable 검토 힌트:

| Fixture | `next_actions` types |
|---|---|
| `clean_assignment` | `review_unconfirmed_trace_coverage` |
| `orphan_scored_rubric` | `review_orphan_rubric`, `review_orphan_bonus_rubric`, `review_unconfirmed_trace_coverage` |
| `uncovered_must_spec` | `review_uncovered_must_spec`, `review_bonus_mandatory_only`, `review_mandatory_spec_bonus_only`, `review_unconfirmed_trace_coverage` |
| `optionality_mismatch` | `review_optionality_mismatch`, `review_unconfirmed_trace_coverage` |
| `bonus_misuse` | `review_double_scoring`, `review_bonus_mandatory_only`, `review_mandatory_spec_bonus_only`, `review_uncovered_must_spec`, `review_orphan_bonus_rubric`, `review_unconfirmed_trace_coverage` |
| `reference_integrity` | `fix_reference_integrity` |

## 입력-계약 가드 (fail loud, 조용한 skip 없음 — [decisions.md](decisions.ko.md) §B5 참고)

load-bearing 입력은 필수다. 하나라도 누락하면 조용한 skip이나 argparse usage
텍스트 대신 구조화된 typed recovery action을 반환한다. **manifest가 policy보다
먼저 검증**되므로, 둘 다 없으면 manifest action이 먼저 발생한다.

| Case | status | exit | next_action |
|---|---|---:|---|
| `--source-manifest` 없음 (policy 있음) | `invalid_input` | 2 | `provide_source_manifest` |
| `--policy` 없음 (manifest 있음) | `invalid_input` | 2 | `provide_policy` |
| 둘 다 누락 | `invalid_input` | 2 | `provide_source_manifest` (manifest 먼저 검사) |

## 재현 (Reproduction)

정본(Docker 개발 환경):

```bash
docker compose build
docker compose run --rm test          # full pytest suite
```

이 스냅샷을 만든 명령(direct, 동등):

```bash
PYTHONPATH=src python3 -m pytest -q                 # 279 passed
PYTHONPATH=src python3 -m pytest --collect-only -q  # per-module counts
```

단일 fixture smoke(위 표의 임의 행에 맞게 fixture 이름만 교체):

```bash
PYTHONPATH=src python3 -m assessment_harness.cli --output json check \
  --spec-items      fixtures/optionality_mismatch/spec_items.yaml \
  --rubric-items    fixtures/optionality_mismatch/rubric_items.yaml \
  --trace-links     fixtures/optionality_mismatch/trace_links.yaml \
  --source-manifest fixtures/optionality_mismatch/source_manifest.yaml \
  --policy          fixtures/optionality_mismatch/policy.yaml \
  --out             work/findings.json \
  --diagnostics-out work/integrity_diagnostics.json \
  --review-queue-out work/review_queue.json
```

[docs/verifications/](verifications/) 아래의 독립 검증 기록은 각 slice를 감사할 때
이 smoke 수치들을 다시 재계산한다 — 작업 로그를 그대로 신뢰하지 않는다.
