# Evidence and reasoning model

## OBSERVED

A fact directly present in collector evidence.

Example:

```text
Ethernet1/1 = down
BGP peer 203.0.113.10 = Idle
```

## INFRASTRUCTURE MEMORY

Durable context retrieved from Infrahub.

Example:

```text
203.0.113.10 -> Ethernet1/1 -> TRANSIT-A -> INTERNET-EGRESS
```

## INFERRED

A conclusion produced by the agent from current evidence and infrastructure memory.

Example:

```text
The interface failure is a plausible explanation for the BGP outage,
and INTERNET-EGRESS is in the affected dependency path.
```

The agent should keep these categories separate so a reader can see what came from the network, what came from infrastructure memory, and what came from model reasoning.
