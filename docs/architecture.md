# Architecture

The first version keeps the system intentionally small:

```text
Network
   |
   v
Collector
   |
   v
Evidence ------+
               |
               v
             Agent <------MCP------> Infrahub
               |                     Infrastructure
               |                        Memory
               v
            Answer
```

## Responsibilities

**Collector** observes the network and produces time-stamped evidence.

**Infrahub** stores durable infrastructure context and relationships.

**Agent** combines current evidence with infrastructure context and explains what is observed versus what it inferred.

## Boundary

Evidence and memory are not the same thing.

A historical observation in memory is context. It is not proof of current network state. Current-state claims should be grounded in fresh collector evidence.
