"""Evaluation for exact tool-argument matching."""

from agentreplay.models import AgentExecutionTrace, ArgumentMatchingRule, EvaluationViolation


def evaluate_argument_matching_rule(
    execution_trace: AgentExecutionTrace,
    rule: ArgumentMatchingRule,
) -> EvaluationViolation | None:
    """Return a violation unless one invocation has exactly the expected arguments object."""
    matching_calls = tuple(
        tool_call
        for tool_call in execution_trace.tool_calls
        if tool_call.tool_name == rule.tool_name
    )
    if any(tool_call.arguments == rule.expected_arguments for tool_call in matching_calls):
        return None

    return EvaluationViolation(
        rule_id=rule.id,
        rule_type=rule.type,
        summary=f"No '{rule.tool_name}' invocation had exactly the expected arguments.",
        expected=rule.expected_arguments,
        observed={
            "matching_calls": [
                {"sequence_number": tool_call.sequence_number, "arguments": tool_call.arguments}
                for tool_call in matching_calls
            ]
        },
        tool_names=(rule.tool_name,),
        call_indexes=tuple(tool_call.sequence_number - 1 for tool_call in matching_calls),
        sequence_numbers=tuple(tool_call.sequence_number for tool_call in matching_calls),
    )
