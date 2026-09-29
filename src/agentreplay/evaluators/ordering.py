"""Evaluation for ordered successful tool actions."""

from agentreplay.models import (
    ActionOrderingRule,
    AgentExecutionTrace,
    EvaluationViolation,
    RecordedToolCall,
    ToolCallStatus,
)


def evaluate_action_ordering_rule(
    execution_trace: AgentExecutionTrace,
    rule: ActionOrderingRule,
) -> EvaluationViolation | None:
    """Return a violation unless successful calls contain the required ordered subsequence."""
    successful_calls = tuple(
        tool_call
        for tool_call in execution_trace.tool_calls
        if tool_call.execution_status is ToolCallStatus.SUCCEEDED
    )
    relevant_calls = tuple(
        tool_call for tool_call in successful_calls if tool_call.tool_name in rule.tool_names
    )
    matched_calls = []
    next_search_index = 0

    for required_tool_name in rule.tool_names:
        remaining_calls = successful_calls[next_search_index:]
        matching_index = next(
            (
                index
                for index, tool_call in enumerate(remaining_calls, next_search_index)
                if tool_call.tool_name == required_tool_name
            ),
            None,
        )
        if matching_index is None:
            return _ordering_violation(rule, required_tool_name, matched_calls, relevant_calls)
        matched_calls.append(successful_calls[matching_index])
        next_search_index = matching_index + 1

    return None


def _ordering_violation(
    rule: ActionOrderingRule,
    missing_tool_name: str,
    matched_calls: list[RecordedToolCall],
    relevant_calls: tuple[RecordedToolCall, ...],
) -> EvaluationViolation:
    """Describe the missing first action or later dependent action in an ordering rule."""
    if not matched_calls:
        summary = f"Required predecessor '{missing_tool_name}' was not observed successfully."
    else:
        summary = (
            f"Dependent action '{missing_tool_name}' was not observed successfully "
            "after its predecessor."
        )

    return EvaluationViolation(
        rule_id=rule.id,
        rule_type=rule.type,
        summary=summary,
        expected={"successful_order": list(rule.tool_names)},
        observed={
            "matching_successful_calls": [
                {"sequence_number": tool_call.sequence_number, "tool_name": tool_call.tool_name}
                for tool_call in relevant_calls
            ]
        },
        tool_names=rule.tool_names,
        call_indexes=tuple(tool_call.sequence_number - 1 for tool_call in relevant_calls),
        sequence_numbers=tuple(tool_call.sequence_number for tool_call in relevant_calls),
    )
