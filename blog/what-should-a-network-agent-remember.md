# What Should a Network Agent Remember? Evidence, Deterministic Evaluation, and Infrastructure Memory

When people talk about memory for AI agents, the conversation usually gets to vector databases pretty quickly. Store previous conversations, embed documentation, retrieve relevant chunks, and put them back into the prompt. That is useful, but I do not think it solves the harder problem for a network operations agent.

A network agent needs more than memory. It needs a way to separate what the network actually showed us, what we can prove from that evidence, what we already know about the infrastructure, and what the language model is inferring.

The architecture I am experimenting with now has four different jobs:

```text
Collectors -> Evidence -> JEV -> Infrahub -> Agent
                         |       |
                    validated   infrastructure
                     findings      memory
```

Collectors observe the network. JEV evaluates evidence deterministically. Infrahub provides structured infrastructure memory and relationships. The agent reasons across all of it.

I do not want the LLM doing jobs that deterministic code can do better, and I do not want a source of truth pretending that yesterday's observation is proof of what the network is doing right now.

## The Problem Is Bigger Than Agent Amnesia

Imagine an agent investigating a BGP incident. It connects to a router, collects BGP state, checks the interface, and maybe queries telemetry or another API. It sees:

```text
Ethernet1/1 operational state: DOWN
BGP peer 203.0.113.10: IDLE
```

A language model knows enough about BGP to tell you that an interface problem could explain why the session is down. But there are several different statements hiding inside that answer.

The collector **observed** that Ethernet1/1 was down. The collector **observed** that the BGP peer was Idle. A deterministic evaluator may be able to **validate** that known invariants have been violated. The infrastructure graph may tell us that the peer uses Ethernet1/1, the interface carries TRANSIT-A, and INTERNET-EGRESS depends on that circuit. The LLM can then **infer** the operational significance.

Those are not interchangeable.

## Three Levels of Truth

I have started thinking about the output in three categories:

```text
OBSERVED
A collector directly measured it.

VALIDATED
A deterministic evaluator tested the evidence against a rule or invariant.

INFERRED
The agent reasoned from evidence, validated findings, and infrastructure context.
```

Suppose the agent says the BGP session is down because Ethernet1/1 failed, affecting the INTERNET-EGRESS service. I want to be able to unpack that sentence.

```text
OBSERVED:
  Ethernet1/1 = DOWN
  BGP peer 203.0.113.10 = IDLE

VALIDATED:
  Peer is not Established.
  Interface is operationally down.
  BGP adjacency health invariant failed.

INFRASTRUCTURE MEMORY:
  203.0.113.10 -> Ethernet1/1
  Ethernet1/1 -> TRANSIT-A
  TRANSIT-A -> INTERNET-EGRESS

INFERRED:
  The interface failure is the strongest supported explanation
  for the BGP outage, and INTERNET-EGRESS is in the affected path.
```

Now I know what came from the network, what was deterministically tested, what came from the source of truth, and what came from the model.

## Where JEV Fits

JEV is not the agent's memory and it is not the source of truth. It is the deterministic evaluation layer. Its job is to take evidence and answer questions that should not require an LLM.

```text
Invariant:
BGP peer state must be Established.

Observed:
203.0.113.10 = Idle

Result:
FAIL
```

The rule I want throughout this project is simple:

> **The LLM should not re-decide something deterministic evaluation has already proven.**

The agent can question freshness, scope, or missing evidence. It can reason about dependencies and likely causes. It can identify what should happen next. But if JEV proves that an invariant was violated, the model does not get a second vote.

## Evidence Is Still Not Memory

Adding JEV does not change another distinction: raw evidence should not automatically become agent memory.

CLI output, telemetry samples, syslog, packet captures, and API responses are evidence. They may be large, noisy, and highly time-sensitive. What I want to preserve as infrastructure memory is durable structured context: sites, devices, interfaces, BGP peers, circuits, services, dependencies, intent, selected observations, changes, and validation history.

That is why Infrahub is interesting to me. Its schema is user-defined, so I can model the objects and relationships the agent actually needs instead of forcing the experiment into a fixed model.

For the first lab:

```text
IAD-01
   |
edge01.iad01
   |
Ethernet1/1
   +-------------------+
   |                   |
203.0.113.10        TRANSIT-A
 BGP Peer               |
                     INTERNET-EGRESS
```

The graph is not telling me that Ethernet1/1 is currently down. The collector tells me that. JEV validates the operational invariants. The graph tells me what Ethernet1/1 means to this network.

## The Questions Change

I am less interested in asking an agent what BGP Idle means. Any decent model can answer that from general networking knowledge.

I am more interested in what we actually observed, which observations have been deterministically validated, what the infrastructure knows about the affected objects, what depends on them, which parts of the diagnosis are proven versus inferred, what evidence is still missing, and what invariant needs to pass before we declare recovery.

Those questions force the agent to reason from evidence instead of giving me a plausible networking answer.

## Infrahub as Infrastructure Memory

Infrahub gives me the persistent structural side of the problem. The agent can query devices, interfaces, peers, circuits, services, and relationships through a graph instead of relying on whatever happens to fit into its prompt.

Many useful NetOps questions are graph questions:

```text
Ethernet1/1
     |
     +--> BGP Peer
     |
     +--> Circuit
             |
             +--> Service
```

If an interface fails, I want to know what depends on it. I am not asking a vector database to find a paragraph that happens to mention the circuit. The relationship itself is data.

Infrahub's MCP server makes this useful because the agent can discover the schema and query the infrastructure graph through a standard tool interface. The model gets infrastructure context and deterministic findings, but those systems remain independent of the model.

## Provenance Matters More Now

An observation should carry where it came from and when it was collected:

```yaml
subject: edge01.iad01:Ethernet1/1
state: down
observed_at: 2026-09-25T16:41:55Z
source: cli
collector: iosxe-interface-state
confidence: deterministic
evidence_reference: evidence://incident-8841/interface-state
```

A JEV finding should point back to the evidence it evaluated. That lets the agent explain the chain behind its conclusion rather than just attach a confidence score to a paragraph.

## Freshness Is Part of Correctness

Memory is durable. Operational state often is not. If Infrahub contains an observation from yesterday saying Ethernet1/1 was up, that is historical context, not proof that it is up now. A JEV result is only as current as the evidence it evaluated.

Before saying the network recovered, I want new evidence:

```text
Execute remediation
        |
        v
Collect fresh evidence
        |
        v
Run JEV validation
        |
        +--> FAIL -> keep investigating
        |
        +--> PASS
               |
               v
        update durable history
```

The LLM should not declare victory because a change command returned successfully. Execution success and network recovery are different things.

## The Write Path Needs the Same Discipline

The Infrahub MCP workflow gives us another useful control point. Agent writes occur on an isolated session branch and can be opened as a Proposed Change for review. They do not silently become default-branch truth.

That gives us a larger loop:

```text
Observe
   |
Evidence
   |
JEV
   |
Validated Findings
   |
Infrahub Context
   |
Agent Reasoning
   |
Proposed Change
   |
Validation
   |
Human Approval
   |
Execution
   |
Observe Again
   |
JEV
```

This is much more interesting to me than giving an LLM SSH credentials and calling it an autonomous network engineer.

Collectors establish evidence. JEV establishes deterministic findings. Infrahub establishes infrastructure context. The agent connects those facts, identifies gaps, and proposes what should happen next. Executors make approved changes. Validators prove whether those changes actually worked.

## The First Lab: BGP Failure

The companion repo starts with one scenario:

```text
Site: IAD-01
Device: edge01.iad01
Interface: Ethernet1/1
BGP Peer: 203.0.113.10 / AS64520
Circuit: TRANSIT-A
Service: INTERNET-EGRESS
```

The collector evidence is Ethernet1/1 down and peer 203.0.113.10 Idle. JEV evaluates that evidence against deterministic checks. Infrahub supplies topology and service relationships.

Then the agent has to answer what the collectors observed, what JEV deterministically established, what Infrahub knows about the affected objects, which service depends on the failed path, which parts of the diagnosis are observed/validated/inferred, what evidence is missing, what should be collected next, and what invariants must pass before the incident is considered resolved.

That is enough to test whether the architecture is doing what I want.

## Where This Goes Next

The next interesting step is not adding more chat memory. It is temporal reasoning.

I want the agent to eventually answer: What changed since this network was healthy? Which of those changes intersect the current failure domain? Which hypothesis can we prove or disprove deterministically? What is the smallest safe remediation we can propose? What evidence proves that remediation restored the intended state?

That gives me a loop that looks more like engineering:

```text
Observe
  -> Evidence
  -> Evaluate
  -> Remember
  -> Reason
  -> Validate
  -> Propose
  -> Approve
  -> Execute
  -> Observe again
```

There is still an LLM in the middle of this system. I am not trying to remove it. I am trying to make sure it is doing the part of the job where an LLM actually helps.

The goal is not an agent that sounds like a network engineer. The goal is an agent that can tell me what it observed, what was proven, what it knows about the infrastructure, what it inferred from those facts, and what evidence would prove whether it was right.

That is a much higher bar, and I think it is a much more useful one.
