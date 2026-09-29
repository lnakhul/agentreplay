"""YAML test-specification parsing."""

from pathlib import Path

import yaml
from pydantic import ValidationError

from agentreplay.models import AgentTestSpecification
from agentreplay.parsing.errors import (
    InputFileNotFoundError,
    InputSchemaValidationError,
    InputSyntaxError,
)
from agentreplay.parsing.trace_parser import _format_validation_errors


def parse_agent_test_specification(specification_path: Path) -> AgentTestSpecification:
    """Load a YAML test specification and validate its typed domain contract."""
    try:
        specification_payload = yaml.safe_load(specification_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise InputFileNotFoundError(specification_path, "test specification") from None
    except UnicodeDecodeError as error:
        raise InputSyntaxError(
            specification_path,
            "test specification",
            "file must be UTF-8",
        ) from error
    except yaml.YAMLError as error:
        raise InputSyntaxError(specification_path, "test specification", str(error)) from error

    try:
        return AgentTestSpecification.model_validate(specification_payload)
    except ValidationError as error:
        raise InputSchemaValidationError(
            specification_path,
            "test specification",
            _format_validation_errors(error),
        ) from None
