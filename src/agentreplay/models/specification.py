"""Behavioral test-specification domain contracts."""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, JsonValue, field_validator, model_validator

from agentreplay.models._base import DomainModel


class RuleType(StrEnum):
    """Supported deterministic behavioral rule categories."""

    REQUIRED_ACTION = "required_action"
    FORBIDDEN_ACTION = "forbidden_action"
    ACTION_ORDERING = "action_ordering"
    EXECUTION_COUNT = "execution_count"
    ARGUMENT_MATCHING = "argument_matching"


class ActionRule(DomainModel):
    """Shared fields for rules that target one named tool action."""

    id: str = Field(min_length=1)
    tool_name: str = Field(min_length=1)

    @field_validator("id", "tool_name")
    @classmethod
    def validate_identifier(cls, value: str) -> str:
        """Reject whitespace-only rule identifiers and tool names."""
        if not value.strip():
            raise ValueError("value must not be blank")
        return value


class RequiredActionRule(ActionRule):
    """Requires at least one successful call to a tool."""

    type: Literal[RuleType.REQUIRED_ACTION] = RuleType.REQUIRED_ACTION


class ForbiddenActionRule(ActionRule):
    """Prohibits every recorded invocation of a tool, regardless of status."""

    type: Literal[RuleType.FORBIDDEN_ACTION] = RuleType.FORBIDDEN_ACTION


class ActionOrderingRule(DomainModel):
    """Requires successful named actions to occur as an ordered subsequence."""

    id: str = Field(min_length=1)
    type: Literal[RuleType.ACTION_ORDERING] = RuleType.ACTION_ORDERING
    tool_names: tuple[str, ...] = Field(min_length=2)

    @field_validator("id")
    @classmethod
    def validate_rule_id(cls, rule_id: str) -> str:
        """Reject whitespace-only rule identifiers."""
        if not rule_id.strip():
            raise ValueError("id must not be blank")
        return rule_id

    @field_validator("tool_names")
    @classmethod
    def validate_tool_names(cls, tool_names: tuple[str, ...]) -> tuple[str, ...]:
        """Reject blank action names while permitting repeated actions."""
        if any(not tool_name.strip() for tool_name in tool_names):
            raise ValueError("tool_names must not contain blank names")
        return tool_names


class ExecutionCountRule(ActionRule):
    """Constrains the number of recorded invocations for one tool, regardless of status."""

    type: Literal[RuleType.EXECUTION_COUNT] = RuleType.EXECUTION_COUNT
    exactly: int | None = Field(default=None, ge=0)
    at_least: int | None = Field(default=None, ge=0)
    at_most: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_count_constraint(self) -> ExecutionCountRule:
        """Require one coherent exact value or inclusive range."""
        if self.exactly is not None and (self.at_least is not None or self.at_most is not None):
            raise ValueError("exactly cannot be combined with at_least or at_most")
        if self.exactly is None and self.at_least is None and self.at_most is None:
            raise ValueError("one of exactly, at_least, or at_most is required")
        if self.at_least is not None and self.at_most is not None and self.at_least > self.at_most:
            raise ValueError("at_least must not exceed at_most")
        return self


class ArgumentMatchingRule(ActionRule):
    """Requires a call whose arguments object exactly equals the expected object.

    Additional recorded arguments cause the rule to fail.
    """

    type: Literal[RuleType.ARGUMENT_MATCHING] = RuleType.ARGUMENT_MATCHING
    expected_arguments: dict[str, JsonValue] = Field(default_factory=dict)


type TestRule = Annotated[
    RequiredActionRule
    | ForbiddenActionRule
    | ActionOrderingRule
    | ExecutionCountRule
    | ArgumentMatchingRule,
    Field(discriminator="type"),
]


class AgentTestSpecification(DomainModel):
    """A typed behavioral contract evaluated against an execution trace."""

    schema_version: Literal["1"]
    name: str = Field(min_length=1)
    rules: tuple[TestRule, ...] = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def validate_name(cls, name: str) -> str:
        """Reject whitespace-only specification names."""
        if not name.strip():
            raise ValueError("name must not be blank")
        return name

    @model_validator(mode="after")
    def validate_unique_rule_ids(self) -> AgentTestSpecification:
        """Ensure every violation can point to one unambiguous rule."""
        rule_ids = [rule.id for rule in self.rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("rule ids must be unique")
        return self
