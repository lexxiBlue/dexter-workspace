-- Dexter Workspace Database Schema
-- Single consolidated schema: workspace config + project management + agent intelligence + roadmap
-- "A house for AI" - everything Dexter needs to be self-aware, autonomous, and recoverable

-- ============================================================================
-- WORKSPACE CORE
-- ============================================================================

CREATE TABLE IF NOT EXISTS workspaces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    project_type TEXT DEFAULT 'general' CHECK (project_type IN ('general', 'web', 'data', 'api', 'automation', 'mobile', 'desktop')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- WORKSPACE CONFIGURATION PERSISTENCE
-- ============================================================================

-- Mirror Cursor config, .env, .cursorignore, mcp.json, etc.
CREATE TABLE IF NOT EXISTS workspace_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    source TEXT,                    -- 'cursor_settings', 'mcp.json', '.cursorignore', '.env'
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (workspace_id, key, source),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

-- Dependencies to install at handoff
CREATE TABLE IF NOT EXISTS workspace_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER NOT NULL,
    name TEXT NOT NULL,              -- 'ruff', 'pytest', 'mypy', 'requests'
    version_spec TEXT,               -- '>=0.4,<0.5' or '==1.2.3'
    install_command TEXT,            -- 'pip install', 'npm install'
    package_manager TEXT,            -- 'pip', 'npm', 'cargo', 'brew'
    required INTEGER DEFAULT 1,      -- 1=hard requirement, 0=optional
    installed INTEGER DEFAULT 0,     -- 1=already installed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (workspace_id, name),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

-- ============================================================================
-- CURSOR CONFIGURATION STORAGE
-- ============================================================================

CREATE TABLE IF NOT EXISTS cursor_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER NOT NULL,
    rule_name TEXT NOT NULL,
    description TEXT,
    globs TEXT,
    rule_type TEXT DEFAULT 'always' CHECK (rule_type IN ('always', 'suggestion', 'warning', 'error')),
    content TEXT NOT NULL,
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS integrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER NOT NULL,
    integration_type TEXT NOT NULL,
    name TEXT NOT NULL,
    config_json TEXT CHECK (json_valid(config_json) OR config_json IS NULL),
    api_key_env_var TEXT,
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    FOREIGN KEY (integration_type) REFERENCES integration_types(type_name)
);

CREATE TABLE IF NOT EXISTS integration_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name TEXT NOT NULL UNIQUE,
    display_name TEXT,
    config_template TEXT,
    documentation_url TEXT
);

INSERT OR IGNORE INTO integration_types (type_name, display_name, config_template, documentation_url) VALUES
    ('google_gmail', 'Gmail', '{"scopes": ["gmail.readonly", "gmail.send"]}', 'https://developers.google.com/gmail/api'),
    ('google_drive', 'Google Drive', '{"scopes": ["drive.readonly", "drive.file"]}', 'https://developers.google.com/drive/api'),
    ('google_sheets', 'Google Sheets', '{"scopes": ["spreadsheets"]}', 'https://developers.google.com/sheets/api'),
    ('google_appscript', 'Google Apps Script', '{"scopes": ["script.projects"]}', 'https://developers.google.com/apps-script/api'),
    ('hubspot', 'HubSpot CRM', '{"scopes": ["crm.objects.contacts.read", "crm.objects.deals.read"]}', 'https://developers.hubspot.com/docs/api'),
    ('openai', 'OpenAI', '{"model": "gpt-4"}', 'https://platform.openai.com/docs'),
    ('tavily', 'Tavily Search', '{"search_depth": "advanced"}', 'https://tavily.com/docs'),
    ('github', 'GitHub', '{"scopes": ["repo", "user"]}', 'https://docs.github.com/en/rest');

CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    project_type TEXT CHECK (project_type IN ('general', 'web', 'data', 'api', 'automation', 'mobile', 'desktop') OR project_type IS NULL),
    rules_json TEXT CHECK (json_valid(rules_json) OR rules_json IS NULL),
    settings_json TEXT CHECK (json_valid(settings_json) OR settings_json IS NULL),
    integrations_json TEXT CHECK (json_valid(integrations_json) OR integrations_json IS NULL),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO templates (name, description, project_type, rules_json, settings_json) VALUES
    ('web_fullstack', 'Full-stack web development', 'web', '["core", "frontend", "backend", "api"]', '{"tabSize": 2, "formatOnSave": true}'),
    ('python_data', 'Python data science', 'data', '["core", "python", "data_science"]', '{"tabSize": 4, "formatOnSave": true}'),
    ('api_backend', 'Backend API development', 'api', '["core", "backend", "api", "database"]', '{"tabSize": 2, "formatOnSave": true}'),
    ('automation', 'Automation and scripting', 'automation', '["core", "python", "automation"]', '{"tabSize": 4, "formatOnSave": true}');

CREATE TABLE IF NOT EXISTS mcp_servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER NOT NULL,
    server_name TEXT NOT NULL,
    server_type TEXT,
    config_json TEXT CHECK (json_valid(config_json) OR config_json IS NULL),
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER,           -- NULL = global, otherwise workspace-scoped
    key TEXT NOT NULL,
    value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (workspace_id, key),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

INSERT OR IGNORE INTO preferences (workspace_id, key, value, description) VALUES
    (NULL, 'default_model', 'gpt-4', 'Default AI model for Cursor'),
    (NULL, 'vim_mode', 'false', 'Enable Vim keybindings'),
    (NULL, 'auto_save', 'true', 'Auto-save files'),
    (NULL, 'format_on_save', 'true', 'Format code on save'),
    (NULL, 'context_length', '8000', 'AI context length'),
    (NULL, 'privacy_mode', 'true', 'Enable privacy mode');

-- ============================================================================
-- PROJECTS (Scoped Autonomy & Role-Based Work)
-- ============================================================================

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER NOT NULL,
    slug TEXT NOT NULL UNIQUE,       -- 'project1_automation-suite'
    name TEXT NOT NULL,
    status TEXT DEFAULT 'active',    -- 'active', 'paused', 'completed', 'archived'
    role_prompt TEXT,                -- How Dexter should behave
    scope_json TEXT,                 -- Structured SOW
    success_criteria_json TEXT,      -- How to judge done/success
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS project_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    agent_session_id INTEGER,
    status TEXT DEFAULT 'running',   -- 'running', 'completed', 'failed', 'paused'
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    summary TEXT,
    error_count INTEGER DEFAULT 0,
    action_count INTEGER DEFAULT 0,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- ============================================================================
-- AGENT SESSIONS & ERROR HANDLING
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    workspace_id INTEGER,
    entry_command TEXT NOT NULL,     -- '/Handoff', '/project1_name'
    user_prompt TEXT,
    model TEXT,
    status TEXT DEFAULT 'running',   -- 'running', 'completed', 'failed', 'paused'
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    summary TEXT,
    session_notes TEXT,
    action_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS agent_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_session_id INTEGER NOT NULL,
    action_id INTEGER,
    error_type TEXT NOT NULL,        -- 'sqlite.OperationalError', 'HTTPError', etc.
    message TEXT NOT NULL,
    context_snapshot TEXT,           -- JSON of state
    retryable INTEGER DEFAULT 0,
    handled INTEGER DEFAULT 0,
    playbook_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    FOREIGN KEY (agent_session_id) REFERENCES agent_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (playbook_id) REFERENCES agent_playbooks(id) ON DELETE SET NULL
);

-- ============================================================================
-- PLAYBOOKS (Self-Healing Strategies)
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_playbooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,        -- 'migration_sqlite_locked'
    category TEXT,                   -- 'recovery', 'optimization', 'validation'
    trigger_pattern TEXT NOT NULL,   -- regex or pattern
    detection_query TEXT,            -- SQL to detect situation
    remediation_steps_json TEXT NOT NULL, -- ordered steps
    preconditions_json TEXT,         -- safety checks
    postconditions_json TEXT,        -- verification
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- AGENT INTELLIGENCE (Memory, Knowledge, Patterns, State)
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER,
    topic TEXT NOT NULL,
    fact TEXT NOT NULL,
    source TEXT,
    confidence REAL DEFAULT 1.0 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    verified INTEGER DEFAULT 0 CHECK (verified IN (0, 1)),
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agent_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER,
    decision_type TEXT NOT NULL,
    input_context TEXT,
    reasoning TEXT,
    decision TEXT NOT NULL,
    outcome TEXT,
    success INTEGER DEFAULT 1 CHECK (success IN (0, 1)),
    learned_from INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    FOREIGN KEY (learned_from) REFERENCES agent_decisions(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS agent_memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    workspace_id INTEGER,
    agent_session_id INTEGER,
    category TEXT NOT NULL,         -- 'reflection', 'decision', 'pattern', 'constraint', 'optimization'
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata_json TEXT,
    importance INTEGER DEFAULT 1,   -- 1-5
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_session_id) REFERENCES agent_sessions(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS agent_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER,
    pattern_name TEXT NOT NULL,
    pattern_type TEXT CHECK (pattern_type IN ('success', 'failure', 'optimization', 'warning')),
    trigger_conditions TEXT,
    action_taken TEXT,
    success_rate REAL DEFAULT 0.0 CHECK (success_rate >= 0.0 AND success_rate <= 1.0),
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agent_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER,
    state_key TEXT NOT NULL,
    state_value TEXT,
    state_type TEXT CHECK (state_type IN ('preference', 'memory', 'goal', 'constraint')),
    expires_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    UNIQUE(workspace_id, state_key)
);

-- ============================================================================
-- KNOWLEDGE BASE (Search Results, Web Crawls)
-- ============================================================================

CREATE TABLE IF NOT EXISTS knowledge_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    workspace_id INTEGER,
    source_type TEXT NOT NULL,      -- 'web', 'mcp_github', 'mcp_file', 'internal_file'
    source_id TEXT,                 -- URL, path
    title TEXT,
    snippet TEXT,
    content_hash TEXT,
    metadata_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS search_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    agent_session_id INTEGER,
    query TEXT NOT NULL,
    provider TEXT,                  -- 'search_web', 'crawl_mcp'
    result_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (agent_session_id) REFERENCES agent_sessions(id) ON DELETE SET NULL
);

-- ============================================================================
-- CORE RUNTIME TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS action_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_session_id INTEGER,
    project_id INTEGER,
    workspace_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action_type TEXT NOT NULL,
    target TEXT,
    description TEXT,
    status TEXT DEFAULT 'completed' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled')),
    rollback_info TEXT,
    FOREIGN KEY (agent_session_id) REFERENCES agent_sessions(id) ON DELETE SET NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name TEXT NOT NULL UNIQUE,
    category TEXT,
    priority INTEGER DEFAULT 5,
    condition TEXT,
    action TEXT NOT NULL,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS rule_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER,
    rule_file TEXT NOT NULL UNIQUE,
    title TEXT,
    description TEXT,
    globs TEXT,
    rule_type TEXT,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_session_id INTEGER,
    workspace_id INTEGER,
    key TEXT NOT NULL,
    value TEXT,
    expires_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_session_id) REFERENCES agent_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    UNIQUE(agent_session_id, workspace_id, key)
);

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

CREATE TABLE IF NOT EXISTS checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_id INTEGER NOT NULL,
    checkpoint_type TEXT NOT NULL CHECK (checkpoint_type IN ('pre_delete', 'pre_modify', 'pre_create', 'backup', 'snapshot')),
    state_snapshot TEXT,
    verified INTEGER DEFAULT 0 CHECK (verified IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (action_id) REFERENCES action_log(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS health_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER,
    project_id INTEGER,
    name TEXT NOT NULL,
    target_type TEXT NOT NULL,      -- 'db_schema', 'file_integrity', 'integration_config', 'dependency'
    check_query_or_script TEXT NOT NULL,
    auto_fix_playbook_id INTEGER,
    last_run_at TIMESTAMP,
    last_status TEXT,               -- 'ok', 'warn', 'fail'
    last_message TEXT,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (auto_fix_playbook_id) REFERENCES agent_playbooks(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS workspace_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER NOT NULL,
    snapshot_type TEXT NOT NULL,    -- 'schema', 'config', 'dependencies', 'rules'
    label TEXT,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

-- ============================================================================
-- ROADMAP & VISION (Long-term Goals & Self-Awareness)
-- ============================================================================

CREATE TABLE IF NOT EXISTS roadmap (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phase INTEGER NOT NULL,         -- 1, 2, 3+
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'planned',  -- 'planned', 'in_progress', 'completed', 'blocked'
    motivation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS roadmap_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roadmap_id INTEGER NOT NULL,
    sequence INTEGER,
    title TEXT NOT NULL,
    description TEXT,
    acceptance_criteria TEXT,
    status TEXT DEFAULT 'planned',  -- 'planned', 'active', 'completed', 'blocked'
    estimated_effort TEXT,          -- 'small', 'medium', 'large'
    dependencies_json TEXT,
    related_playbooks_json TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (roadmap_id) REFERENCES roadmap(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS vision_statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,         -- 'core_mission', 'user_goals', 'technical_ideals', 'constraints'
    statement TEXT NOT NULL,
    rationale TEXT,
    linked_roadmap_items_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS architecture_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_date TEXT,
    title TEXT NOT NULL,
    context TEXT NOT NULL,
    decision TEXT NOT NULL,
    rationale TEXT NOT NULL,
    alternatives_considered TEXT,
    trade_offs TEXT,
    status TEXT DEFAULT 'accepted',  -- 'proposed', 'accepted', 'deprecated', 'superseded'
    superseded_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- DEFAULT DATA
-- ============================================================================

INSERT OR IGNORE INTO rules (rule_name, category, priority, condition, action) VALUES
    ('no_blind_delete', 'destructive', 1, 'action contains DELETE or REMOVE', 'CREATE checkpoint THEN confirm THEN execute'),
    ('log_all_actions', 'audit', 1, 'always', 'INSERT into action_log before execution'),
    ('verify_after_change', 'quality', 2, 'action modifies file', 'READ file after change AND compare to intent'),
    ('stay_in_scope', 'focus', 2, 'file not in task scope', 'SKIP unless explicitly requested'),
    ('ask_once', 'autonomy', 3, 'ambiguous instruction', 'ASK for clarification ONCE then proceed with best judgment'),
    ('minimal_change', 'efficiency', 3, 'always', 'Make smallest change that achieves goal'),
    ('no_side_edits', 'focus', 2, 'touching unrelated code', 'STOP and reconsider scope'),
    ('learn_from_errors', 'growth', 2, 'error handled successfully', 'UPDATE agent_playbooks and agent_memories with pattern'),
    ('recover_proactively', 'resilience', 2, 'health_check fails', 'Query agent_playbooks for auto_fix and execute if safe');

-- Phase 1: Foundation
INSERT OR IGNORE INTO roadmap (phase, title, description, status, motivation) VALUES
    (1, 'Foundation: Schema & Self-Awareness', 'Build complete schema with session tracking, error handling, memory, health checks', 'in_progress', 'Establish Dexter as self-aware autonomous agent');

INSERT OR IGNORE INTO roadmap_items (roadmap_id, sequence, title, description, acceptance_criteria, status) 
SELECT (SELECT id FROM roadmap WHERE phase = 1), 1, 'Agent sessions & error tracking', 'Full session tracking with error context', 'Dexter logs every session and error with recovery context', 'in_progress';

INSERT OR IGNORE INTO roadmap_items (roadmap_id, sequence, title, description, acceptance_criteria, status) 
SELECT (SELECT id FROM roadmap WHERE phase = 1), 2, 'Memory & reflections', 'agent_memories table with workspace scoping', 'Dexter writes insights after each task', 'in_progress';

INSERT OR IGNORE INTO roadmap_items (roadmap_id, sequence, title, description, acceptance_criteria, status) 
SELECT (SELECT id FROM roadmap WHERE phase = 1), 3, 'Playbooks & error recovery', 'Playbooks with remediation; errors trigger recovery', 'Dexter recovers from error classes autonomously', 'in_progress';

-- Core vision
INSERT OR IGNORE INTO vision_statements (category, statement, rationale) VALUES
    ('core_mission', 'Dexter is a self-aware, autonomous agent manager for hands-off task delegation', 'Clear identity and purpose'),
    ('core_mission', 'Every configuration, decision, memory, and error is queryable and persistent', 'Total self-awareness and recovery capability'),
    ('user_goals', 'User delegates projects with scope; Dexter researches, plans, executes, self-heals', 'Hands-off sufficiency'),
    ('user_goals', 'Dexter learns from every error and successful recovery', 'Continuous improvement and autonomy'),
    ('technical_ideals', 'Single consolidated schema; every table has clear purpose and FK relationships', 'Clean, maintainable architecture'),
    ('technical_ideals', 'Cursor config mirrored in DB for full recovery without filesystem dependence', 'Total control and reproducibility'),
    ('constraints', 'Dexter operates within guardrails defined in rules and project role_prompts', 'Safe autonomy'),
    ('constraints', 'Dexter asks confirmation on destructive ops, schema changes, external side effects', 'User remains in control');

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_workspace_settings_workspace ON workspace_settings(workspace_id);
CREATE INDEX IF NOT EXISTS idx_workspace_dependencies_workspace ON workspace_dependencies(workspace_id);
CREATE INDEX IF NOT EXISTS idx_cursor_rules_workspace ON cursor_rules(workspace_id);
CREATE INDEX IF NOT EXISTS idx_cursor_rules_active ON cursor_rules(is_active);
CREATE INDEX IF NOT EXISTS idx_integrations_workspace ON integrations(workspace_id);
CREATE INDEX IF NOT EXISTS idx_integrations_type ON integrations(integration_type);
CREATE INDEX IF NOT EXISTS idx_integrations_active ON integrations(is_active);
CREATE INDEX IF NOT EXISTS idx_mcp_workspace ON mcp_servers(workspace_id);
CREATE INDEX IF NOT EXISTS idx_mcp_active ON mcp_servers(is_active);
CREATE INDEX IF NOT EXISTS idx_workspaces_project_type ON workspaces(project_type);
CREATE INDEX IF NOT EXISTS idx_preferences_key ON preferences(key);
CREATE INDEX IF NOT EXISTS idx_projects_workspace ON projects(workspace_id);
CREATE INDEX IF NOT EXISTS idx_projects_slug ON projects(slug);
CREATE INDEX IF NOT EXISTS idx_project_runs_project ON project_runs(project_id);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_project ON agent_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_workspace ON agent_sessions(workspace_id);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_status ON agent_sessions(status);
CREATE INDEX IF NOT EXISTS idx_agent_errors_session ON agent_errors(agent_session_id);
CREATE INDEX IF NOT EXISTS idx_agent_errors_type ON agent_errors(error_type);
CREATE INDEX IF NOT EXISTS idx_agent_errors_handled ON agent_errors(handled);
CREATE INDEX IF NOT EXISTS idx_action_log_session ON action_log(agent_session_id);
CREATE INDEX IF NOT EXISTS idx_action_log_workspace ON action_log(workspace_id);
CREATE INDEX IF NOT EXISTS idx_action_log_timestamp ON action_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_action_log_status ON action_log(status);
CREATE INDEX IF NOT EXISTS idx_context_session ON context(agent_session_id);
CREATE INDEX IF NOT EXISTS idx_context_key ON context(key);
CREATE INDEX IF NOT EXISTS idx_context_expires ON context(expires_at);
CREATE INDEX IF NOT EXISTS idx_domains_workspace ON domains(workspace_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_action ON checkpoints(action_id);
CREATE INDEX IF NOT EXISTS idx_rules_category ON rules(category);
CREATE INDEX IF NOT EXISTS idx_rules_active ON rules(is_active);
CREATE INDEX IF NOT EXISTS idx_rule_docs_workspace ON rule_documents(workspace_id);
CREATE INDEX IF NOT EXISTS idx_rule_docs_file ON rule_documents(rule_file);
CREATE INDEX IF NOT EXISTS idx_knowledge_workspace ON agent_knowledge(workspace_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_topic ON agent_knowledge(topic);
CREATE INDEX IF NOT EXISTS idx_knowledge_confidence ON agent_knowledge(confidence);
CREATE INDEX IF NOT EXISTS idx_decisions_workspace ON agent_decisions(workspace_id);
CREATE INDEX IF NOT EXISTS idx_decisions_type ON agent_decisions(decision_type);
CREATE INDEX IF NOT EXISTS idx_decisions_success ON agent_decisions(success);
CREATE INDEX IF NOT EXISTS idx_memories_project ON agent_memories(project_id);
CREATE INDEX IF NOT EXISTS idx_memories_workspace ON agent_memories(workspace_id);
CREATE INDEX IF NOT EXISTS idx_memories_category ON agent_memories(category);
CREATE INDEX IF NOT EXISTS idx_patterns_workspace ON agent_patterns(workspace_id);
CREATE INDEX IF NOT EXISTS idx_patterns_type ON agent_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_state_workspace ON agent_state(workspace_id);
CREATE INDEX IF NOT EXISTS idx_state_key ON agent_state(state_key);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_project ON knowledge_items(project_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_items_workspace ON knowledge_items(workspace_id);
CREATE INDEX IF NOT EXISTS idx_search_queries_project ON search_queries(project_id);
CREATE INDEX IF NOT EXISTS idx_health_checks_workspace ON health_checks(workspace_id);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES & INTROSPECTION
-- ============================================================================

CREATE VIEW IF NOT EXISTS view_active_rules AS
SELECT * FROM cursor_rules WHERE is_active = 1;

CREATE VIEW IF NOT EXISTS view_active_global_rules AS
SELECT * FROM rules WHERE is_active = 1 ORDER BY priority;

CREATE VIEW IF NOT EXISTS view_recent_decisions AS
SELECT * FROM agent_decisions
WHERE created_at > datetime('now', '-7 days')
ORDER BY created_at DESC;

CREATE VIEW IF NOT EXISTS view_successful_decisions AS
SELECT * FROM agent_decisions
WHERE success = 1
ORDER BY created_at DESC;

CREATE VIEW IF NOT EXISTS view_active_integrations AS
SELECT * FROM integrations WHERE is_active = 1;

CREATE VIEW IF NOT EXISTS view_system_stats AS
SELECT
    (SELECT COUNT(*) FROM workspaces) as workspace_count,
    (SELECT COUNT(*) FROM projects) as project_count,
    (SELECT COUNT(*) FROM agent_sessions) as session_count,
    (SELECT COUNT(*) FROM action_log) as action_total,
    (SELECT COUNT(*) FROM action_log WHERE status = 'completed') as action_completed,
    (SELECT COUNT(*) FROM action_log WHERE status = 'failed') as action_failed,
    (SELECT COUNT(*) FROM agent_errors WHERE handled = 0) as unhandled_errors,
    (SELECT COUNT(*) FROM agent_knowledge) as knowledge_count,
    (SELECT COUNT(*) FROM agent_memories) as memory_count,
    (SELECT COUNT(*) FROM agent_playbooks) as playbook_count;

CREATE VIEW IF NOT EXISTS view_agent_intelligence AS
SELECT
    w.id as workspace_id,
    (SELECT COUNT(*) FROM agent_knowledge WHERE workspace_id = w.id) as knowledge_count,
    (SELECT COUNT(*) FROM agent_decisions WHERE workspace_id = w.id) as decision_count,
    (SELECT COUNT(*) FROM agent_patterns WHERE workspace_id = w.id) as pattern_count,
    (SELECT COUNT(*) FROM agent_state WHERE workspace_id = w.id) as state_count,
    (SELECT COUNT(*) FROM agent_memories WHERE workspace_id = w.id) as memory_count
FROM workspaces w
UNION ALL
SELECT
    NULL as workspace_id,
    (SELECT COUNT(*) FROM agent_knowledge WHERE workspace_id IS NULL) as knowledge_count,
    (SELECT COUNT(*) FROM agent_decisions WHERE workspace_id IS NULL) as decision_count,
    (SELECT COUNT(*) FROM agent_patterns WHERE workspace_id IS NULL) as pattern_count,
    (SELECT COUNT(*) FROM agent_state WHERE workspace_id IS NULL) as state_count,
    (SELECT COUNT(*) FROM agent_memories WHERE workspace_id IS NULL) as memory_count;

CREATE VIEW IF NOT EXISTS view_successful_patterns AS
SELECT * FROM agent_patterns
WHERE success_rate >= 0.7
ORDER BY success_rate DESC, usage_count DESC;

CREATE VIEW IF NOT EXISTS view_high_confidence_knowledge AS
SELECT * FROM agent_knowledge
WHERE confidence >= 0.8
ORDER BY confidence DESC, usage_count DESC;

CREATE VIEW IF NOT EXISTS view_expired_context AS
SELECT * FROM context
WHERE expires_at IS NOT NULL
AND expires_at < datetime('now');

CREATE VIEW IF NOT EXISTS view_old_completed_actions AS
SELECT * FROM action_log
WHERE status = 'completed'
AND timestamp < datetime('now', '-30 days');

CREATE VIEW IF NOT EXISTS view_project_status AS
SELECT
    p.id,
    p.slug,
    p.name,
    p.status,
    (SELECT COUNT(*) FROM project_runs WHERE project_id = p.id) as run_count,
    (SELECT COUNT(*) FROM agent_memories WHERE project_id = p.id) as memory_count
FROM projects p;

CREATE VIEW IF NOT EXISTS view_roadmap_progress AS
SELECT
    r.phase,
    r.title,
    r.status as phase_status,
    (SELECT COUNT(*) FROM roadmap_items WHERE roadmap_id = r.id AND status = 'completed') as completed,
    (SELECT COUNT(*) FROM roadmap_items WHERE roadmap_id = r.id) as total
FROM roadmap r
ORDER BY r.phase;
