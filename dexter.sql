-- Dexter Workspace Database Schema
-- Single source of truth for AI-first workspace

-- Action log - every operation Dexter performs
CREATE TABLE IF NOT EXISTS action_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT DEFAULT (datetime('now')),
    action_type TEXT NOT NULL,
    target TEXT,
    description TEXT,
    status TEXT DEFAULT 'completed',
    rollback_info TEXT
);

-- Rules - behavioral guardrails
CREATE TABLE IF NOT EXISTS rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name TEXT NOT NULL UNIQUE,
    category TEXT,
    priority INTEGER DEFAULT 5,
    condition TEXT,
    action TEXT NOT NULL,
    is_active INTEGER DEFAULT 1
);

-- Context - working memory for current task
CREATE TABLE IF NOT EXISTS context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT,
    expires_at TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Domains - organized work areas
CREATE TABLE IF NOT EXISTS domains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    path TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Checkpoints - verification points before destructive ops
CREATE TABLE IF NOT EXISTS checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_id INTEGER,
    checkpoint_type TEXT NOT NULL,
    state_snapshot TEXT,
    verified INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (action_id) REFERENCES action_log(id)
);

-- Default guardrail rules
INSERT OR IGNORE INTO rules (rule_name, category, priority, condition, action) VALUES
    ('no_blind_delete', 'destructive', 1, 'action contains DELETE or REMOVE', 'CREATE checkpoint THEN confirm THEN execute'),
    ('log_all_actions', 'audit', 1, 'always', 'INSERT into action_log before execution'),
    ('verify_after_change', 'quality', 2, 'action modifies file', 'READ file after change AND compare to intent'),
    ('stay_in_scope', 'focus', 2, 'file not in task scope', 'SKIP unless explicitly requested'),
    ('ask_once', 'autonomy', 3, 'ambiguous instruction', 'ASK for clarification ONCE then proceed with best judgment'),
    ('minimal_change', 'efficiency', 3, 'always', 'Make smallest change that achieves goal'),
    ('no_side_edits', 'focus', 2, 'touching unrelated code', 'STOP and reconsider scope');

-- Default domains
INSERT OR IGNORE INTO domains (name, description, path) VALUES
    ('hubspot', 'HubSpot CRM integration and automation', 'domains/hubspot'),
    ('google', 'Google Workspace (Gmail, Drive, Sheets, Apps Script)', 'domains/google'),
    ('automation', 'General automation scripts and workflows', 'domains/automation'),
    ('projects', 'Active project workspaces', 'domains/projects');
