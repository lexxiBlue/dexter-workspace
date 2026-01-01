-- Dexter Workspace Configuration Database Schema
-- SQLite database for managing Cursor IDE workspace configurations

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

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_rules_workspace ON cursor_rules(workspace_id);
CREATE INDEX IF NOT EXISTS idx_rules_active ON cursor_rules(is_active);
CREATE INDEX IF NOT EXISTS idx_integrations_workspace ON integrations(workspace_id);
CREATE INDEX IF NOT EXISTS idx_integrations_type ON integrations(integration_type);
CREATE INDEX IF NOT EXISTS idx_integrations_active ON integrations(is_active);
CREATE INDEX IF NOT EXISTS idx_mcp_workspace ON mcp_servers(workspace_id);
CREATE INDEX IF NOT EXISTS idx_mcp_active ON mcp_servers(is_active);
CREATE INDEX IF NOT EXISTS idx_workspaces_project_type ON workspaces(project_type);
CREATE INDEX IF NOT EXISTS idx_preferences_key ON preferences(key);
