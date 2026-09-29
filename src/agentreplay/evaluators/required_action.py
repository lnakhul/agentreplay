"""Evaluation for required tool actions."""

from agentreplay.models import (
    AgentExecutionTrace,
    EvaluationViolation,
    RequiredActionRule,
    ToolCallStatus,
)


def evaluate_required_action_rule(
    execution_trace: AgentExecutionTrace,
    rule: RequiredActionRule,
) -> EvaluationViolation | None:
    """Return a violation unless the required tool completed successfully."""
    matching_calls = tuple(
        tool_call
        for tool_call in execution_trace.tool_calls
        if tool_call.tool_name == rule.tool_name
    )
    if any(tool_call.execution_status is ToolCallStatus.SUCCEEDED for tool_call in matching_calls):
        return None

    return EvaluationViolation(
        rule_id=rule.id,
        rule_type=rule.type,
        summary=f"Required tool '{rule.tool_name}' did not complete successfully.",
        expected={"tool_name": rule.tool_name, "execution_status": ToolCallStatus.SUCCEEDED.value},
        observed={
            "matching_calls": [
                {
                    "sequence_number": tool_call.sequence_number,
                    "execution_status": tool_call.execution_status.value,
                }
                for tool_call in matching_calls
            ]
        },
        tool_names=(rule.tool_name,),
        call_indexes=tuple(tool_call.sequence_number - 1 for tool_call in matching_calls),
        sequence_numbers=tuple(tool_call.sequence_number for tool_call in matching_calls),
    )
