# What Should a Network Agent Actually Remember? Building Infrastructure Memory with Infrahub

When people talk about memory for AI agents, the conversation usually gets to vector databases pretty quickly. Store previous conversations, embed documentation, retrieve relevant chunks, and put them back into the prompt.

That is useful, but I do not think it solves the harder memory problem for a network operations agent.

If I ask an agent to troubleshoot a BGP problem today, it can collect evidence, reason through the problem, and give me a useful answer. Then the next investigation starts and we are back to rebuilding context. What device is this? Where is it? What interface does this peer use? Which circuit is attached to that interface? What service depends on the circuit?

A network agent should not have to rediscover the structure of the network every time it starts reasoning.

That is the problem I want to explore with Infrahub.

## Start With a Smaller Architecture

I originally started adding more layers to this experiment: deterministic evaluators, validation objects, additional truth states. All of those ideas have value, but they also hide the first question I actually want to answer.

**What should a network agent remember?**

So I am starting with a much smaller architecture:

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
                                       |
                                       v
                              Infrastructure Memory
```

The collector tells the agent what the network is doing now.

Infrahub tells the agent what the infrastructure is.

The agent reasons across both.

That separation is the experiment.

## Evidence Is Not Memory

This is the distinction I think matters most.

Suppose I collect this from a router:

```text
Ethernet1/1 operational state: DOWN
BGP peer 203.0.113.10: IDLE
```

Those are observations. They are evidence from a particular point in time.

I do not need to turn every line of `show ip bgp summary`, every interface counter, every syslog message, or every telemetry sample into permanent agent memory. Most of that information is useful because of when it was collected.

What I want the agent to remember is the durable context around that evidence.

For example:

```text
203.0.113.10
     |
     v
Ethernet1/1
     |
     v
TRANSIT-A
     |
     v
INTERNET-EGRESS
```

Now the live evidence means something.

The agent does not just know that a BGP peer is Idle. It can discover which interface the peer is attached to, which circuit uses that interface, and which service depends on that circuit.

That is the kind of memory I am interested in.

## Why a Graph Makes Sense

A lot of agent-memory examples start with semantic search. That makes sense for unstructured information such as runbooks, vendor documentation, incident notes, and postmortems.

Infrastructure is different.

The relationships themselves matter.

A device belongs to a site. An interface belongs to a device. A BGP peer terminates on an interface. A circuit uses an interface. A service depends on a circuit.

Those are not paragraphs I want an embedding model to rediscover. They are relationships I want represented directly.

For the first lab, the graph is intentionally small:

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

That is enough to start asking much better questions.

## The Questions I Want the Agent to Answer

I am not particularly interested in asking the agent, "What does BGP Idle mean?"

A modern language model already knows enough general networking information to answer that.

I want to ask questions that require knowledge of **this network**.

What do we know about peer `203.0.113.10`?

Which interface is it associated with?

What circuit uses that interface?

What service depends on that circuit?

Given the live evidence, what might be affected?

What part of that answer came directly from the network, and what part did the agent infer?

What evidence is still missing before we take action?

Those questions require more than general networking knowledge. They require infrastructure context.

## OBSERVED Versus INFERRED

For this first version, I am keeping the reasoning model deliberately simple.

There are two categories I care about.

```text
OBSERVED
A collector directly measured it.

INFERRED
The agent reasoned from evidence and infrastructure context.
```

If the collector says:

```text
Ethernet1/1 = DOWN
BGP peer 203.0.113.10 = IDLE
```

those are OBSERVED facts.

If Infrahub tells us:

```text
203.0.113.10 -> Ethernet1/1
Ethernet1/1 -> TRANSIT-A
TRANSIT-A -> INTERNET-EGRESS
```

that is infrastructure context.

The agent may then conclude:

```text
The failed interface is a plausible explanation for the BGP outage,
and INTERNET-EGRESS is in the affected dependency path.
```

That is INFERRED.

The distinction matters because I do not want a model turning a reasonable conclusion into something that sounds like the network directly reported it.

## Why Infrahub

Infrahub is interesting here because I can define the infrastructure model I want rather than adapting the experiment to a fixed schema.

For this lab I only need a handful of objects:

```text
Site
Device
Interface
BGP Peer
Circuit
Service
Observation
```

And a handful of relationships:

```text
Device -> Site
Interface -> Device
BGP Peer -> Interface
Circuit -> Interface
Service -> Circuit
```

That is enough to start building infrastructure memory without trying to model the entire network on day one.

The other piece I care about is MCP. Instead of writing a pile of custom functions just so the agent can interrogate the graph, the Infrahub MCP server gives the agent a standard tool interface for discovering and querying that infrastructure context.

That keeps the agent side surprisingly small.

## Freshness Still Matters

There is an important trap when we start calling something "memory."

Memory is durable. Operational state often is not.

If an observation stored yesterday says Ethernet1/1 was up, that is useful history. It is not proof that Ethernet1/1 is up right now.

For current operational questions, the agent should prefer fresh collector evidence.

That gives us another useful boundary:

```text
Infrahub
  |
  +--> What exists?
  +--> How is it related?
  +--> What is the intended structure?
  +--> What historical context do we have?

Collector
  |
  +--> What did the network show us now?
```

The agent combines the two, but it should not confuse them.

## The First BGP Lab

The repository starts with one simple failure.

The infrastructure model says:

```text
Site: IAD-01
Device: edge01.iad01
Interface: Ethernet1/1
BGP Peer: 203.0.113.10
Remote ASN: 64520
Circuit: TRANSIT-A
Service: INTERNET-EGRESS
```

The collector evidence says:

```text
Ethernet1/1 = DOWN
203.0.113.10 = IDLE
```

The agent gets the evidence directly and queries Infrahub for the rest.

Then I want it to answer:

1. What did the collector actually observe?
2. What does Infrahub know about this peer?
3. Which interface is involved?
4. What circuit and service depend on that path?
5. Which statements are observed facts?
6. Which statements are agent inference?
7. What evidence is missing?
8. What should we collect next before taking action?

This is deliberately not an autonomous remediation demo.

I want to get the evidence and memory boundary right before adding execution.

## What I Am Not Putting in Infrahub

I also do not want Infrahub to become a dumping ground for everything the agent ever sees.

I would not put every raw CLI response into the graph. I would not dump high-volume telemetry into it. I would not store the model's chain of thought. I would not treat every temporary observation as durable truth.

Different information has different jobs.

Raw operational evidence can live with the collection or telemetry system. Runbooks and vendor documentation may eventually make more sense in a retrieval system. Working conversation state belongs in the agent runtime.

Infrahub's job in this architecture is narrower and more useful: **structured infrastructure memory**.

## Where Deterministic Evaluation Comes In Later

There is another problem waiting right behind this one.

Some questions should not be answered by an LLM at all.

If a BGP peer must be Established and the collected state is Idle, code can evaluate that condition deterministically. If six BGP flaps per minute violates an operational invariant of two flaps per five minutes, I do not need a language model to decide whether the threshold was exceeded.

That deserves its own layer and, more importantly, its own experiment.

I do not want to hide the infrastructure-memory lesson underneath it.

So the progression I am working toward looks more like this:

```text
1. Infrastructure Memory
        |
        v
2. Deterministic Evaluation
        |
        v
3. Temporal Reasoning
        |
        v
4. Safe Execution
```

First give the agent memory.

Then stop asking the LLM questions code can answer.

Then use history to reason about what changed.

Then worry about letting the agent propose or execute changes.

Each step solves a different problem.

## Where This Goes Next

The interesting end state is still larger than memory.

Eventually I want an agent that can collect current evidence, understand the infrastructure around the failure, compare current state with previous known-good state, determine which conclusions can be proven deterministically, propose the smallest reasonable change, and then collect new evidence to verify the result.

But I do not think we need to build all of that at once to learn something useful.

The first question is enough:

> **What should a network agent actually remember?**

My answer right now is not "everything."

It should remember the durable structure and context that makes fresh evidence meaningful.

That is what I want to test with Infrahub.
