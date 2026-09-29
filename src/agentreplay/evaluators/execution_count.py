"""Evaluation for tool invocation counts."""

from agentreplay.models import AgentExecutionTrace, EvaluationViolation, ExecutionCountRule


def evaluate_execution_count_rule(
    execution_trace: AgentExecutionTrace,
    rule: ExecutionCountRule,
) -> EvaluationViolation | None:
    """Return a violation when all recorded invocations violate the configured count bounds."""
    matching_calls = tuple(
        tool_call
        for tool_call in execution_trace.tool_calls
        if tool_call.tool_name == rule.tool_name
    )
    actual_count = len(matching_calls)
    expected_count = _expected_count(rule)

    if _count_matches(actual_count, rule):
        return None

    return EvaluationViolation(
        rule_id=rule.id,
        rule_type=rule.type,
        summary=(
            f"Tool '{rule.tool_name}' was invoked {actual_count} time(s), "
            f"which does not satisfy the configured count constraint."
        ),
        expected=expected_count,
        observed={"actual_count": actual_count},
        tool_names=(rule.tool_name,),
        call_indexes=tuple(tool_call.sequence_number - 1 for tool_call in matching_calls),
        sequence_numbers=tuple(tool_call.sequence_number for tool_call in matching_calls),
    )


def _count_matches(actual_count: int, rule: ExecutionCountRule) -> bool:
    """Determine whether an invocation count satisfies an already-valid rule."""
    if rule.exactly is not None:
        return actual_count == rule.exactly
    if rule.at_least is not None and actual_count < rule.at_least:
        return False
    return rule.at_most is None or actual_count <= rule.at_most


def _expected_count(rule: ExecutionCountRule) -> dict[str, int]:
    """Render the validated count constraint as structured expectation data."""
    if rule.exactly is not None:
        return {"exactly": rule.exactly}

    expected_count = {}
    if rule.at_least is not None:
        expected_count["at_least"] = rule.at_least
    if rule.at_most is not None:
        expected_count["at_most"] = rule.at_most
    return expected_count
