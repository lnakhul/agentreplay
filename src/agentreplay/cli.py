"""Typer command-line interface for AgentReplay."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from agentreplay.evaluation_engine import EvaluationEngine
from agentreplay.parsing import (
    InputFileNotFoundError,
    InputSchemaValidationError,
    InputSyntaxError,
    parse_agent_execution_trace,
    parse_agent_test_specification,
)
from agentreplay.reporting import render_evaluation_report

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.callback()
def main() -> None:
    """Run deterministic behavioral tests for agent execution traces."""


@app.command()
def test(
    trace_file: Annotated[Path, typer.Argument(help="Path to the JSON execution trace.")],
    spec_file: Annotated[
        Path,
        typer.Option("--spec", help="Path to the YAML behavioral test specification."),
    ],
) -> None:
    """Evaluate one execution trace against one behavioral specification."""
    try:
        execution_trace = parse_agent_execution_trace(trace_file)
        test_specification = parse_agent_test_specification(spec_file)
        evaluation_report = EvaluationEngine().evaluate(execution_trace, test_specification)
        render_evaluation_report(console, execution_trace, test_specification, evaluation_report)
    except (InputFileNotFoundError, InputSchemaValidationError, InputSyntaxError) as error:
        console.print(f"[bold red]ERROR[/bold red] {error}")
        raise typer.Exit(code=2) from None
    except Exception as error:
        console.print(f"[bold red]ERROR[/bold red] unexpected execution error: {error}")
        raise typer.Exit(code=2) from None

    if not evaluation_report.passed:
        raise typer.Exit(code=1)
