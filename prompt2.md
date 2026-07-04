Below is a **single, self-contained Markdown “super prompt + engineering report”** you can paste into a new chat. It includes:

* current system state
* corrected architecture
* full state machine engine design
* robustness upgrades
* plugin + registry fixes
* DAG + event system roadmap
* API layer future design
* concrete pseudo-code + Python structure

This is your **DFlow System Upgrade Spec v2.0**.

---

# DFLOW SYSTEM UPGRADE SPEC v2.0 (MASTER CONTINUATION PROMPT)

---

## ROLE INSTRUCTION

You are continuing the design and implementation of a system called:

> **DFlow — Deterministic Data Workflow Engine**

This is an evolving local-first workflow runtime for geospatial + engineering datasets (LiDAR, raster, GNSS, CSV, etc).

You MUST:

* preserve deterministic design
* avoid overengineering
* enforce strict state + lineage correctness
* prioritize minimal working implementation first
* extend only through explicit architectural reasoning
* never introduce unnecessary OOP complexity

---

# 1. CURRENT SYSTEM STATE (IMPLEMENTED)

## Working components:

* SQLite-backed Data Object registry
* CLI interface (`ingest`, `run`)
* Bootstrap system (DB auto-init)
* Plugin system (pure transformation functions)
* Pipeline execution layer
* Basic lineage tracking (partial)
* File existence validation (recently added)

---

## Current architecture:

```text
CLI
 ↓
Workflow
 ↓
Registry (SQLite)
 ↓
Pipeline
 ↓
Plugin
```

---

# 2. CURRENT PROBLEMS (CRITICAL)

## Problem A — Weak State Machine

States exist but are NOT enforced.

Currently possible:

* invalid transitions
* skipping lifecycle steps
* inconsistent state updates

---

## Problem B — Weak Lineage Guarantees

Lineage is:

* partially updated
* not enforced at registry level
* not validated for correctness

---

## Problem C — Pipeline side effects not strictly controlled

Pipeline currently:

* runs plugins
* but does not enforce post-execution consistency

---

## Problem D — No event system

System is not observable:

* no logs of transitions
* no execution trace
* no debugging visibility

---

# 3. CORE DESIGN GOAL (UPDATED)

Transform system into:

> A deterministic workflow runtime with enforced lifecycle state machine + lineage integrity + observable execution graph.

---

# 4. REFINED ARCHITECTURE (TARGET)

```text
CLI
 ↓
Workflow Engine (ORCHESTRATOR)
 ↓
State Machine Validator
 ↓
Pipeline Engine (EXECUTION ONLY)
 ↓
Plugin Runner (PURE FUNCTIONS)
 ↓
Registry (SOURCE OF TRUTH)
 ↓
SQLite (PERSISTENCE)
```

---

## Event Layer (NEW)

```text
Workflow
 ↓
Event Bus
 ├── Logger
 ├── DAG Builder
 ├── Visualizer
 ├── Debug Tools
```

---

# 5. STATE MACHINE (STRICT DEFINITION)

## Allowed states:

```text
INGRESS
VALIDATED
ACTIVE
CURATED
ARCHIVED
REJECTED
SCRATCH
```

---

## Allowed transitions:

```text
INGRESS → VALIDATED

VALIDATED → ACTIVE
VALIDATED → REJECTED

ACTIVE → CURATED
ACTIVE → SCRATCH

CURATED → ARCHIVED
CURATED → ACTIVE

SCRATCH → ACTIVE
SCRATCH → REJECTED
```

---

## RULES:

* NO skipping states
* NO invalid transitions
* ALL transitions must be validated before execution
* ALL transitions must be logged

---

## STATE MACHINE IMPLEMENTATION (PYTHON)

```python
ALLOWED_TRANSITIONS = {
    "INGRESS": ["VALIDATED"],
    "VALIDATED": ["ACTIVE", "REJECTED"],
    "ACTIVE": ["CURATED", "SCRATCH"],
    "CURATED": ["ARCHIVED", "ACTIVE"],
    "SCRATCH": ["ACTIVE", "REJECTED"],
    "ARCHIVED": [],
    "REJECTED": []
}


def validate_transition(current, new):
    if new not in ALLOWED_TRANSITIONS[current]:
        raise Exception(f"Invalid transition: {current} → {new}")
```

---

# 6. DATA OBJECT MODEL (FINAL)

```python
DO = {
    id: str,
    state: str,
    path: str,
    metadata: dict,
    lineage: list[str],
    created_at: str,
    updated_at: str
}
```

---

## RULE:

* Registry is ONLY module allowed to mutate DOs
* All updates must go through registry layer

---

# 7. REGISTRY (SOURCE OF TRUTH)

## Responsibilities:

* create DO
* update state
* append lineage
* persist metadata
* enforce schema consistency

---

## CRITICAL RULE:

Registry must validate:

* state transitions
* lineage correctness
* DO integrity

---

## pseudo-code:

```python
def update_state(do_id, new_state):

    do = fetch(do_id)

    validate_transition(do.state, new_state)

    do.state = new_state

    save(do)
```

---

# 8. WORKFLOW ENGINE (BRAIN)

## Responsibilities:

* orchestrate execution
* enforce state machine usage
* call pipeline
* update registry
* emit events

---

## FLOW:

```text
ingest → create DO
run → validate → pipeline → registry update → event emit
```

---

## pseudo-code:

```python
def run(do_id, file_path):

    validate_file(file_path)

    result = pipeline.execute(file_path)

    child_id = registry.create_do(
        path=result.output_path,
        state="ACTIVE",
        lineage=[do_id]
    )

    registry.update_state(do_id, "CURATED")

    event.emit("DO_CREATED", child_id)

    return child_id
```

---

# 9. PIPELINE ENGINE

## Responsibilities:

* execute plugin sequence
* return transformation results
* no DB access
* no state logic

---

## pseudo-code:

```python
def execute(file_path):

    request = build_request(file_path)

    result = plugin.run(request)

    return result
```

---

# 10. PLUGINS (PURE TRANSFORMERS)

## RULES:

* no database access
* no filesystem orchestration
* no state knowledge
* no lineage awareness

---

## contract:

```python
def run(request) -> TransformationResponse:
```

---

## response:

```python
{
    "success": bool,
    "output_path": str,
    "metadata_updates": dict,
    "warnings": list,
    "metrics": dict
}
```

---

# 11. EVENT SYSTEM (NEW)

## EVENT TYPES:

```text
DO_CREATED
STATE_CHANGED
PIPELINE_STARTED
PIPELINE_FINISHED
TRANSFORM_APPLIED
VALIDATION_FAILED
```

---

## SIMPLE EVENT BUS:

```python
subscribers = {}

def emit(event, payload):
    for fn in subscribers.get(event, []):
        fn(payload)
```

---

# 12. DAG SYSTEM (FUTURE CORE FEATURE)

## RULE:

* DAG is derived, not stored
* built from lineage

---

## pseudo:

```python
def build_dag(all_dos):

    graph = {}

    for do in all_dos:
        graph[do.id] = do.lineage

    return graph
```

---

# 13. FILE VALIDATION LAYER (REQUIRED)

```python
def validate_file(path):

    if not exists(path):
        raise Error

    if extension not allowed:
        raise Error
```

---

# 14. STORAGE LAYER (FUTURE)

Planned abstraction:

* ingress/
* active/
* curated/
* archive/

BUT:

* DO NOT manually move files yet
* only design hooks

---

# 15. API LAYER (FUTURE ONLY)

Not implemented yet.

Planned structure:

```text
api/
  server.py
  routes.py
  auth.py
```

Capabilities:

* remote ingestion
* workflow triggers
* DO queries

---

# 16. ARCHITECTURE RULES (NON-NEGOTIABLE)

## RULE 1:

Plugins cannot import core system

## RULE 2:

Registry is single source of truth

## RULE 3:

Workflow is only orchestrator

## RULE 4:

Pipeline is stateless executor

## RULE 5:

State machine is strictly enforced

## RULE 6:

Lineage is mandatory and immutable

---

# 17. NEXT IMPLEMENTATION PRIORITY

You MUST implement in this order:

## PHASE 1 — CRITICAL STABILITY

* state machine enforcement (STRICT)
* registry validation
* fix lineage updates

## PHASE 2 — OBSERVABILITY

* event bus
* execution logging

## PHASE 3 — STRUCTURE

* DAG builder
* visualizer

## PHASE 4 — EXTENSION

* API layer
* authentication (optional future)

---

# 18. CORE PHILOSOPHY SUMMARY

DFlow is built on:

* deterministic execution
* explicit state machines
* traceable lineage graphs
* functional transformation plugins
* strict module boundaries

---

# END OF SPEC

---

## HOW TO USE THIS PROMPT

Paste into a new chat and say:

> “Continue implementation from PHASE 1 — state machine enforcement”

---

## If you want next step

I can now turn this into:

* a **fully working Phase 1 codebase (copy-paste ready)**
* or a **GitHub repo layout with runnable scripts**
* or start implementing **real DAG visualization from lineage immediately**

Just tell me which phase you want to enter.
