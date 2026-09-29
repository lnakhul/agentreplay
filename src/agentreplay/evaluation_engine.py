"""Deterministic orchestration for behavioral-rule evaluation."""

from typing import assert_never

from agentreplay.evaluators.argument_matching import evaluate_argument_matching_rule
from agentreplay.evaluators.execution_count import evaluate_execution_count_rule
from agentreplay.evaluators.forbidden_action import evaluate_forbidden_action_rule
from agentreplay.evaluators.ordering import evaluate_action_ordering_rule
from agentreplay.evaluators.required_action import evaluate_required_action_rule
from agentreplay.models import (
    ActionOrderingRule,
    AgentExecutionTrace,
    AgentTestSpecification,
    ArgumentMatchingRule,
    EvaluationReport,
    EvaluationViolation,
    ExecutionCountRule,
    ForbiddenActionRule,
    RequiredActionRule,
    TestRule,
)


class EvaluationEngine:
    """Evaluate every configured deterministic rule against one execution trace."""

    def evaluate(
        self,
        execution_trace: AgentExecutionTrace,
        test_specification: AgentTestSpecification,
    ) -> EvaluationReport:
        """Return a report containing every rule violation in specification order."""
        violations = tuple(
            violation
            for rule in test_specification.rules
            if (violation := self._evaluate_rule(execution_trace, rule)) is not None
        )
        return EvaluationReport(
            specification_name=test_specification.name,
            evaluated_rule_count=len(test_specification.rules),
            violations=violations,
        )

    @staticmethod
    def _evaluate_rule(
        execution_trace: AgentExecutionTrace,
        rule: TestRule,
    ) -> EvaluationViolation | None:
        """Dispatch one typed rule to its deterministic evaluator."""
        match rule:
            case RequiredActionRule():
                return evaluate_required_action_rule(execution_trace, rule)
            case ForbiddenActionRule():
                return evaluate_forbidden_action_rule(execution_trace, rule)
            case ActionOrderingRule():
                return evaluate_action_ordering_rule(execution_trace, rule)
            case ExecutionCountRule():
                return evaluate_execution_count_rule(execution_trace, rule)
            case ArgumentMatchingRule():
                return evaluate_argument_matching_rule(execution_trace, rule)
            case _:
                assert_never(rule)
