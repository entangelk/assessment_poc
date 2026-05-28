"""Contract tests for framework-neutral agent runners."""

from __future__ import annotations

from pathlib import Path

from assessment_harness.agent_runners import AgentRunner, MockFixtureRunner
from assessment_harness.schemas import validate


def test_mock_fixture_runner_satisfies_agent_runner_protocol(
    fixture_dir: Path,
) -> None:
    runner = MockFixtureRunner(fixture_dir / "clean_assignment")

    assert isinstance(runner, AgentRunner)


def test_mock_fixture_runner_replays_fixture_artifacts(fixture_dir: Path) -> None:
    runner = MockFixtureRunner(fixture_dir / "clean_assignment", run_id="mock_run")
    result = runner.run(
        spec_path=fixture_dir / "clean_assignment" / "source" / "spec.md",
        rubric_path=fixture_dir / "clean_assignment" / "source" / "rubric.md",
        tools=[],
        max_turns=1,
        policy={"rules": {}},
    )

    assert result.run_id == "mock_run"
    assert result.runner_name == "mock_fixture"
    assert result.finish_reason == "complete"
    assert validate("spec_items", result.artifacts["spec_items"]) == []
    assert validate("rubric_items", result.artifacts["rubric_items"]) == []
    assert validate("trace_links", result.artifacts["trace_links"]) == []
    assert len(result.audit_trace) > 0
    assert all(validate("agent_trace", event) == [] for event in result.audit_trace)
    assert result.audit_trace[-1]["finish_reason"] == "complete"
    assert result.raw_trace[0]["fixture_dir"].endswith("clean_assignment")


def test_agent_trace_schema_rejects_unattributed_event() -> None:
    assert validate("agent_trace", {"finish_reason": "complete"}) != []


def test_agent_trace_schema_requires_role_payload() -> None:
    bare_role_events = [
        {"run_id": "run_1", "turn": 0, "role": "system"},
        {"run_id": "run_1", "turn": 1, "role": "agent"},
        {"run_id": "run_1", "turn": 1, "role": "tool"},
    ]

    for event in bare_role_events:
        assert validate("agent_trace", event) != []
