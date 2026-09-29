"""Tests for deterministic behavioral rule evaluators."""

import pytest
from pydantic import JsonValue

from agentreplay.evaluators.argument_matching import evaluate_argument_matching_rule
from agentreplay.evaluators.execution_count import evaluate_execution_count_rule
from agentreplay.evaluators.forbidden_action import evaluate_forbidden_action_rule
from agentreplay.evaluators.ordering import evaluate_action_ordering_rule
from agentreplay.models import (
    ActionOrderingRule,
    AgentExecutionTrace,
    ArgumentMatchingRule,
    ExecutionCountRule,
    ForbiddenActionRule,
    RecordedToolCall,
    ToolCallStatus,
)


def build_execution_trace(*tool_calls: RecordedToolCall) -> AgentExecutionTrace:
    """Build a trace with explicitly supplied, ordered calls."""
    return AgentExecutionTrace(schema_version="1", run_id="evaluation-run", tool_calls=tool_calls)


def build_tool_call(
    sequence_number: int,
    tool_name: str,
    execution_status: ToolCallStatus = ToolCallStatus.SUCCEEDED,
    arguments: dict[str, JsonValue] | None = None,
) -> RecordedToolCall:
    """Build a recorded tool call for a deterministic evaluator test."""
    return RecordedToolCall(
        sequence_number=sequence_number,
        tool_name=tool_name,
        arguments={} if arguments is None else arguments,
        execution_status=execution_status,
    )


def test_forbidden_action_passes_when_tool_was_not_invoked() -> None:
    execution_trace = build_execution_trace(build_tool_call(1, "get_order"))
    rule = ForbiddenActionRule(id="no-refund", tool_name="issue_refund")

    violation = evaluate_forbidden_action_rule(execution_trace, rule)

    assert violation is None


def test_forbidden_action_fails_for_failed_tool_invocation() -> None:
    execution_trace = build_execution_trace(
        build_tool_call(1, "issue_refund", ToolCallStatus.FAILED)
    )
    rule = ForbiddenActionRule(id="no-refund", tool_name="issue_refund")

    violation = evaluate_forbidden_action_rule(execution_trace, rule)

    assert violation is not None
    assert violation.sequence_numbers == (1,)
    assert violation.observed == {
        "call_count": 1,
        "matching_calls": [{"sequence_number": 1, "execution_status": "failed"}],
    }


def test_ordering_passes_when_repeated_actions_contain_an_ordered_subsequence() -> None:
    execution_trace = build_execution_trace(
        build_tool_call(1, "cancel_order"),
        build_tool_call(2, "get_order"),
        build_tool_call(3, "get_order"),
        build_tool_call(4, "cancel_order"),
    )
    rule = ActionOrderingRule(
        id="load-before-cancel",
        tool_names=("get_order", "cancel_order"),
    )

    violation = evaluate_action_ordering_rule(execution_trace, rule)

    assert violation is None


def test_ordering_reports_missing_predecessor() -> None:
    execution_trace = build_execution_trace(build_tool_call(1, "cancel_order"))
    rule = ActionOrderingRule(
        id="load-before-cancel",
        tool_names=("get_order", "cancel_order"),
    )

    violation = evaluate_action_ordering_rule(execution_trace, rule)

    assert violation is not None
    assert "predecessor 'get_order'" in violation.summary
    assert violation.sequence_numbers == (1,)


def test_ordering_reports_missing_dependent_action() -> None:
    execution_trace = build_execution_trace(build_tool_call(1, "get_order"))
    rule = ActionOrderingRule(
        id="load-before-cancel",
        tool_names=("get_order", "cancel_order"),
    )

    violation = evaluate_action_ordering_rule(execution_trace, rule)

    assert violation is not None
    assert "Dependent action 'cancel_order'" in violation.summary
    assert violation.sequence_numbers == (1,)


def test_ordering_fails_when_dependent_action_only_precedes_predecessor() -> None:
    execution_trace = build_execution_trace(
        build_tool_call(1, "cancel_order"),
        build_tool_call(2, "get_order"),
    )
    rule = ActionOrderingRule(
        id="load-before-cancel",
        tool_names=("get_order", "cancel_order"),
    )

    violation = evaluate_action_ordering_rule(execution_trace, rule)

    assert violation is not None
    assert violation.sequence_numbers == (1, 2)


@pytest.mark.parametrize(
    ("rule_arguments", "call_count", "should_pass"),
    [
        ({"exactly": 2}, 2, True),
        ({"exactly": 2}, 1, False),
        ({"at_least": 2}, 3, True),
        ({"at_least": 2}, 1, False),
        ({"at_most": 2}, 2, True),
        ({"at_most": 2}, 3, False),
    ],
)
def test_execution_count_supports_exact_minimum_and_maximum_constraints(
    rule_arguments: dict[str, int], call_count: int, should_pass: bool
) -> None:
    tool_calls = tuple(
        build_tool_call(sequence_number, "cancel_order")
        for sequence_number in range(1, call_count + 1)
    )
    execution_trace = build_execution_trace(*tool_calls)
    rule = ExecutionCountRule(id="cancel-count", tool_name="cancel_order", **rule_arguments)

    violation = evaluate_execution_count_rule(execution_trace, rule)

    assert (violation is None) is should_pass
    if violation is not None:
        assert violation.observed == {"actual_count": call_count}


def test_argument_matching_requires_an_exact_arguments_object() -> None:
    execution_trace = build_execution_trace(
        build_tool_call(1, "cancel_order", arguments={"order_id": "ORD-1001", "dry_run": False})
    )
    rule = ArgumentMatchingRule(
        id="expected-cancellation",
        tool_name="cancel_order",
        expected_arguments={"order_id": "ORD-1001"},
    )

    violation = evaluate_argument_matching_rule(execution_trace, rule)

    assert violation is not None
    assert "exactly the expected arguments" in violation.summary
    assert violation.sequence_numbers == (1,)


def test_argument_matching_passes_for_exact_arguments_on_any_recorded_status() -> None:
    execution_trace = build_execution_trace(
        build_tool_call(
            1,
            "cancel_order",
            ToolCallStatus.FAILED,
            {"order_id": "ORD-1001"},
        )
    )
    rule = ArgumentMatchingRule(
        id="expected-cancellation",
        tool_name="cancel_order",
        expected_arguments={"order_id": "ORD-1001"},
    )

    violation = evaluate_argument_matching_rule(execution_trace, rule)

    assert violation is None
