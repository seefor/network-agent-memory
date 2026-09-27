# network-agent-memory

An experiment in giving an AI network engineer **infrastructure memory** using **Infrahub**, **MCP**, and **Pydantic AI**.

The first version deliberately keeps the architecture small:

```text
Network -> Collector -> Evidence -> Agent <-> Infrahub
                                      infrastructure
                                         memory
```

The question behind the project is simple:

> **What should a network agent actually remember?**

## Evidence is not memory

Live CLI/API/telemetry output is evidence. It tells the agent what was observed at a particular time.

Infrahub stores durable infrastructure context: devices, interfaces, peers, circuits, services, intent, and relationships.

The agent reasons across both.

## Two claim classes

- **OBSERVED** — directly present in the supplied collector evidence.
- **INFERRED** — reasoning produced by the agent from evidence plus Infrahub context.

The agent must not present an inference as something the network directly reported.

## BGP scenario

The first scenario supplies fresh evidence:

```text
Ethernet1/1 = down
203.0.113.10 = Idle
```

Infrahub provides the infrastructure relationship:

```text
203.0.113.10 -> Ethernet1/1 -> TRANSIT-A -> INTERNET-EGRESS
```

The agent should be able to explain what it observed, what the graph knows, what may be affected, what it is inferring, and what evidence is still missing.

## Run the agent

```bash
uv sync
cp .env.example .env

uv run python -m agent.main \
  --evidence scenarios/01-bgp-failure/evidence.json \
  "What is happening with BGP peer 203.0.113.10, what depends on it, and separate OBSERVED facts from INFERRED conclusions?"
```

The agent connects to Infrahub over MCP for topology and dependency context.

## Repository layout

```text
agent/       Pydantic AI reasoning layer
schemas/     Infrahub infrastructure-memory schema
objects/     lab seed-data notes
scenarios/   collector evidence and investigation questions
docs/        architecture and evidence/memory model
blog/        companion article
```

## What comes next

This repo intentionally does **not** include a deterministic evaluation engine yet.

That is the next experiment: stop asking the LLM questions that code can answer deterministically. A later version can insert that layer between evidence and reasoning without changing Infrahub's job as infrastructure memory.

For now, the goal is to make the memory problem easy to see and easy to follow.
