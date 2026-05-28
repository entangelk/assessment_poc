"""Deterministic fixture-replay runner for protocol contract tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from assessment_harness.agent_runners.base import AgentRunResult
from assessment_harness.models import read_yaml


class MockFixtureRunner:
    """Replay fixture YAML through the AgentRunner protocol.

    This runner proves the orchestration boundary is not tied to a specific SDK.
    It is not a candidate generator and should not be used for real assessment
    extraction.
    """

    name = "mock_fixture"

    def __init__(self, fixture_dir: Path, run_id: str = "mock_run_001") -> None:
        self.fixture_dir = Path(fixture_dir)
        self.run_id = run_id

    def run(
        self,
        spec_path: Path,
        rubric_path: Path,
        tools: Sequence[Any],
        max_turns: int,
        policy: Mapping[str, Any],
    ) -> AgentRunResult:
        artifacts = {
            "spec_items": read_yaml(self.fixture_dir / "spec_items.yaml"),
            "rubric_items": read_yaml(self.fixture_dir / "rubric_items.yaml"),
            "trace_links": read_yaml(self.fixture_dir / "trace_links.yaml"),
        }
        optional_files = {
            "source_manifest": self.fixture_dir / "source_manifest.yaml",
            "policy": self.fixture_dir / "policy.yaml",
        }
        for key, path in optional_files.items():
            if path.exists():
                artifacts[key] = read_yaml(path)

        audit_trace = (
            {
                "run_id": self.run_id,
                "turn": 0,
                "role": "system",
                "content_ref": "mock_fixture_replay",
            },
            {
                "run_id": self.run_id,
                "finish_reason": "complete",
                "turns": 0,
                "tool_call_count": 0,
            },
        )
        raw_trace = (
            {
                "run_id": self.run_id,
                "runner": self.name,
                "fixture_dir": str(self.fixture_dir),
                "spec_path": str(spec_path),
                "rubric_path": str(rubric_path),
                "max_turns": max_turns,
                "tool_count": len(tools),
                "policy_keys": sorted(policy.keys()),
            },
        )

        return AgentRunResult(
            run_id=self.run_id,
            runner_name=self.name,
            finish_reason="complete",
            artifacts=artifacts,
            audit_trace=audit_trace,
            raw_trace=raw_trace,
        )
