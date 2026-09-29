# AgentReplay — Copilot Engineering Instructions

## Project purpose

AgentReplay is a small open-source Python developer tool for deterministic behavioral testing of AI-agent tool execution.

AI agents do more than generate text: they call tools and cause side effects.

AgentReplay evaluates recorded agent execution traces and allows developers to assert:

- which tools were called
- which tools were not called
- the order in which tools were called
- the arguments supplied to tools
- how many times tools were called
- whether behavioral regressions occurred

The core project must remain deterministic.

AgentReplay does NOT require an LLM to evaluate traces.

The initial version is intentionally small.

## Engineering philosophy

Write this project as if it were being developed and reviewed by senior software engineers.

Prioritize:

1. correctness
2. clear domain modeling
3. readability
4. explicit behavior
5. testability
6. maintainability
7. simplicity

Do not optimize for number of features.

Avoid unnecessary abstractions and architecture.

Do not introduce:

- databases
- web servers
- React
- Docker
- cloud infrastructure
- queues
- microservices
- dependency-injection frameworks
- repository patterns
- generic factory hierarchies
- plugin architectures
- LLM dependencies

unless explicitly requested later.

## Python

Target Python 3.14.

Use modern Python typing throughout.

Prefer:

- pathlib.Path
- enums where appropriate
- dataclasses or Pydantic models for domain contracts
- explicit return types
- small focused functions
- immutable models where it improves correctness

Use Pydantic v2 for external/domain data validation.

Use PyYAML for YAML specifications.

Use Typer for the CLI.

Use Rich for human-readable terminal output.

Use pytest for tests.

Use Ruff for linting and formatting.

## Naming

Use descriptive domain-specific names.

Avoid vague identifiers such as:

- data
- obj
- item
- res
- req
- ctx
- mgr
- helper
- util
- tmp
- x
- y

unless their meaning is genuinely obvious from a tiny local scope.

Prefer names such as:

- execution_trace
- recorded_tool_call
- test_specification
- evaluation_report
- evaluation_violation
- required_action_rule
- forbidden_action_rule
- action_ordering_rule
- execution_count_rule

Prefer:

    evaluate_execution_trace()

over:

    process()

Prefer:

    TraceEvaluator

over:

    Manager

Descriptive does not mean unnecessarily verbose.

## Domain terminology

Use consistent terminology:

AgentExecutionTrace
RecordedToolCall
AgentTestSpecification
EvaluationReport
EvaluationViolation
RequiredActionRule
ForbiddenActionRule
ActionOrderingRule
ExecutionCountRule
ArgumentMatchingRule

Do not invent multiple terms for the same concept.

## Architecture

Keep these concerns separated:

1. Domain models
2. Trace/specification parsing
3. Deterministic evaluation
4. Report generation
5. CLI

Evaluation rules should operate on typed domain objects rather than raw dictionaries.

The CLI should orchestrate the application but should not contain evaluation logic.

Parsing should not contain evaluation logic.

Report rendering should not determine whether rules pass or fail.

## V1 requirements

V1 must support:

- JSON execution traces
- YAML test specifications
- required tool actions
- forbidden tool actions
- tool-call ordering
- execution-count constraints
- exact argument matching
- structured evaluation results
- readable CLI output
- exit code 0 for success
- non-zero exit code for failed evaluation
- GitHub Actions usage
- automated tests

## Out of scope for V1

Do not implement:

- live LLM execution
- OpenAI integration
- Anthropic integration
- agent framework integrations
- trace recording SDKs
- dashboards
- databases
- hosted services
- semantic/LLM evaluation
- financial-services-specific functionality

Those may be considered later.

## Testing

Test behavior rather than implementation details.

Each evaluator should have:

- passing cases
- failing cases
- edge cases

Integration tests should exercise:

trace JSON
    +
specification YAML
    ↓
evaluation
    ↓
expected report

Do not mock code unnecessarily when deterministic domain objects can be constructed directly.

## Error handling

Never silently swallow exceptions.

Differentiate:

- invalid trace input
- invalid test specification
- evaluation failure
- unexpected internal failure

User-facing CLI errors should be concise and actionable.

## Documentation

Public APIs and important domain models should have useful docstrings.

Comments should explain WHY, not repeat WHAT the code already says.

Avoid excessive comments.

## Scope control

Before implementing each requested phase:

1. inspect the existing repository
2. summarize the relevant current architecture
3. describe the files you intend to create or modify
4. identify any architectural trade-offs
5. implement only the requested phase

Do not silently introduce major architectural decisions.

After each phase:

1. run the relevant tests
2. run Ruff
3. summarize what changed
4. identify remaining limitations
5. suggest a concise Git commit message

Do not automatically start the next phase.