"""Public errors raised while loading AgentReplay input documents."""

from pathlib import Path


class InputFileNotFoundError(FileNotFoundError):
    """Raised when a trace or specification file does not exist."""

    def __init__(self, path: Path, document_kind: str) -> None:
        self.path = path
        self.document_kind = document_kind
        super().__init__(f"{document_kind} file not found: {path}")


class InputSyntaxError(ValueError):
    """Raised when a trace or specification cannot be decoded."""

    def __init__(self, path: Path, document_kind: str, detail: str) -> None:
        self.path = path
        self.document_kind = document_kind
        self.detail = detail
        super().__init__(f"invalid {document_kind} syntax in {path}: {detail}")


class InputSchemaValidationError(ValueError):
    """Raised when decoded input does not meet its domain contract."""

    def __init__(self, path: Path, document_kind: str, detail: str) -> None:
        self.path = path
        self.document_kind = document_kind
        self.detail = detail
        super().__init__(f"invalid {document_kind} schema in {path}: {detail}")
