# AgentReplay

AgentReplay is a deterministic CLI for testing an AI agent's recorded tool execution.
It evaluates JSON traces against YAML behavioral specifications without an LLM, network
calls, or live agent execution.

It can assert required and forbidden tools, action ordering, invocation counts, and exact
argument objects.

## Local Use

AgentReplay requires Python 3.14 or later.

```bash
python -m pip install ".[dev]"
agentreplay test examples/order-agent/success-trace.json \
	--spec examples/order-agent/cancel-order.yaml
```

The command returns `0` when all rules pass, `1` for behavioral failures, and `2` for
invalid input or execution errors.

The fictional order-agent examples demonstrate a passing cancellation, a policy-ordering
regression, and a duplicate-cancellation regression.

## GitHub Actions

This repository's [CI workflow](.github/workflows/ci.yml) installs the project, runs Ruff
and pytest, and executes the passing order-agent fixture. The workflow fails if that fixture
produces a behavioral violation.

Another repository can check out AgentReplay as source and run its own trace/specification
pair. Replace `your-org/agentreplay` with the repository and revision your project trusts.

```yaml
name: Agent behavioral tests

on:
	pull_request:

jobs:
	agentreplay:
		runs-on: ubuntu-latest
		steps:
			- name: Check out application
				uses: actions/checkout@v4

			- name: Check out AgentReplay
				uses: actions/checkout@v4
				with:
					repository: your-org/agentreplay
					ref: main
					path: tools/agentreplay

			- name: Set up Python
				uses: actions/setup-python@v5
				with:
					python-version: "3.14"

			- name: Install AgentReplay
				run: python -m pip install ./tools/agentreplay

			- name: Verify recorded agent behavior
				run: >-
					agentreplay test tests/agent-traces/cancel-order.json
					--spec tests/agent-specifications/cancel-order.yaml
```
