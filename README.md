# network-agent-memory

Evidence-grounded agentic NetOps using **JEV**, **Infrahub**, **MCP**, and **Pydantic AI**.

```text
Collectors -> Evidence -> JEV -> Validated Findings
                         |
                         +----> Agent <----> Infrahub
```

## Three claim classes
- **OBSERVED** — directly measured by a collector.
- **VALIDATED** — deterministically evaluated by JEV.
- **INFERRED** — reasoned by the agent from evidence, JEV findings, and infrastructure context.

**Rule:** the LLM should not re-decide something deterministic evaluation has already proven.

## Run JEV
```bash
uv sync --extra dev
uv run python -m jev.cli scenarios/01-bgp-failure/evidence.json
uv run pytest
```

## Run the agent
```bash
cp .env.example .env
uv run python -m agent.main --evidence scenarios/01-bgp-failure/evidence.json   "Why is BGP peer 203.0.113.10 down, what service is affected, and separate OBSERVED, VALIDATED, and INFERRED claims?"
```

The agent connects to Infrahub via MCP for topology and dependency context.

## BGP scenario
```text
203.0.113.10 -> Ethernet1/1 -> TRANSIT-A -> INTERNET-EGRESS
```

## Recovery rule
`executor success != network recovery`

Recovery requires **fresh evidence -> JEV validation -> PASS**.

## Infrahub safety boundary
Infrahub MCP writes are session-branch isolated and can be submitted as Proposed Changes for human review. The MCP server does not expose branch merge as an agent operation.

## Repo layout
```text
agent/       Pydantic AI + Infrahub MCP reasoning
jev/         deterministic evaluator
schemas/     Infrahub schema
objects/     lab seed-data notes
scenarios/   evidence, questions, JEV output
docs/        architecture and truth model
blog/        companion article
tests/       JEV unit tests
```

`jev/` is a small local deterministic evaluator so the lab is runnable. It is intentionally replaceable with a larger JEV implementation later.
