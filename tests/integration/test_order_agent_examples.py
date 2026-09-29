"""Integration tests for the fictional order-agent example traces."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentreplay.cli import app

runner = CliRunner()
EXAMPLES_DIRECTORY = Path(__file__).parents[2] / "examples" / "order-agent"
SPECIFICATION_PATH = EXAMPLES_DIRECTORY / "cancel-order.yaml"


@pytest.mark.parametrize(
    ("trace_filename", "expected_exit_code", "expected_counts", "expected_failure"),
    [
        ("success-trace.json", 0, (6, 0), None),
        ("policy-violation-trace.json", 1, (5, 1), "FAIL action_ordering"),
        ("duplicate-cancellation-trace.json", 1, (5, 1), "FAIL execution_count"),
    ],
)
def test_order_agent_examples_demonstrate_expected_behavior(
    trace_filename: str,
    expected_exit_code: int,
    expected_counts: tuple[int, int],
    expected_failure: str | None,
) -> None:
    result = runner.invoke(
        app,
        ["test", str(EXAMPLES_DIRECTORY / trace_filename), "--spec", str(SPECIFICATION_PATH)],
    )

    passed_count, failed_count = expected_counts
    assert result.exit_code == expected_exit_code
    assert f"{passed_count} passed" in result.output
    assert f"{failed_count} failed" in result.output
    if expected_failure is not None:
        assert expected_failure in result.output
