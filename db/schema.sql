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

-- Indexes for query performance (RFC-0008)
CREATE INDEX IF NOT EXISTS idx_state ON do_registry(state);
CREATE INDEX IF NOT EXISTS idx_path ON do_registry(path);
CREATE INDEX IF NOT EXISTS idx_created ON do_registry(created_at);