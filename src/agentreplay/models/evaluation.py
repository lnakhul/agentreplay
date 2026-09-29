"""Evaluation-result domain contracts."""

from typing import Annotated

from pydantic import Field, JsonValue, computed_field

from agentreplay.models._base import DomainModel
from agentreplay.models.specification import RuleType

type CallIndex = Annotated[int, Field(ge=0)]


class EvaluationViolation(DomainModel):
    """One actionable mismatch between a rule and a recorded trace."""

    rule_id: str = Field(min_length=1)
    rule_type: RuleType
    summary: str = Field(min_length=1)
    expected: JsonValue | None = None
    observed: JsonValue | None = None
    call_indexes: tuple[CallIndex, ...] = ()


class EvaluationReport(DomainModel):
    """The structured outcome of evaluating one test specification."""

    specification_name: str = Field(min_length=1)
    evaluated_rule_count: int = Field(ge=0)
    violations: tuple[EvaluationViolation, ...] = ()

    @computed_field
    @property
    def passed(self) -> bool:
        """Whether evaluation produced no violations."""
        return not self.violations
