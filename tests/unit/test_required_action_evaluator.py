"""Tests for required-action evaluation."""

from agentreplay.evaluators.required_action import evaluate_required_action_rule
from agentreplay.models import (
    AgentExecutionTrace,
    RecordedToolCall,
    RequiredActionRule,
    ToolCallStatus,
)


def test_required_action_passes_for_successful_matching_call() -> None:
    execution_trace = AgentExecutionTrace(
        schema_version="1",
        run_id="successful-read",
        tool_calls=(
            RecordedToolCall(
                sequence_number=1,
                tool_name="read_order",
                arguments={},
                execution_status=ToolCallStatus.SUCCEEDED,
            ),
        ),
    )
    rule = RequiredActionRule(id="read-order", tool_name="read_order")

    violation = evaluate_required_action_rule(execution_trace, rule)

    assert violation is None


def test_required_action_rejects_failed_matching_calls() -> None:
    execution_trace = AgentExecutionTrace(
        schema_version="1",
        run_id="failed-read",
        tool_calls=(
            RecordedToolCall(
                sequence_number=1,
                tool_name="read_order",
                arguments={},
                execution_status=ToolCallStatus.FAILED,
            ),
        ),
    )
    rule = RequiredActionRule(id="read-order", tool_name="read_order")

    violation = evaluate_required_action_rule(execution_trace, rule)

    assert violation is not None
    assert violation.rule_id == "read-order"
    assert violation.tool_names == ("read_order",)
    assert violation.sequence_numbers == (1,)
    assert violation.expected == {"tool_name": "read_order", "execution_status": "succeeded"}
