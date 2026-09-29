"""Integration tests for deterministic evaluation orchestration."""

from agentreplay.evaluation_engine import EvaluationEngine
from agentreplay.models import (
    ActionOrderingRule,
    AgentExecutionTrace,
    AgentTestSpecification,
    ArgumentMatchingRule,
    ExecutionCountRule,
    ForbiddenActionRule,
    RecordedToolCall,
    RequiredActionRule,
    ToolCallStatus,
)


def test_engine_returns_a_passing_report_when_all_rules_pass() -> None:
    execution_trace = AgentExecutionTrace(
        schema_version="1",
        run_id="passing-order-cancellation",
        tool_calls=(
            RecordedToolCall(
                sequence_number=1,
                tool_name="get_order",
                arguments={"order_id": "ORD-1001"},
                execution_status=ToolCallStatus.SUCCEEDED,
            ),
            RecordedToolCall(
                sequence_number=2,
                tool_name="cancel_order",
                arguments={"order_id": "ORD-1001"},
                execution_status=ToolCallStatus.SUCCEEDED,
            ),
        ),
    )
    test_specification = AgentTestSpecification(
        schema_version="1",
        name="Passing order cancellation",
        rules=(
            RequiredActionRule(id="read-order", tool_name="get_order"),
            ForbiddenActionRule(id="no-refund", tool_name="issue_refund"),
            ActionOrderingRule(
                id="read-before-cancel",
                tool_names=("get_order", "cancel_order"),
            ),
            ExecutionCountRule(id="cancel-once", tool_name="cancel_order", exactly=1),
            ArgumentMatchingRule(
                id="expected-arguments",
                tool_name="cancel_order",
                expected_arguments={"order_id": "ORD-1001"},
            ),
        ),
    )

    report = EvaluationEngine().evaluate(execution_trace, test_specification)

    assert report.passed is True
    assert report.evaluated_rule_count == 5
    assert report.violations == ()


def test_engine_collects_every_rule_violation() -> None:
    execution_trace = AgentExecutionTrace(
        schema_version="1",
        run_id="failing-order-cancellation",
        tool_calls=(
            RecordedToolCall(
                sequence_number=1,
                tool_name="cancel_order",
                arguments={"order_id": "ORD-incorrect"},
                execution_status=ToolCallStatus.SUCCEEDED,
            ),
        ),
    )
    test_specification = AgentTestSpecification(
        schema_version="1",
        name="Failing order cancellation",
        rules=(
            RequiredActionRule(id="read-order", tool_name="get_order"),
            ForbiddenActionRule(id="no-cancel", tool_name="cancel_order"),
            ActionOrderingRule(
                id="read-before-cancel",
                tool_names=("get_order", "cancel_order"),
            ),
            ExecutionCountRule(id="cancel-twice", tool_name="cancel_order", exactly=2),
            ArgumentMatchingRule(
                id="expected-arguments",
                tool_name="cancel_order",
                expected_arguments={"order_id": "ORD-1001"},
            ),
        ),
    )

    report = EvaluationEngine().evaluate(execution_trace, test_specification)

    assert report.passed is False
    assert [violation.rule_id for violation in report.violations] == [
        "read-order",
        "no-cancel",
        "read-before-cancel",
        "cancel-twice",
        "expected-arguments",
    ]
