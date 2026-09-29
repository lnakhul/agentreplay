"""Integration tests for the AgentReplay Typer command-line interface."""

import json
from pathlib import Path

from typer.testing import CliRunner

from agentreplay.cli import app

runner = CliRunner()
PROJECT_DIRECTORY = Path(__file__).parents[2]


def test_cli_returns_zero_and_renders_passing_example() -> None:
    trace_path = PROJECT_DIRECTORY / "examples" / "order-agent" / "success-trace.json"
    specification_path = PROJECT_DIRECTORY / "examples" / "order-agent" / "cancel-order.yaml"

    result = runner.invoke(app, ["test", str(trace_path), "--spec", str(specification_path)])

    assert result.exit_code == 0
    assert "AgentReplay" in result.output
    assert "Trace: order-agent-success" in result.output
    assert "6 passed" in result.output
    assert "0 failed" in result.output


def test_cli_returns_one_and_renders_all_behavioral_failures(tmp_path: Path) -> None:
    trace_path = tmp_path / "failing-trace.json"
    trace_path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "run_id": "order-agent-failure",
                "tool_calls": [
                    {
                        "sequence_number": 1,
                        "tool_name": "cancel_order",
                        "arguments": {"order_id": "ORD-1001"},
                        "execution_status": "succeeded",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    specification_path = tmp_path / "failing-specification.yaml"
    specification_path.write_text(
        """schema_version: "1"
name: failing-order-agent
rules:
  - id: get-order-executed
    type: required_action
    tool_name: get_order
  - id: cancel-forbidden
    type: forbidden_action
    tool_name: cancel_order
  - id: policy-before-cancellation
    type: action_ordering
    tool_names: [check_cancellation_policy, cancel_order]
  - id: no-cancellations
    type: execution_count
    tool_name: cancel_order
    at_most: 0
  - id: cancellation-arguments
    type: argument_matching
    tool_name: cancel_order
    expected_arguments:
      order_id: ORD-1001
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["test", str(trace_path), "--spec", str(specification_path)])

    assert result.exit_code == 1
    assert "1 passed" in result.output
    assert "4 failed" in result.output
    assert "FAIL required_action" in result.output
    assert "FAIL execution_count" in result.output
    assert "Expected:" in result.output
    assert "Observed:" in result.output


def test_cli_returns_two_for_invalid_input() -> None:
    specification_path = PROJECT_DIRECTORY / "examples" / "order-agent" / "cancel-order.yaml"

    result = runner.invoke(app, ["test", "missing-trace.json", "--spec", str(specification_path)])

    assert result.exit_code == 2
    assert "ERROR" in result.output
    assert "execution trace file not found" in result.output
