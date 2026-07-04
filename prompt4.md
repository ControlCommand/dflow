# DFLOW PHASE 4 — CATALOG QUERY + LIFECYCLE CONTROL + CORE ENGINE HARDENING

## ROLE

You are continuing development of DFlow, a deterministic local-first workflow engine for geospatial and engineering datasets.

This system is NOT an app.

It is NOT a GUI project.

It is a deterministic data lifecycle engine with queryable lineage and reproducible transformations.

You MUST prioritize:

- correctness over features
- determinism over flexibility
- safety over convenience
- explicit state over implicit behavior
- queryability over UI

Do NOT introduce unnecessary frameworks.
Do NOT introduce distributed systems.
Do NOT introduce REST/API layers yet.

---

# 1. CURRENT SYSTEM STATE

Already implemented:

- SQLite Catalog (formerly registry)
- Data Object lifecycle (partial)
- Lineage tracking
- Plugin-based pipeline execution
- DAG generation (basic)
- CLI interface
- Validation layer
- Event bus (basic)

---

# 2. CORE PROBLEM OF CURRENT PHASE

The system currently lacks:

## ❌ Query Layer
No structured filtering or search of Data Objects.

## ❌ Lifecycle Control API
State transitions are not encapsulated in a safe transactional layer.

## ❌ Soft deletion / archival semantics
No safe removal model exists.

## ❌ Catalog abstraction consistency
Some legacy "registry" terminology may remain.

## ❌ System-level safety hardening
No constraints against unsafe or inconsistent operations.

---

# 3. NEW ARCHITECTURAL GOAL

Evolve system into:

> A deterministic catalog-driven workflow engine with safe lifecycle transitions and queryable lineage graph.

---

# 4. CORE ARCHITECTURE (UPDATED)

```
CLI
 ↓
Catalog API (SOURCE OF TRUTH)
 ↓
Lifecycle Engine (STATE + TRANSITIONS)
 ↓
Query Engine (FILTER + SEARCH)
 ↓
Workflow Engine (ORCHESTRATION)
 ↓
Pipeline Engine (EXECUTION ONLY)
 ↓
Plugin Layer (PURE TRANSFORMS)
 ↓
SQLite (PERSISTENCE)
```

---

# 5. CATALOG QUERY LAYER (NEW CORE MODULE)

## FILE: core/catalog_query.py

### REQUIRED CAPABILITIES

Implement deterministic query functions:

```python
def filter_by_state(state: str): pass

def filter_by_path(substring: str): pass

def filter_by_time_range(start, end): pass

def search_metadata(key, value): pass

def get_ancestors(do_id): pass

def get_descendants(do_id): pass

def get_siblings(do_id): pass

def full_text_search(query): pass
```

---

## EXAMPLE IMPLEMENTATION (SAFE SQL PATTERNS)

```python
def filter_by_state(state):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM catalog
        WHERE state = ?
    """, (state,))

    return cur.fetchall()
```

### SAFETY RULES:

- NEVER use string concatenation in SQL queries
- ALWAYS use parameterized queries
- NEVER execute raw user input as SQL
- ALWAYS sanitize CLI inputs before passing to query engine

---

# 6. LIFECYCLE CONTROL ENGINE (CRITICAL)

## FILE: core/lifecycle.py

### PURPOSE:

All state changes MUST go through this module.

---

## STATE TRANSITION RULES

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
```

---

## SAFE TRANSITION FUNCTION

```python
def transition(catalog, do_id, new_state, reason=None):

    record = catalog.get(do_id)

    if new_state not in ALLOWED_TRANSITIONS[record.state]:
        raise Exception(f"Invalid transition {record.state} → {new_state}")

    catalog.update_state(do_id, new_state)

    catalog.log_transition(
        do_id=do_id,
        from_state=record.state,
        to_state=new_state,
        reason=reason
    )
```

---

## RULES:

- NO direct state mutation outside lifecycle engine
- EVERY transition must be logged
- OPTIONAL reason field must be supported

---

# 7. SOFT DELETE + ARCHIVAL MODEL

## DO NOT physically delete data by default

### Add states:

- ARCHIVED → retained but inactive
- REJECTED → invalidated but preserved
- SCRATCH → temporary workspace

---

## DELETE BEHAVIOR

```python
def delete(do_id):
    transition(do_id, "REJECTED", reason="user delete")
```

OR:

```python
def archive(do_id):
    transition(do_id, "ARCHIVED", reason="long-term storage")
```

---

# 8. CATALOG CORE ENGINE (UPDATED ABSTRACTION)

Rename:

- registry.py → catalog.py

---

## RESPONSIBILITIES:

- DO creation
- DO retrieval
- metadata storage
- lineage updates
- state updates (via lifecycle only)
- integrity enforcement

---

## STRICT RULE:

Catalog MUST NOT:

- execute pipelines
- load plugins
- perform transformations

---

# 9. SQL IMPROVEMENTS

## REQUIRED INDEXES:

```sql
CREATE INDEX idx_state ON catalog(state);
CREATE INDEX idx_path ON catalog(path);
CREATE INDEX idx_created ON catalog(created_at);
```

---

## OPTIONAL FUTURE EXTENSIONS:

- JSON metadata indexing
- full-text search (FTS5 SQLite module)

---

# 10. CLI EXPANSION (NEW COMMANDS)

Add:

```bash
dflow query --state ACTIVE
dflow query --path survey
dflow query --meta key=value

dflow archive <id>
dflow delete <id>

dflow ancestors <id>
dflow descendants <id>
dflow siblings <id>

dflow inspect <id>
```

---

# 11. CORE BACKEND ENGINE HARDENING

## PIPELINE MUST BE STRICTLY ISOLATED

```python
def execute_pipeline(input_path):
    request = build_request(input_path)

    result = plugin.run(request)

    validate_plugin_response(result)

    return result
```

---

## PLUGIN SAFETY CONTRACT

Plugins MUST:

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

## SAFETY RULES:

- Plugins MUST NOT access catalog
- Plugins MUST NOT access filesystem beyond input/output contract
- Plugins MUST NOT mutate global state
- Plugins MUST be deterministic

---

# 12. SYSTEM SAFETY CONSTRAINTS

To reduce bugs and unsafe behavior:

## REQUIRED RULES:

- No dynamic SQL generation from user input
- No eval(), exec(), or runtime code injection
- No hidden side effects in plugins
- No direct file system mutation outside pipeline layer
- No silent failures — all errors must propagate

---

# 13. OBSERVABILITY IMPROVEMENTS

Every action MUST emit events:

- DO_CREATED
- STATE_CHANGED
- PIPELINE_STARTED
- PIPELINE_FINISHED
- TRANSFORMATION_FAILED

---

# 14. DAG RELATIONSHIP RULE

DAG is ALWAYS derived:

```text
CATALOG → LINEAGE → DAG
```

NOT:

```text
DAG → STORAGE
```

---

## DAG RULES:

- No manual graph editing
- No external graph storage
- Always rebuild from catalog

---

# 15. INTEGRITY CHECKS (MANDATORY)

Implement:

```python
def validate_catalog_integrity():
    check_missing_parents()
    check_orphans()
    check_invalid_states()
    check_broken_lineage()
    check_cycles()
```

---

# 16. ARCHITECTURE GUARANTEE

System must always satisfy:

- Deterministic outputs for identical inputs
- Single source of truth (Catalog)
- Explicit state transitions only
- Fully reconstructable DAG from Catalog
- No hidden dependencies

---

# 17. OUT OF SCOPE (DO NOT IMPLEMENT)

- REST API
- Authentication system
- Distributed execution
- Cloud sync
- GUI applications
- Real-time streaming DAG
- External integrations

---

# 18. SUCCESS CRITERIA

This phase is complete only if:

✓ Catalog Query layer is fully functional  
✓ Lifecycle engine enforces all transitions  
✓ Soft delete/archival is implemented  
✓ DAG remains purely derived  
✓ CLI supports full inspection + query  
✓ Integrity validation passes  
✓ No unsafe SQL or plugin behavior exists  
✓ System remains deterministic under repeated runs  

---

# FINAL INTENT

This phase transforms DFlow from:

> a workflow prototype

into:

> a deterministic catalog-driven data lifecycle engine with queryable lineage and safe state transitions

---

END OF SPEC

this should include: 
Catalog Query + Lifecycle Control layer (your next phase)
Core backend engine upgrades
Safety + robustness constraints (bug reduction, no unsafe execution patterns)
SQL improvements
CLI expansion
lineage + DAG correctness alignment
concrete code + pseudo-code examples
strict implementation rules to prevent drift

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

Do not use placeholders.

Do not leave TODOs.

Do not stub functionality.

Every component implemented in this phase must function exactly as intended.

**Don't just implement features. Audit the architecture continuously. If a name, module boundary, or responsibility no longer matches reality, propose a refactor before adding new functionality. Prefer architectural consistency over preserving earlier decisions.**
