"""JSON execution-trace parsing."""

import json
from pathlib import Path

from pydantic import ValidationError

from agentreplay.models import AgentExecutionTrace
from agentreplay.parsing.errors import (
    InputFileNotFoundError,
    InputSchemaValidationError,
    InputSyntaxError,
)


def parse_agent_execution_trace(trace_path: Path) -> AgentExecutionTrace:
    """Load a JSON execution trace and validate its typed domain contract."""
    try:
        trace_payload = json.loads(trace_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise InputFileNotFoundError(trace_path, "execution trace") from None
    except UnicodeDecodeError as error:
        raise InputSyntaxError(trace_path, "execution trace", "file must be UTF-8") from error
    except json.JSONDecodeError as error:
        detail = f"{error.msg} at line {error.lineno}, column {error.colno}"
        raise InputSyntaxError(trace_path, "execution trace", detail) from error

    try:
        return AgentExecutionTrace.model_validate(trace_payload)
    except ValidationError as error:
        raise InputSchemaValidationError(
            trace_path,
            "execution trace",
            _format_validation_errors(error),
        ) from None


def _format_validation_errors(error: ValidationError) -> str:
    """Condense Pydantic details into a concise, stable public message."""
    details = []
    for validation_error in error.errors(include_url=False):
        location = ".".join(str(part) for part in validation_error["loc"]) or "document"
        details.append(f"{location}: {validation_error['msg']}")
    return "; ".join(details)
