"""Typed domain contracts for AgentReplay execution traces and specifications."""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    computed_field,
    field_validator,
    model_validator,
)


class DomainModel(BaseModel):
    """Base configuration shared by immutable AgentReplay domain models."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ToolCallStatus(StrEnum):
    """Terminal outcome recorded for a tool invocation."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RecordedToolCall(DomainModel):
    """One ordered tool invocation recorded during an agent run."""

    sequence_number: int = Field(ge=1)
    tool_name: str = Field(min_length=1)
    arguments: dict[str, JsonValue] = Field(default_factory=dict)
    execution_status: ToolCallStatus

    @field_validator("tool_name")
    @classmethod
    def validate_tool_name(cls, tool_name: str) -> str:
        """Reject whitespace-only tool names."""
        if not tool_name.strip():
            raise ValueError("tool_name must not be blank")
        return tool_name


class AgentExecutionTrace(DomainModel):
    """An ordered record of tool calls produced by one agent run."""

    schema_version: Literal["1"]
    run_id: str = Field(min_length=1)
    tool_calls: tuple[RecordedToolCall, ...] = ()

    @field_validator("run_id")
    @classmethod
    def validate_run_id(cls, run_id: str) -> str:
        """Reject whitespace-only run identifiers."""
        if not run_id.strip():
            raise ValueError("run_id must not be blank")
        return run_id

    @model_validator(mode="after")
    def validate_sequence_numbers(self) -> AgentExecutionTrace:
        """Require contiguous sequence numbers so trace order is unambiguous."""
        sequence_numbers = [tool_call.sequence_number for tool_call in self.tool_calls]
        expected_sequence_numbers = list(range(1, len(self.tool_calls) + 1))
        if sequence_numbers != expected_sequence_numbers:
            raise ValueError("tool call sequence_numbers must be contiguous and start at 1")
        return self


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
    """Requires at least one call to a tool."""

    type: Literal[RuleType.REQUIRED_ACTION] = RuleType.REQUIRED_ACTION


class ForbiddenActionRule(ActionRule):
    """Prohibits every call to a tool."""

    type: Literal[RuleType.FORBIDDEN_ACTION] = RuleType.FORBIDDEN_ACTION


class ActionOrderingRule(DomainModel):
    """Requires the named actions to occur in the specified order."""

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
    """Constrains the number of invocations for one tool."""

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
    """Requires a tool call with an exactly matching JSON arguments object."""

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
