-- Dexter Workspace Configuration Database Schema
-- SQLite database for managing Cursor IDE workspace configurations and domain data
-- This is the "house" layer: config, integrations, projects, and domain models

-- =============================================================================
-- WORKSPACE CORE
-- =============================================================================

-- Workspace configurations table
CREATE TABLE IF NOT EXISTS workspaces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    project_type TEXT DEFAULT 'general',
    status TEXT DEFAULT 'active',  -- 'active', 'paused', 'archived'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workspace settings - mirror of Cursor config, .cursorignore, .env, mcp.json, etc.
CREATE TABLE IF NOT EXISTS workspace_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    source TEXT,                   -- 'cursor_settings', 'mcp.json', '.cursorignore', '.env', etc.
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (workspace_id, key, source),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

-- Workspace dependencies - packages, tools, CLI requirements
CREATE TABLE IF NOT EXISTS workspace_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER NOT NULL,
    name TEXT NOT NULL,            -- 'ruff', 'pytest', 'mypy', 'requests', etc.
    version_spec TEXT,             -- '>=0.4,<0.5' or '==1.2.3'
    install_command TEXT,          -- 'pip install', 'npm install', 'brew install', etc.
    package_manager TEXT,          -- 'pip', 'npm', 'cargo', 'brew', etc.
    required INTEGER DEFAULT 1,    -- 1 = hard requirement, 0 = optional
    installed INTEGER DEFAULT 0,   -- 1 = already installed, 0 = pending
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (workspace_id, name),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

-- =============================================================================
-- CURSOR CONFIGURATION STORAGE
-- =============================================================================

-- Cursor rules storage
CREATE TABLE IF NOT EXISTS cursor_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER,
    rule_name TEXT NOT NULL,
    description TEXT,
    globs TEXT,
    rule_type TEXT DEFAULT 'always',
    content TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

-- Integration configurations
CREATE TABLE IF NOT EXISTS integrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER,
    integration_type TEXT NOT NULL,
    name TEXT NOT NULL,
    config_json TEXT,
    api_key_env_var TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
    FOREIGN KEY (integration_type) REFERENCES integration_types(type_name)
);

-- Supported integration types (reference table)
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
    project_type TEXT,
    rules_json TEXT,
    settings_json TEXT,
    integrations_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    workspace_id INTEGER,
    server_name TEXT NOT NULL,
    server_type TEXT,
    config_json TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

-- User preferences - global or workspace-scoped
CREATE TABLE IF NOT EXISTS preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER,          -- NULL = global, otherwise workspace-scoped
    key TEXT NOT NULL,
    value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (workspace_id, key),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

-- Insert default global preferences
INSERT OR IGNORE INTO preferences (workspace_id, key, value, description) VALUES
    (NULL, 'default_model', 'gpt-4', 'Default AI model for Cursor'),
    (NULL, 'vim_mode', 'false', 'Enable Vim keybindings'),
    (NULL, 'auto_save', 'true', 'Auto-save files'),
    (NULL, 'format_on_save', 'true', 'Format code on save'),
    (NULL, 'context_length', '8000', 'AI context length'),
    (NULL, 'privacy_mode', 'true', 'Enable privacy mode');

-- =============================================================================
-- PROJECTS (scoped autonomy & role-based work)
-- =============================================================================

-- Projects - discrete scopes of work with defined roles and success criteria
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER NOT NULL,
    slug TEXT NOT NULL UNIQUE,         -- 'project1_automation-suite', 'proj2_datamodeling'
    name TEXT NOT NULL,
    status TEXT DEFAULT 'active',      -- 'active', 'paused', 'completed', 'archived'
    role_prompt TEXT,                  -- How Dexter should behave for this project
    scope_json TEXT,                   -- Structured scope of work (features, constraints, endpoints)
    success_criteria_json TEXT,        -- How to judge done/success
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

-- Project runs - execution history per project
CREATE TABLE IF NOT EXISTS project_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    agent_session_id INTEGER,
    status TEXT DEFAULT 'running',     -- 'running', 'completed', 'failed', 'paused'
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    summary TEXT,
    error_count INTEGER DEFAULT 0,
    action_count INTEGER DEFAULT 0,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- =============================================================================
-- DOMAIN TABLES: Equipment Rental & Procurement System
-- =============================================================================

-- Customers: External actors (businesses, individuals) ordering equipment
CREATE TABLE IF NOT EXISTS customers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    company TEXT,
    integration_type TEXT,
    integration_id TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders: Equipment rental requests from customers
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    equipment_type TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    total_price REAL NOT NULL,
    status TEXT DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

-- Integration configurations: Credentials and settings for external service sync
CREATE TABLE IF NOT EXISTS integration_configs (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    integration_type TEXT NOT NULL,
    api_key TEXT NOT NULL,
    api_base_url TEXT,
    sync_status TEXT DEFAULT 'active',
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    UNIQUE (customer_id, integration_type)
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_workspace_settings_workspace ON workspace_settings(workspace_id);
CREATE INDEX IF NOT EXISTS idx_workspace_dependencies_workspace ON workspace_dependencies(workspace_id);
CREATE INDEX IF NOT EXISTS idx_rules_workspace ON cursor_rules(workspace_id);
CREATE INDEX IF NOT EXISTS idx_integrations_workspace ON integrations(workspace_id);
CREATE INDEX IF NOT EXISTS idx_mcp_workspace ON mcp_servers(workspace_id);
CREATE INDEX IF NOT EXISTS idx_projects_workspace ON projects(workspace_id);
CREATE INDEX IF NOT EXISTS idx_project_runs_project ON project_runs(project_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_integration_configs_customer ON integration_configs(customer_id);
CREATE INDEX IF NOT EXISTS idx_preferences_workspace ON preferences(workspace_id);
