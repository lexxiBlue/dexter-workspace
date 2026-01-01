-- Dexter Workspace Database Schema
-- Single consolidated schema file for all tables
-- Loads workspace configuration tables first, then runtime tables

-- ============================================================================
-- WORKSPACE CONFIGURATION TABLES (loaded first)
-- ============================================================================

-- Workspace configurations table
CREATE TABLE IF NOT EXISTS workspaces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    project_type TEXT DEFAULT 'general' CHECK (project_type IN ('general', 'web', 'data', 'api', 'automation', 'mobile', 'desktop')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cursor rules storage
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

-- Integration configurations
CREATE TABLE IF NOT EXISTS integrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER NOT NULL,
    integration_type TEXT NOT NULL,
    name TEXT NOT NULL,
    config_json TEXT CHECK (json_valid(config_json) OR config_json IS NULL),
    api_key_env_var TEXT,
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    FOREIGN KEY (integration_type) REFERENCES integration_types(type_name)
);

-- Supported integration types
CREATE TABLE IF NOT EXISTS integration_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name TEXT NOT NULL UNIQUE,
    display_name TEXT,
    config_template TEXT,
    documentation_url TEXT
);

-- Insert default integration types
INSERT OR IGNORE INTO integration_types (type_name, display_name, config_template, documentation_url) VALUES
    ('google_gmail', 'Gmail', '{"scopes": ["gmail.readonly", "gmail.send"]}', 'https://developers.google.com/gmail/api'),
    ('google_drive', 'Google Drive', '{"scopes": ["drive.readonly", "drive.file"]}', 'https://developers.google.com/drive/api'),
    ('google_sheets', 'Google Sheets', '{"scopes": ["spreadsheets"]}', 'https://developers.google.com/sheets/api'),
    ('google_appscript', 'Google Apps Script', '{"scopes": ["script.projects"]}', 'https://developers.google.com/apps-script/api'),
    ('hubspot', 'HubSpot CRM', '{"scopes": ["crm.objects.contacts.read", "crm.objects.deals.read"]}', 'https://developers.hubspot.com/docs/api'),
    ('openai', 'OpenAI', '{"model": "gpt-4"}', 'https://platform.openai.com/docs'),
    ('tavily', 'Tavily Search', '{"search_depth": "advanced"}', 'https://tavily.com/docs'),
    ('github', 'GitHub', '{"scopes": ["repo", "user"]}', 'https://docs.github.com/en/rest');

-- Workspace templates
CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    project_type TEXT CHECK (project_type IN ('general', 'web', 'data', 'api', 'automation', 'mobile', 'desktop') OR project_type IS NULL),
    rules_json TEXT CHECK (json_valid(rules_json) OR rules_json IS NULL),
    settings_json TEXT CHECK (json_valid(settings_json) OR settings_json IS NULL),
    integrations_json TEXT CHECK (json_valid(integrations_json) OR integrations_json IS NULL),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default templates
INSERT OR IGNORE INTO templates (name, description, project_type, rules_json, settings_json) VALUES
    ('web_fullstack', 'Full-stack web development', 'web', '["core", "frontend", "backend", "api"]', '{"tabSize": 2, "formatOnSave": true}'),
    ('python_data', 'Python data science', 'data', '["core", "python", "data_science"]', '{"tabSize": 4, "formatOnSave": true}'),
    ('api_backend', 'Backend API development', 'api', '["core", "backend", "api", "database"]', '{"tabSize": 2, "formatOnSave": true}'),
    ('automation', 'Automation and scripting', 'automation', '["core", "python", "automation"]', '{"tabSize": 4, "formatOnSave": true}');

-- MCP server configurations
CREATE TABLE IF NOT EXISTS mcp_servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER NOT NULL,
    server_name TEXT NOT NULL,
    server_type TEXT,
    config_json TEXT CHECK (json_valid(config_json) OR config_json IS NULL),
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

-- User preferences
CREATE TABLE IF NOT EXISTS preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default preferences
INSERT OR IGNORE INTO preferences (key, value, description) VALUES
    ('default_model', 'gpt-4', 'Default AI model for Cursor'),
    ('vim_mode', 'false', 'Enable Vim keybindings'),
    ('auto_save', 'true', 'Auto-save files'),
    ('format_on_save', 'true', 'Format code on save'),
    ('context_length', '8000', 'AI context length'),
    ('privacy_mode', 'true', 'Enable privacy mode');

-- ============================================================================
-- RUNTIME TABLES (loaded after workspace tables)
-- ============================================================================

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

-- Rule documents - stores markdown rule content from .mdc files
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

-- Agent knowledge base - facts and information the agent has learned
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

-- Agent decisions - stores reasoning and decision history
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
    FOREIGN KEY (learned_from) REFERENCES agent_decisions(id)
);

-- Agent patterns - learned patterns and heuristics
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

-- Agent state - current agent state and personality
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

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Workspace configuration indexes
CREATE INDEX IF NOT EXISTS idx_rules_workspace ON cursor_rules(workspace_id);
CREATE INDEX IF NOT EXISTS idx_cursor_rules_active ON cursor_rules(is_active);
CREATE INDEX IF NOT EXISTS idx_integrations_workspace ON integrations(workspace_id);
CREATE INDEX IF NOT EXISTS idx_integrations_type ON integrations(integration_type);
CREATE INDEX IF NOT EXISTS idx_integrations_active ON integrations(is_active);
CREATE INDEX IF NOT EXISTS idx_mcp_workspace ON mcp_servers(workspace_id);
CREATE INDEX IF NOT EXISTS idx_mcp_active ON mcp_servers(is_active);
CREATE INDEX IF NOT EXISTS idx_workspaces_project_type ON workspaces(project_type);
CREATE INDEX IF NOT EXISTS idx_preferences_key ON preferences(key);

-- Runtime table indexes
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
CREATE INDEX IF NOT EXISTS idx_rule_docs_workspace ON rule_documents(workspace_id);
CREATE INDEX IF NOT EXISTS idx_rule_docs_file ON rule_documents(rule_file);
CREATE INDEX IF NOT EXISTS idx_knowledge_workspace ON agent_knowledge(workspace_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_topic ON agent_knowledge(topic);
CREATE INDEX IF NOT EXISTS idx_knowledge_confidence ON agent_knowledge(confidence);
CREATE INDEX IF NOT EXISTS idx_decisions_workspace ON agent_decisions(workspace_id);
CREATE INDEX IF NOT EXISTS idx_decisions_type ON agent_decisions(decision_type);
CREATE INDEX IF NOT EXISTS idx_decisions_success ON agent_decisions(success);
CREATE INDEX IF NOT EXISTS idx_patterns_workspace ON agent_patterns(workspace_id);
CREATE INDEX IF NOT EXISTS idx_patterns_type ON agent_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_state_workspace ON agent_state(workspace_id);
CREATE INDEX IF NOT EXISTS idx_state_key ON agent_state(state_key);
