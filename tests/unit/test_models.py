"""Tests for the AgentReplay domain contracts."""

import json
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from agentreplay.models import (
    ActionOrderingRule,
    AgentExecutionTrace,
    AgentTestSpecification,
    ArgumentMatchingRule,
    EvaluationReport,
    EvaluationViolation,
    ExecutionCountRule,
    RecordedToolCall,
    RequiredActionRule,
    RuleType,
    ToolCallStatus,
)

FIXTURES_DIRECTORY = Path(__file__).parents[1] / "fixtures"


def test_valid_trace_fixture_parses() -> None:
    trace_payload = json.loads(
        (FIXTURES_DIRECTORY / "traces" / "order_cancellation_trace.json").read_text()
    )

    execution_trace = AgentExecutionTrace.model_validate(trace_payload)

    assert execution_trace.run_id == "order-cancellation-2026-09-29-001"
    assert [tool_call.sequence_number for tool_call in execution_trace.tool_calls] == [1, 2, 3]
    assert execution_trace.tool_calls[1].execution_status is ToolCallStatus.SUCCEEDED


@pytest.mark.parametrize(
    ("tool_calls", "error_message"),
    [
        (
            [
                RecordedToolCall(
                    sequence_number=1,
                    tool_name="get_order",
                    arguments={},
                    execution_status=ToolCallStatus.SUCCEEDED,
                ),
                RecordedToolCall(
                    sequence_number=1,
                    tool_name="cancel_order",
                    arguments={},
                    execution_status=ToolCallStatus.SUCCEEDED,
                ),
            ],
            "contiguous",
        ),
        (
            [
                RecordedToolCall(
                    sequence_number=2,
                    tool_name="get_order",
                    arguments={},
                    execution_status=ToolCallStatus.SUCCEEDED,
                )
            ],
            "contiguous",
        ),
    ],
)
def test_trace_rejects_non_contiguous_sequence_numbers(
    tool_calls: list[RecordedToolCall], error_message: str
) -> None:
    with pytest.raises(ValidationError, match=error_message):
        AgentExecutionTrace(schema_version="1", run_id="run-123", tool_calls=tool_calls)


def test_trace_rejects_invalid_status() -> None:
    with pytest.raises(ValidationError, match="execution_status"):
        RecordedToolCall.model_validate(
            {
                "sequence_number": 1,
                "tool_name": "get_order",
                "arguments": {},
                "execution_status": "in_progress",
            }
        )


def test_trace_serialization_round_trip() -> None:
    execution_trace = AgentExecutionTrace(
        schema_version="1",
        run_id="round-trip-run",
        tool_calls=(
            RecordedToolCall(
                sequence_number=1,
                tool_name="get_order",
                arguments={"order_id": "ORD-1001", "include_items": True},
                execution_status=ToolCallStatus.SUCCEEDED,
            ),
        ),
    )

    serialized_trace = execution_trace.model_dump(mode="json")

    assert AgentExecutionTrace.model_validate(serialized_trace) == execution_trace


def test_valid_rule_specification_fixture_parses_discriminated_rules() -> None:
    specification_path = (
        FIXTURES_DIRECTORY / "specifications" / "order_cancellation_specification.yaml"
    )
    specification_payload = yaml.safe_load(specification_path.read_text())

    specification = AgentTestSpecification.model_validate(specification_payload)

    assert isinstance(specification.rules[0], RequiredActionRule)
    assert isinstance(specification.rules[2], ActionOrderingRule)
    assert isinstance(specification.rules[3], ExecutionCountRule)
    assert isinstance(specification.rules[4], ArgumentMatchingRule)


@pytest.mark.parametrize(
    "rule_payload",
    [
        {
            "id": "ambiguous-count",
            "type": "execution_count",
            "tool_name": "cancel_order",
            "exactly": 1,
            "at_least": 1,
        },
        {
            "id": "empty-count",
            "type": "execution_count",
            "tool_name": "cancel_order",
        },
        {
            "id": "single-step-order",
            "type": "action_ordering",
            "tool_names": ["cancel_order"],
        },
        {
            "id": "unknown-rule",
            "type": "timing_constraint",
            "tool_name": "cancel_order",
        },
    ],
)
def test_specification_rejects_malformed_rules(rule_payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        AgentTestSpecification.model_validate(
            {"schema_version": "1", "name": "Malformed specification", "rules": [rule_payload]}
        )


def test_specification_rejects_duplicate_rule_ids() -> None:
    rule = {"id": "cancel-once", "type": "required_action", "tool_name": "cancel_order"}

    with pytest.raises(ValidationError, match="rule ids must be unique"):
        AgentTestSpecification.model_validate(
            {"schema_version": "1", "name": "Duplicate rule ids", "rules": [rule, rule]}
        )


def test_evaluation_report_pass_state_is_derived_from_violations() -> None:
    passing_report = EvaluationReport(specification_name="Cancellation", evaluated_rule_count=5)
    failing_report = EvaluationReport(
        specification_name="Cancellation",
        evaluated_rule_count=5,
        violations=(
            EvaluationViolation(
                rule_id="cancel-once",
                rule_type=RuleType.EXECUTION_COUNT,
                summary="Expected one cancellation call but observed two.",
                expected=1,
                observed=2,
                call_indexes=(1, 2),
            ),
        ),
    )

    assert passing_report.passed is True
    assert failing_report.passed is False
