"""Evaluation for forbidden tool actions."""

from agentreplay.models import AgentExecutionTrace, EvaluationViolation, ForbiddenActionRule


def evaluate_forbidden_action_rule(
    execution_trace: AgentExecutionTrace,
    rule: ForbiddenActionRule,
) -> EvaluationViolation | None:
    """Return a violation when the forbidden tool was invoked at any status."""
    matching_calls = tuple(
        tool_call
        for tool_call in execution_trace.tool_calls
        if tool_call.tool_name == rule.tool_name
    )
    if not matching_calls:
        return None

    return EvaluationViolation(
        rule_id=rule.id,
        rule_type=rule.type,
        summary=f"Forbidden tool '{rule.tool_name}' was invoked.",
        expected={"tool_name": rule.tool_name, "call_count": 0},
        observed={
            "call_count": len(matching_calls),
            "matching_calls": [
                {
                    "sequence_number": tool_call.sequence_number,
                    "execution_status": tool_call.execution_status.value,
                }
                for tool_call in matching_calls
            ],
        },
        tool_names=(rule.tool_name,),
        call_indexes=tuple(tool_call.sequence_number - 1 for tool_call in matching_calls),
        sequence_numbers=tuple(tool_call.sequence_number for tool_call in matching_calls),
    )
