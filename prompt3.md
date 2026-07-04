"Complete the deterministic lineage engine and prove it works. Only then build the DAG visualizer." build deterministic foundations first, then derive representations from them.



# DFlow Design Doctrine

## Before writing code, verify that every proposed change satisfies these principles:

- Determinism: identical input and workflow produce identical output.

- Single Source of Truth: the Catalog is the only authoritative metadata store.

- Derived Representations: DAGs, visualizations, reports, and queries are regenerated from Catalog data rather than stored independently.

- Functional Boundaries: modules communicate through explicit contracts; plugins remain pure functions with no hidden side effects.

- Observability: every meaningful state transition and transformation is inspectable.

- Replaceability: any subsystem (pipeline, visualization, storage backend) can be replaced without changing the conceptual model.

- Minimal Necessary Complexity: choose the simplest implementation that preserves correctness; do not introduce abstraction without demonstrated need.

- Architectural Integrity: if implementation and architecture diverge, refactor before extending.


# Architecture Audit.

Begin by answering these questions before writing any code:

1. Does every subsystem own exactly one responsibility?
2. Does every module name accurately describe what it now does?
3. Are there any hidden couplings between modules?
4. Are there duplicate sources of truth?
5. Can any module be removed without breaking the conceptual model?
6. Does every state mutation flow through the Catalog?
7. Can the DAG always be regenerated solely from the Catalog?
8. Are any modules acting as "god objects"?
9. Does every plugin remain a pure transformation?
10. Does the implementation still reflect the original deterministic philosophy?

You are required to produce an Architecture Audit Report before changing code.

# DFLOW PHASE 2 — LINEAGE COMPLETION & DAG VISUALIZATION

## ROLE

You are continuing development of DFlow.

DFlow is a deterministic workflow runtime for engineering datasets.

The architecture is already established.

Your job is NOT to redesign it.

Your job is to complete every missing implementation required before a DAG can truthfully exist.

The DAG is a derived representation.

The lineage engine is the source of truth.

If the lineage engine is incomplete, implement it first.

Do not use placeholders.

Do not leave TODOs.

Do not stub functionality.

Every component implemented in this phase must function exactly as intended.

**Don't just implement features. Audit the architecture continuously. If a name, module boundary, or responsibility no longer matches reality, propose a refactor before adding new functionality. Prefer architectural consistency over preserving earlier decisions.**

---

# PRIMARY OBJECTIVE

Produce a fully working lineage engine whose output can be visualized as a deterministic DAG.

The visualization must be generated entirely from registry information.

No duplicate sources of truth.

No manually constructed graphs.

---

# PRE-FLIGHT CHECKLIST

Before writing any DAG code, audit the entire project.

Verify that every item below is fully implemented.

If any item is incomplete, implement it first.

---

## Bootstrap

- SQLite database auto-created
- Schema auto-applied
- Storage folders initialized
- Initialization idempotent

---

## Registry

Must support:

- create DO
- retrieve DO
- update DO
- delete DO (if intended)
- update state
- append lineage
- query lineage
- metadata persistence
- timestamp updates

No placeholder methods.

---

## Validation

Must verify:

- file exists
- supported extension
- readable file
- duplicate detection (if desired)
- invalid path rejection

---

## State Machine

Must enforce:

- allowed transitions only
- invalid transition rejection
- transition logging
- immutable archived state (if applicable)

No direct state mutation allowed outside registry/workflow.

---

## Workflow Engine

Must:

- orchestrate execution
- validate inputs
- invoke pipeline
- create child DOs
- update lineage
- update state
- emit events

No skipped lifecycle steps.

---

## Pipeline

Must:

- execute plugins
- return deterministic TransformationResponse
- never modify registry directly

---

## Plugin Runner

Must:

- dynamically load plugins
- validate plugin contract
- reject malformed responses

---

## Plugin Contract

Every plugin must return:

- success
- output_path
- metadata_updates
- warnings
- metrics

No exceptions.

---

## Event System

Must exist.

Must support:

- subscribe
- unsubscribe
- emit

Events should include:

- DO_CREATED
- STATE_CHANGED
- PIPELINE_STARTED
- PIPELINE_FINISHED
- VALIDATION_FAILED
- TRANSFORMATION_COMPLETED

---

## CLI

Must expose:

- bootstrap
- ingest
- run
- inspect
- lineage
- dag

---

## Tests

There must be executable tests proving:

- lineage correctness
- state correctness
- plugin correctness
- registry correctness

No placeholder tests.

---

# LINEAGE ENGINE

The lineage engine is the authoritative record describing how every Data Object came into existence.

Every DO must know:

- its parent(s)
- its children
- transformation responsible
- timestamp
- originating plugin
- workflow execution

Lineage must never be inferred from folders.

Lineage must never depend on filenames.

Lineage exists solely in the registry.

---

## REQUIRED LINEAGE RULES

Every transformation produces a new DO.

Input DOs are immutable historical records.

Transformation creates:

Parent DO
        │
        ▼
Transformation
        │
        ▼
Child DO

No transformation overwrites history.

---

Example:

Raw LiDAR

↓

Noise Removal

↓

Filtered LiDAR

↓

Classification

↓

Classified LiDAR

↓

Rasterization

↓

DEM

Each node is a unique DO.

Each edge represents one deterministic transformation.

---

# Refactor registry

Rename registry.py → catalog.py.
Rename every registry reference throughout the project.
Rename variables (registry, registry_entry) to (catalog, catalog_entry).
Update imports, function names, documentation, comments, tests, CLI help, RFCs, and diagrams.
Rewrite architectural descriptions so Catalog is consistently defined as the authoritative metadata subsystem.
Ensure there are no mixed terms ("registry" and "catalog") remaining unless referring to historical notes.
Verify that the refactor introduces no behavioral changes—only semantic and architectural improvements.

---

# DAG REQUIREMENTS

Only begin DAG implementation after lineage passes validation.

The DAG is NOT another database.

The DAG is NOT manually edited.

The DAG is always generated from registry lineage.

---

## Graph Rules

Each DO is exactly one node.

Each parent-child relationship is exactly one edge.

No cycles.

No duplicate edges.

No orphan nodes unless explicitly ingested.

---

## Graph Behavior

The graph must rebuild entirely from registry contents.

Running rebuild twice must produce identical results.

The graph is deterministic.

---

## Visualization Requirements

Provide a visualization capable of showing:

DO ID

State

Transformation

Parent

Children

Creation order

Current state

Transformation history

---

Nodes should support different visual styles for different lifecycle states.

Example:

INGRESS

VALIDATED

ACTIVE

CURATED

ARCHIVED

REJECTED

SCRATCH

Visualization styling should be isolated from graph logic.

---

## Graph Queries

Implement functions capable of answering:

Show ancestors

Show descendants

Show siblings

Show transformation history

Show workflow branch

Find root DO

Find leaf DOs

Detect disconnected nodes

Verify graph integrity

---

## Integrity Validation

Implement automated verification.

Checks include:

No cycles

No missing parents

No missing children

No duplicate IDs

No duplicate edges

No invalid state references

No orphan lineage references

---

# PSEUDOCODE

Registry

↓

Load all DOs

↓

Build adjacency map

↓

Validate graph

↓

Generate DAG object

↓

Expose query interface

↓

Render visualization

---

Pseudo:

load_registry()

↓

validate_lineage()

↓

build_graph()

↓

validate_graph()

↓

render()

---

# OUT OF SCOPE

Do NOT implement:

REST API

Authentication

Networking

Cloud synchronization

User accounts

Remote execution

Distributed computing

GUI redesign

Storage migration

AI integration

Those belong to future phases.

---

# SUCCESS CRITERIA

This phase is complete only when:

✓ Every registry record participates correctly in lineage.

✓ State transitions remain valid.

✓ Parent-child relationships are deterministic.

✓ Graph integrity passes automatically.

✓ DAG rebuilds entirely from registry.

✓ Visualization reflects registry exactly.

✓ Every graph query returns correct results.

✓ No placeholders remain.

# The finished implementation should represent a production-quality deterministic lineage engine whose DAG is a faithful projection of registry state rather than an independently maintained structure.

as for DAG when you DO reach that point, keep this in mind:
Level 1 — ASCII DAG (debug tool)

This is the Unix approach.

survey.csv
    │
    ▼
Import
    │
    ▼
Validated Survey
    │
    ▼
Coordinate Transform
    │
    ▼
Projected Survey

Pros:

trivial to implement
great for debugging
works over SSH
perfect for logs and tests

This should exist regardless.

Level 2 — Interactive Graph Viewer (what I think the MVP should become)

This is what I'm envisioning for DFlow.

Imagine opening:

dflow dag

and it launches something like:

+------------------------------------------------------------+
|                     DFlow Graph                            |
|                                                            |
|  ○ Raw LiDAR --------▶ ○ Filter --------▶ ○ Classified      |
|       │                                      │             |
|       │                                      ▼             |
|       └──────────────▶ ○ DSM ───────────▶ ○ Hillshade       |
|                                                            |
+------------------------------------------------------------+

Now imagine you can:

zoom
pan
click nodes
inspect metadata
inspect lineage
inspect plugin history
inspect timestamps
inspect state
highlight parents
highlight descendants

Essentially like a Git commit graph.

This is what I think the MVP should target.

Level 3 — Live Workflow Monitor (long-term vision)

This is where it gets really interesting.

Imagine you're processing 40 LiDAR tiles.

While plugins are running...

○ tile001.las      [Running]
○ tile002.las      [Queued]
○ tile003.las      [Finished]
○ tile004.las      [Failed]

The graph updates live.

New nodes appear.

Edges animate.

States change color.

You immediately know:

what is running
what failed
what depends on what

This is basically a local workflow orchestration dashboard.

But here's the thing...

I actually don't think the DAG is the end goal.

I think it's the UI for the Catalog.

Your architecture is naturally converging toward this:

Filesystem
      │
      ▼
Validation
      │
      ▼
Workflow
      │
      ▼
Catalog
      │
      ▼
Lineage
      │
      ▼
DAG
      │
      ▼
Visualization

Notice something:

The DAG doesn't own anything.

It projects what the Catalog already knows.

That's why I was so insistent on fixing lineage first.

Here's the part that excites me

I think we're accidentally building something more interesting.

Not a DAG viewer.

A Workflow Explorer.

Imagine clicking a node.

Instead of only seeing metadata...

DO: 1A73...

State:
ACTIVE

Plugin:
denoise

Created:
2026-07-04

Parent:
Raw LiDAR

Children:
DSM
DTM
Hillshade

Metadata:
...

Logs:
...

Execution Time:
43 ms

Warnings:
0

Storage Tier:
ACTIVE

Current Location:
/storage/active/...

That's not just a graph.

That's an interactive debugger for your entire data lifecycle.

My recommendation

Don't think of visual/ as a "graph drawing" module.

Think of it as a projection layer.

Eventually it could contain:

visual/

    dag.py
        builds graph

    explorer.py
        node inspection

    timeline.py
        execution timeline

    metrics.py
        pipeline statistics

    render.py
        rendering backend

    layouts.py
        graph layout algorithms

The Catalog owns truth.

The Visual subsystem owns understanding.

If I were designing DFlow from scratch today

This would be my roadmap:

ASCII DAG — immediate debugging and testing.
Interactive local viewer (likely using Python with a lightweight graph/GUI or web frontend) — zoom, pan, click, inspect.
Live workflow monitor — real-time updates as workflows execute.
Workflow Explorer — a comprehensive interface where the graph is just one way of exploring the Catalog.

