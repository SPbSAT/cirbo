CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS benchmarks_library (
    id INTEGER PRIMARY KEY,
    function TEXT,
    format TEXT,
    description TEXT,
    storage_link TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS agents_schedule (
    agent_id INTEGER NOT NULL,
    skill_name TEXT NOT NULL,
    PRIMARY KEY (agent_id, skill_name)
);

INSERT OR IGNORE INTO schema_migrations (version, name, applied_at)
VALUES (1, '001_init.sql', datetime('now'));
