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