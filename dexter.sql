-- Dexter Workspace Database Schema
-- Single source of truth for AI-first workspace

-- Action log - every operation Dexter performs
CREATE TABLE IF NOT EXISTS action_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action_type TEXT NOT NULL,
    target TEXT,
    description TEXT,
    status TEXT DEFAULT 'completed' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled')),
    rollback_info TEXT,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE SET NULL
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
    workspace_id INTEGER,
    key TEXT NOT NULL,
    value TEXT,
    expires_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    UNIQUE(workspace_id, key)
);

-- Domains - organized work areas
CREATE TABLE IF NOT EXISTS domains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER,
    name TEXT NOT NULL,
    description TEXT,
    path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    UNIQUE(workspace_id, name)
);

-- Checkpoints - verification points before destructive ops
CREATE TABLE IF NOT EXISTS checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_id INTEGER NOT NULL,
    checkpoint_type TEXT NOT NULL CHECK (checkpoint_type IN ('pre_delete', 'pre_modify', 'pre_create', 'backup', 'snapshot')),
    state_snapshot TEXT,
    verified INTEGER DEFAULT 0 CHECK (verified IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (action_id) REFERENCES action_log(id) ON DELETE CASCADE
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

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_action_log_workspace ON action_log(workspace_id);
CREATE INDEX IF NOT EXISTS idx_action_log_timestamp ON action_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_action_log_status ON action_log(status);
CREATE INDEX IF NOT EXISTS idx_context_workspace ON context(workspace_id);
CREATE INDEX IF NOT EXISTS idx_context_key ON context(key);
CREATE INDEX IF NOT EXISTS idx_context_expires ON context(expires_at);
CREATE INDEX IF NOT EXISTS idx_domains_workspace ON domains(workspace_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_action ON checkpoints(action_id);
CREATE INDEX IF NOT EXISTS idx_rules_category ON rules(category);
CREATE INDEX IF NOT EXISTS idx_rules_active ON rules(is_active);

-- Default domains (will be created per workspace, not globally)
-- Note: Domains are now workspace-specific, so these are examples only
