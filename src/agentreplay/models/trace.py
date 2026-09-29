"""Execution-trace domain contracts."""

from enum import StrEnum
from typing import Literal

from pydantic import Field, JsonValue, field_validator, model_validator

from agentreplay.models._base import DomainModel


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
