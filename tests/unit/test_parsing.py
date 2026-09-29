"""Tests for typed execution-trace and test-specification parsing."""

from pathlib import Path

import pytest

from agentreplay.models import AgentExecutionTrace, AgentTestSpecification
from agentreplay.parsing import (
    InputFileNotFoundError,
    InputSchemaValidationError,
    InputSyntaxError,
    parse_agent_execution_trace,
    parse_agent_test_specification,
)

FIXTURES_DIRECTORY = Path(__file__).parents[1] / "fixtures"


def test_parses_valid_order_agent_trace_fixture() -> None:
    trace_path = FIXTURES_DIRECTORY / "traces" / "order_cancellation_trace.json"

    execution_trace = parse_agent_execution_trace(trace_path)

    assert isinstance(execution_trace, AgentExecutionTrace)
    assert execution_trace.tool_calls[1].tool_name == "cancel_order"


def test_rejects_malformed_json_trace(tmp_path: Path) -> None:
    trace_path = tmp_path / "malformed-trace.json"
    trace_path.write_text('{"schema_version": "1",', encoding="utf-8")

    with pytest.raises(InputSyntaxError, match="execution trace syntax"):
        parse_agent_execution_trace(trace_path)


def test_rejects_structurally_invalid_trace(tmp_path: Path) -> None:
    trace_path = tmp_path / "invalid-trace.json"
    trace_path.write_text('{"schema_version": "1", "tool_calls": []}', encoding="utf-8")

    with pytest.raises(InputSchemaValidationError, match="run_id"):
        parse_agent_execution_trace(trace_path)


def test_parses_valid_order_agent_specification_fixture() -> None:
    specification_path = (
        FIXTURES_DIRECTORY / "specifications" / "order_cancellation_specification.yaml"
    )

    specification = parse_agent_test_specification(specification_path)

    assert isinstance(specification, AgentTestSpecification)
    assert specification.rules[3].id == "cancel-once"


def test_rejects_malformed_yaml_specification(tmp_path: Path) -> None:
    specification_path = tmp_path / "malformed-specification.yaml"
    specification_path.write_text("rules: [unclosed", encoding="utf-8")

    with pytest.raises(InputSyntaxError, match="test specification syntax"):
        parse_agent_test_specification(specification_path)


def test_rejects_structurally_invalid_specification(tmp_path: Path) -> None:
    specification_path = tmp_path / "invalid-specification.yaml"
    specification_path.write_text(
        "schema_version: '1'\nname: Invalid specification\nrules: []\n",
        encoding="utf-8",
    )

    with pytest.raises(InputSchemaValidationError, match="rules"):
        parse_agent_test_specification(specification_path)


@pytest.mark.parametrize(
    ("parser", "path"),
    [
        (parse_agent_execution_trace, Path("missing-trace.json")),
        (parse_agent_test_specification, Path("missing-specification.yaml")),
    ],
)
def test_rejects_missing_input_file(parser: object, path: Path) -> None:
    with pytest.raises(InputFileNotFoundError, match="file not found"):
        parser(path)  # type: ignore[operator]
