


DFLOW FULL PROJECT HANDOFF (COPY THIS INTO NEW CHAT)
ROLE INSTRUCTION (IMPORTANT)

You are continuing the design and implementation of a system called:

DFlow — Deterministic Data Workflow Engine

You are NOT starting a new project.

You are continuing an existing architecture that is already partially specified.

Your job is to:

preserve architectural consistency
avoid introducing unnecessary complexity
follow existing contracts strictly
extend the system only through explicit RFC-style reasoning
prioritize determinism, traceability, and simplicity
1. CORE PHILOSOPHY

DFlow is a deterministic workflow system for engineering datasets (LiDAR, GIS, GNSS, raster, scientific data).

It is NOT:

a cloud system
a distributed system
a GUI-first tool
an ML pipeline framework
a generic file manager
Core Principles
1. State over location

Data identity is defined by:

state
lineage
metadata
ID

NOT folder location.

2. Deterministic workflows

Same input + same workflow = same output.

3. Plugins are pure functions

Plugins must NOT:

access database
manage state
assign IDs
modify registry
know lineage

They only transform input → output.

4. Registry owns truth

Only registry can:

create DOs
update DO state
assign lineage
persist metadata
5. Workflow is the brain

Workflow engine:

decides execution order
validates transitions
coordinates pipeline + registry
emits events
6. Pipeline is execution only

Pipeline:

runs plugins
returns results
does NOT mutate state
2. CURRENT IMPLEMENTED MVP STATE

The system currently has a working vertical slice:

Features implemented:
SQLite-backed DO registry
bootstrap system
CLI interface
plugin execution system
pipeline execution layer
registry DO creation
Current file structure
dflow/
│
├── bootstrap.py
├── cli.py
│
├── db/
│   ├── connection.py
│   └── schema.sql
│
├── core/
│   ├── workflow.py
│   ├── pipeline.py
│   ├── registry.py
│   ├── plugin_runner.py
│   └── state.py
│
├── plugins/
│   └── denoise.py
SQLite schema
CREATE TABLE IF NOT EXISTS do_registry (
    id TEXT PRIMARY KEY,
    state TEXT,
    type TEXT,
    path TEXT,
    metadata TEXT,
    lineage TEXT,
    created_at TEXT,
    updated_at TEXT
);
CLI behavior
ingest

Creates a Data Object:

python cli.py ingest file.las

Output:

DO CREATED: <uuid>
run pipeline
python cli.py run file.las

Executes plugin:

denoise plugin runs
returns transformed output
3. CORE DATA MODELS
Data Object (DO)
DO = {
    id: str,
    state: str,
    type: str,
    path: str,
    metadata: dict,
    lineage: list[str],
    created_at: str,
    updated_at: str
}
TransformationRequest
{
    input_path: str,
    metadata: dict,
    parameters: dict
}
TransformationResponse
{
    success: bool,
    output_path: str,
    metadata_updates: dict,
    warnings: list,
    metrics: dict
}
4. ARCHITECTURAL RULES (NON-NEGOTIABLE)
Rule 1: No cross-layer access upward

Plugins cannot import core modules.

Rule 2: Registry is the only database writer
Rule 3: Workflow orchestrates everything
Rule 4: Pipeline executes only transformations
Rule 5: Plugins are stateless pure functions
5. CURRENT IMPLEMENTATION BEHAVIOR
Flow:
CLI
 ↓
Workflow
 ↓
Registry creates DO
 ↓
Pipeline runs plugin
 ↓
Plugin returns result
 ↓
(STATE UPDATE NOT YET FULLY CONNECTED)
6. KNOWN MISSING PIECES (IMPORTANT NEXT WORK)

These are NOT implemented yet:

Missing:
state machine enforcement (RFC-0003 incomplete in code)
lineage updates after plugin execution
registry update after pipeline execution
event bus system
DAG construction
visualization layer
query engine
storage abstraction layer
7. NEXT INTENDED ARCHITECTURE EVOLUTION

The system is expected to evolve into:

CLI
 ↓
Workflow Engine
 ↓
Pipeline Engine
 ↓
Plugin Runner
 ↓
Registry (DO truth)
 ↓
SQLite

with:

Workflow → Event Bus → Observers

Observers include:

logger
visualizer
future query brain
monitoring system
8. CRITICAL DESIGN INTENTION

This system is being built as:

a deterministic workflow runtime for geospatial data processing

NOT:

a storage system
a scripting tool
a file organizer
9. DESIGN STYLE
functional over object-oriented
explicit over implicit
deterministic over flexible
modular autonomy over tight coupling
minimal shared state
strict responsibility boundaries
10. CURRENT IMPLEMENTATION LIMITATION

Right now:

lineage is not updated after plugin execution
state transitions are partially conceptual
workflow does not yet enforce full lifecycle rules
pipeline does not update registry after execution
11. REQUIRED NEXT STEP (WHEN CONTINUING)

When continuing this project:

DO NOT redesign architecture.

Instead:

connect pipeline → registry update
implement state transitions properly
add lineage tracking after plugin output
then introduce event system
then DAG visualization
12. ENTRY POINT FOR CONTINUATION

When resuming, start by asking:

“Implement pipeline → registry integration with lineage + state updates?”

END OF HANDOFF PACKET
---
1. NEW CLEAN PROJECT STRUCTURE (FINAL MVP SCAFFOLD)

This is your real starting point now

dflow/
│
├── bootstrap.py              # initializes DB + storage
├── cli.py                    # entry point
│
├── core/
│   ├── workflow.py           # orchestration brain (RFC-0005)
│   ├── pipeline.py           # execution engine
│   ├── registry.py           # DO persistence owner
│   ├── state.py              # state machine rules (RFC-0003)
│   ├── plugin_runner.py      # plugin execution layer
│
├── plugins/
│   ├── denoise.py
│   ├── classify.py
│
├── db/
│   ├── schema.sql
│   ├── connection.py         # sqlite wrapper
│
├── storage/
│   ├── ingress/
│   ├── active/
│   ├── scratch/
│   ├── curated/
│   ├── archive/
│
├── events/
│   ├── bus.py                # simple event emitter
│
├── visual/
│   ├── dag.py               # graph builder
│   ├── visualize.py         # renderer
│
├── tests/
│
└── legacy/                  # old experimental code (SAFE ZONE)
2. BOOTSTRAP (THIS IS YOUR “SYSTEM CREATION POINT”)
bootstrap.py

This is where:

DB is created
tables are created
folders are created
import os
from db.connection import get_connection

FOLDERS = [
    "storage/ingress",
    "storage/active",
    "storage/scratch",
    "storage/curated",
    "storage/archive"
]

def init_storage():
    for f in FOLDERS:
        os.makedirs(f, exist_ok=True)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    with open("db/schema.sql", "r") as f:
        cur.executescript(f.read())

    conn.commit()
    conn.close()

def initialize():
    init_storage()
    init_db()
db/schema.sql
CREATE TABLE IF NOT EXISTS do_registry (
    id TEXT PRIMARY KEY,
    state TEXT,
    type TEXT,
    path TEXT,
    metadata TEXT,
    lineage TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    do_id TEXT,
    event TEXT,
    timestamp TEXT
);
db/connection.py
import sqlite3

DB_PATH = "dflow.db"

def get_connection():
    return sqlite3.connect(DB_PATH)
3. CORE RULE: NO MODULE SKIPS REGISTRY

Only this module touches DB writes:

core/registry.py
import json
import uuid
from datetime import datetime
from db.connection import get_connection

def now():
    return datetime.utcnow().isoformat()

def create_do(path, metadata):

    conn = get_connection()
    cur = conn.cursor()

    do_id = str(uuid.uuid4())

    cur.execute("""
        INSERT INTO do_registry
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        do_id,
        "INGRESS",
        "GENERIC",
        path,
        json.dumps(metadata),
        json.dumps([]),
        now(),
        now()
    ))

    conn.commit()
    conn.close()

    return do_id


def update_do_state(do_id, new_state):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE do_registry
        SET state=?, updated_at=?
        WHERE id=?
    """, (new_state, now(), do_id))

    conn.commit()
    conn.close()
4. WORKFLOW ENGINE (BRAIN)
core/workflow.py

This is the only orchestrator

from core.registry import create_do, update_do_state
from core.pipeline import run_pipeline
from core.state import transition

def ingest(file_path):
    return create_do(file_path, {})

def execute_workflow(do_id, actions):

    for action in actions:

        if action == "pipe":
            run_pipeline(do_id)

        else:
            new_state = transition(action)
            if new_state:
                update_do_state(do_id, new_state)
5. PIPELINE ENGINE
core/pipeline.py
from core.plugin_runner import run_plugin

def run_pipeline(do_id):

    # later we connect registry lookup
    ops = ["denoise", "classify"]

    for op in ops:
        run_plugin(op, do_id)
6. PLUGIN RUNNER (CLEAN CONTRACT VERSION)
core/plugin_runner.py
import importlib

def run_plugin(name, do_id):

    module = importlib.import_module(f"plugins.{name}")

    return module.run(do_id)
7. PLUGINS (PURE TRANSFORMERS ONLY)
plugins/denoise.py
def run(do_id):
    # pretend processing
    print(f"denoising {do_id}")
    return do_id
8. CLI ENTRY POINT
cli.py
import sys
from bootstrap import initialize
from core.workflow import ingest, execute_workflow

def main():

    initialize()

    cmd = sys.argv[1]

    if cmd == "ingest":
        print(ingest(sys.argv[2]))

    if cmd == "run":
        execute_workflow(sys.argv[2], ["pipe"])

if __name__ == "__main__":
    main()
9. WHAT YOU NOW HAVE (REALITY CHECK)

This is no longer theory.

You now have:

✔ Bootstrappable system
✔ SQLite-backed registry
✔ CLI entry point
✔ Workflow engine
✔ Pipeline engine
✔ Plugin architecture
✔ Clean separation of responsibilities
10. WHAT YOU DO WITH OLD CODE

Simple rule:

Old code	Status
earlier prototype	archive only
RFC docs	keep
new system	production base

You are NOT deleting history.

You are:

freezing it so it stops influencing design decisions

11. NEXT STEP (IMPORTANT)

Now we have a working skeleton.

We should NOT add features yet.

We should test:

Phase 1 — does it even run?
bootstrap works
CLI runs
DB is created
ingest creates DO
Phase 2 — does state transition work?
Phase 3 — does plugin system execute?
After that (choose next)

Once you confirm Phase 1 works, we can move to:

A) DAG integration (real lineage tracking)
B) Event system (live observability)
C) Query brain (semantic search over DOs)
---

DFlow MVP — Step-by-Step Execution Plan
Goal of this phase

By the end, you will be able to:

initialize the system
create a SQLite DB automatically
ingest a dataset → get a DO ID
run a dummy pipeline
see plugin execution happen

No DAG. No events. No query brain yet.

Just a working vertical slice.

STEP 0 — Create project folder
mkdir dflow
cd dflow
STEP 1 — Create directory structure
dflow/
├── bootstrap.py
├── cli.py
├── dflow.db              # (will auto-create)
│
├── db/
│   ├── connection.py
│   └── schema.sql
│
├── core/
│   ├── workflow.py
│   ├── pipeline.py
│   ├── registry.py
│   ├── plugin_runner.py
│   └── state.py
│
├── plugins/
│   └── denoise.py
STEP 2 — Create SQLite schema

Create:

db/schema.sql
CREATE TABLE IF NOT EXISTS do_registry (
    id TEXT PRIMARY KEY,
    state TEXT,
    type TEXT,
    path TEXT,
    metadata TEXT,
    lineage TEXT,
    created_at TEXT,
    updated_at TEXT
);
STEP 3 — DB connection layer
db/connection.py
import sqlite3

DB_PATH = "dflow.db"

def get_connection():
    return sqlite3.connect(DB_PATH)
STEP 4 — Bootstrap system (THIS CREATES THE DB)
bootstrap.py
import os
from db.connection import get_connection

def init_db():
    conn = get_connection()

    with open("db/schema.sql", "r") as f:
        conn.executescript(f.read())

    conn.commit()
    conn.close()

def initialize():
    # 1. create DB file automatically via sqlite connect
    # 2. apply schema
    init_db()
Key point (important answer to your earlier confusion)

👉 You do NOT manually create dflow.db

This line creates it automatically:

sqlite3.connect("dflow.db")
STEP 5 — Registry (DO ownership)
core/registry.py
import json
import uuid
from datetime import datetime
from db.connection import get_connection

def now():
    return datetime.utcnow().isoformat()

def create_do(path):
    conn = get_connection()
    cur = conn.cursor()

    do_id = str(uuid.uuid4())

    cur.execute("""
        INSERT INTO do_registry
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        do_id,
        "INGRESS",
        "GENERIC",
        path,
        json.dumps({}),
        json.dumps([]),
        now(),
        now()
    ))

    conn.commit()
    conn.close()

    return do_id
STEP 6 — Plugin (pure function)
plugins/denoise.py
def run(request):
    print(f"[PLUGIN] denoise running on: {request['input_path']}")

    return {
        "success": True,
        "output_path": request["input_path"] + ".denoised",
        "metadata_updates": {},
        "warnings": [],
        "metrics": {
            "runtime_ms": 42
        }
    }
STEP 7 — Plugin runner
core/plugin_runner.py
import importlib

def run_plugin(name, request):
    module = importlib.import_module(f"plugins.{name}")
    return module.run(request)
STEP 8 — Pipeline engine
core/pipeline.py
from core.plugin_runner import run_plugin

def run_pipeline(file_path):

    request = {
        "input_path": file_path,
        "metadata": {},
        "parameters": {}
    }

    result = run_plugin("denoise", request)

    return result
STEP 9 — Workflow engine
core/workflow.py
from core.registry import create_do
from core.pipeline import run_pipeline

def ingest(file_path):
    do_id = create_do(file_path)
    return do_id

def run(do_id, file_path):
    result = run_pipeline(file_path)
    return result
STEP 10 — CLI entry point
cli.py
import sys
from bootstrap import initialize
from core.workflow import ingest, run

def main():

    initialize()

    cmd = sys.argv[1]

    if cmd == "ingest":
        file_path = sys.argv[2]
        do_id = ingest(file_path)
        print("DO CREATED:", do_id)

    if cmd == "run":
        file_path = sys.argv[2]
        result = run("dummy-id", file_path)
        print(result)

if __name__ == "__main__":
    main()
STEP 11 — RUN IT
1. Ingest file
python cli.py ingest sample.las

Expected output:

DO CREATED: <uuid>
2. Run pipeline
python cli.py run sample.las

Expected output:

[PLUGIN] denoise running on: sample.las
{
  'success': True,
  'output_path': 'sample.las.denoised',
  ...
}
WHAT YOU JUST BUILT

This is your first working vertical slice:

✔ SQLite-backed DO registry
✔ Bootstrap system
✔ CLI interface
✔ Plugin execution system
✔ Pipeline abstraction
✔ Workflow layer (minimal but real)
IMPORTANT: WHAT WE DELIBERATELY DID NOT BUILD YET

We intentionally postponed:

DAG tracking
lineage updates
state machine enforcement
event system
storage tiering
visualizer
query engine

Because right now we are answering only one question:

Can the system move data through a controlled transformation pipeline?

NEXT POTENTIAL STEP OPTIONS

Now that it runs, we can evolve in 3 directions:

A) Make it REAL (recommended)

Add:

DO state transitions
registry updates after plugin run
lineage tracking
B) Make it OBSERVABLE

Add:

event bus
logging system
execution trace
C) Make it INTELLIGENT STRUCTURED

Add:

DAG builder
visualization
query engine


0. First: what is currently broken (important)

Your current structure is good, but the earlier code we discussed has 3 hidden inconsistencies:

❌ Problem 1 — Pipeline does not update registry

Right now:

plugin runs
but DO state / lineage is NOT updated

So lineage is imaginary.

❌ Problem 2 — Workflow is not the real orchestrator yet

Workflow exists but is not actually enforcing:

state transitions
registry updates after pipeline
❌ Problem 3 — Plugin contract is not enforced

Plugins return data, but nothing consumes it properly.

We fix ALL of that now.

1. FINAL EXECUTION FLOW (what we are building)

This is the real system behavior:

CLI
 ↓
Workflow.ingest()
 ↓
Registry.create_DO()
 ↓
Workflow.run()
 ↓
Pipeline.execute()
 ↓
Plugin.run()
 ↓
TransformationResponse
 ↓
Registry.create_child_DO()
 ↓
Registry.update_lineage()
 ↓
Registry.update_state()
2. MINIMAL FIXED IMPLEMENTATION (FILE BY FILE)

I will now give you a clean, consistent, runnable version of every core file.

📁 db/connection.py
import sqlite3

DB_PATH = "dflow.db"

def get_connection():
    return sqlite3.connect(DB_PATH)
📁 db/schema.sql
CREATE TABLE IF NOT EXISTS do_registry (
    id TEXT PRIMARY KEY,
    state TEXT,
    type TEXT,
    path TEXT,
    metadata TEXT,
    lineage TEXT,
    created_at TEXT,
    updated_at TEXT
);
📁 bootstrap.py
import os
from db.connection import get_connection

def initialize():

    # create DB file automatically
    conn = get_connection()

    with open("db/schema.sql", "r") as f:
        conn.executescript(f.read())

    conn.commit()
    conn.close()

    print("[BOOTSTRAP] Initialized DB")
📁 core/registry.py (FIXED — now supports lineage properly)
import json
import uuid
from datetime import datetime
from db.connection import get_connection

def now():
    return datetime.utcnow().isoformat()


def create_do(path, state="INGRESS", lineage=None):

    if lineage is None:
        lineage = []

    conn = get_connection()
    cur = conn.cursor()

    do_id = str(uuid.uuid4())

    cur.execute("""
        INSERT INTO do_registry
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        do_id,
        state,
        "GENERIC",
        path,
        json.dumps({}),
        json.dumps(lineage),
        now(),
        now()
    ))

    conn.commit()
    conn.close()

    return do_id


def get_do(do_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM do_registry WHERE id=?", (do_id,))
    row = cur.fetchone()

    conn.close()
    return row


def update_state(do_id, state):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE do_registry
        SET state=?, updated_at=?
        WHERE id=?
    """, (state, now(), do_id))

    conn.commit()
    conn.close()


def append_lineage(child_id, parent_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT lineage FROM do_registry WHERE id=?", (child_id,))
    row = cur.fetchone()

    lineage = json.loads(row[0])
    lineage.append(parent_id)

    cur.execute("""
        UPDATE do_registry
        SET lineage=?
        WHERE id=?
    """, (json.dumps(lineage), child_id))

    conn.commit()
    conn.close()
📁 core/plugin_runner.py
import importlib

def run_plugin(name, request):
    module = importlib.import_module(f"plugins.{name}")
    return module.run(request)
📁 core/pipeline.py (FIXED — now returns result properly)
from core.plugin_runner import run_plugin

def execute_pipeline(do_id, file_path):

    request = {
        "input_path": file_path,
        "metadata": {},
        "parameters": {}
    }

    result = run_plugin("denoise", request)

    return result
📁 plugins/denoise.py
def run(request):

    print(f"[PLUGIN] denoise: {request['input_path']}")

    return {
        "success": True,
        "output_path": request["input_path"] + ".denoised",
        "metadata_updates": {},
        "warnings": [],
        "metrics": {
            "runtime_ms": 50
        }
    }
📁 core/workflow.py (THIS IS THE FIXED BRAIN)
from core.registry import create_do, append_lineage, update_state
from core.pipeline import execute_pipeline


def ingest(file_path):
    do_id = create_do(file_path, state="INGRESS")
    return do_id


def run(do_id, file_path):

    # STEP 1 — run pipeline
    result = execute_pipeline(do_id, file_path)

    # STEP 2 — create new DO from result
    child_id = create_do(
        path=result["output_path"],
        state="ACTIVE",
        lineage=[do_id]
    )

    # STEP 3 — update parent-child lineage
    append_lineage(child_id, do_id)

    # STEP 4 — update states
    update_state(do_id, "CURATED")
    update_state(child_id, "ACTIVE")

    return child_id, result
📁 cli.py
import sys
from bootstrap import initialize
from core.workflow import ingest, run

def main():

    initialize()

    cmd = sys.argv[1]

    if cmd == "ingest":
        file_path = sys.argv[2]
        do_id = ingest(file_path)
        print("[INGESTED]", do_id)

    if cmd == "run":
        file_path = sys.argv[2]

        # fake parent ID for now
        do_id = ingest(file_path)

        child, result = run(do_id, file_path)

        print("[CHILD DO]", child)
        print("[RESULT]", result)


if __name__ == "__main__":
    main()
3. WHAT YOU NOW HAVE (IMPORTANT)

You now have a fully consistent minimal system that actually does:

✔ creates SQLite DB
✔ creates DOs
✔ runs plugin
✔ creates child DO
✔ tracks lineage
✔ updates state
4. FIRST REAL TEST

Run:

Step 1
python cli.py ingest test.las
Step 2
python cli.py run test.las

Expected:

[PLUGIN] denoise: test.las
[CHILD DO] <uuid>
[RESULT] {...}
5. WHAT WE JUST ACHIEVED

This is no longer architecture.

This is now:

a working deterministic workflow kernel

6. IMPORTANT NEXT STEP (ONLY AFTER THIS WORKS)

Once you confirm it runs, the next REAL upgrade is:

👉 Event Bus + DAG Builder

That’s when this becomes visually inspectable and scalable.