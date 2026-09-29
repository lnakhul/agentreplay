"""Human-readable rendering for deterministic evaluation reports."""

import json

from rich.console import Console

from agentreplay.models import (
    ActionOrderingRule,
    AgentExecutionTrace,
    AgentTestSpecification,
    ArgumentMatchingRule,
    EvaluationReport,
    ExecutionCountRule,
    ForbiddenActionRule,
    RequiredActionRule,
    TestRule,
)


def render_evaluation_report(
    console: Console,
    execution_trace: AgentExecutionTrace,
    test_specification: AgentTestSpecification,
    evaluation_report: EvaluationReport,
) -> None:
    """Render concise pass/fail results suitable for terminals and CI logs."""
    violations_by_rule_id = {
        violation.rule_id: violation for violation in evaluation_report.violations
    }
    passed_count = evaluation_report.evaluated_rule_count - len(evaluation_report.violations)

    console.print("[bold]AgentReplay[/bold]")
    console.print()
    console.print(f"Trace: {execution_trace.run_id}")
    console.print(f"Specification: {test_specification.name}")
    console.print()

    for rule in test_specification.rules:
        if rule.id not in violations_by_rule_id:
            console.print(f"[green]PASS[/green] {_describe_rule(rule)}")

    console.print()
    console.print(f"{passed_count} passed")
    console.print(f"{len(evaluation_report.violations)} failed")

    for violation in evaluation_report.violations:
        console.print()
        console.print(f"[bold red]FAIL[/bold red] {violation.rule_type.value}")
        console.print(violation.summary)
        console.print(f"Expected: {_format_value(violation.expected)}")
        console.print(f"Observed: {_format_value(violation.observed)}")
        if violation.sequence_numbers:
            sequence_numbers = ", ".join(str(number) for number in violation.sequence_numbers)
            console.print(f"Sequences: {sequence_numbers}")


def _describe_rule(rule: TestRule) -> str:
    """Return a concise success label for a configured rule."""
    match rule:
        case RequiredActionRule():
            return f"{rule.tool_name} executed successfully"
        case ForbiddenActionRule():
            return f"{rule.tool_name} was not executed"
        case ActionOrderingRule():
            return f"{' before '.join(rule.tool_names)} occurred in order"
        case ExecutionCountRule():
            return _describe_execution_count_rule(rule)
        case ArgumentMatchingRule():
            return f"{rule.tool_name} arguments matched exactly"


def _describe_execution_count_rule(rule: ExecutionCountRule) -> str:
    """Render a count rule's already-valid constraint in human terms."""
    if rule.exactly is not None:
        return f"{rule.tool_name} executed exactly {rule.exactly} time(s)"
    if rule.at_least is not None and rule.at_most is not None:
        return f"{rule.tool_name} executed between {rule.at_least} and {rule.at_most} time(s)"
    if rule.at_least is not None:
        return f"{rule.tool_name} executed at least {rule.at_least} time(s)"
    return f"{rule.tool_name} executed at most {rule.at_most} time(s)"


def _format_value(value: object) -> str:
    """Serialize structured expectation data into a compact deterministic string."""
    return json.dumps(value, ensure_ascii=True, sort_keys=True)
