-- Dexter Workspace Control-Plane Database Schema
-- Complete audit trail, error handling, memory, and self-healing for autonomous AI agent
-- This is the "brain" of the Dexter IDE house: logs, rules, sessions, patterns, and recovery

-- =============================================================================
-- CORE RULES & DOMAINS (audit/control)
-- =============================================================================

-- Rules - behavioral guardrails enforced across all sessions
CREATE TABLE IF NOT EXISTS rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name TEXT NOT NULL UNIQUE,
    category TEXT,
    priority INTEGER DEFAULT 5,
    condition TEXT,
    action TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Domains - organized work areas within workspace
CREATE TABLE IF NOT EXISTS domains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    path TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- =============================================================================
-- ACTION LOG & CHECKPOINTS (audit trail)
-- =============================================================================

-- Action log - every significant operation Dexter performs
CREATE TABLE IF NOT EXISTS action_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_session_id INTEGER,
    project_id INTEGER,
    timestamp TEXT DEFAULT (datetime('now')),
    action_type TEXT NOT NULL,      -- 'db_write', 'file_create', 'api_call', 'error_recovery', etc.
    target TEXT,                    -- table, file path, URL, etc.
    description TEXT,
    status TEXT DEFAULT 'completed',-- 'completed', 'failed', 'rolled_back'
    rollback_info TEXT,
    FOREIGN KEY (agent_session_id) REFERENCES agent_sessions(id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Checkpoints - verification snapshots before/after destructive ops
CREATE TABLE IF NOT EXISTS checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_id INTEGER,
    checkpoint_type TEXT NOT NULL,  -- 'pre', 'post', 'rollback'
    state_snapshot TEXT,            -- JSON of DB state, file checksums, etc.
    verified INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (action_id) REFERENCES action_log(id)
);

-- Context - working memory for current session/task
CREATE TABLE IF NOT EXISTS context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_session_id INTEGER,
    key TEXT NOT NULL,
    value TEXT,
    expires_at TEXT,
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE (agent_session_id, key),
    FOREIGN KEY (agent_session_id) REFERENCES agent_sessions(id)
);

-- =============================================================================
-- SESSIONS & ERROR HANDLING (self-awareness & healing)
-- =============================================================================

-- Agent sessions - every time a user opens /Handoff or /project#_*
CREATE TABLE IF NOT EXISTS agent_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    workspace_id INTEGER,
    entry_command TEXT NOT NULL,    -- '/Handoff', '/project1_name', etc.
    user_prompt TEXT,
    model TEXT,
    status TEXT DEFAULT 'running',  -- 'running', 'completed', 'failed', 'paused'
    started_at TEXT DEFAULT (datetime('now')),
    ended_at TEXT,
    summary TEXT,
    session_notes TEXT,
    action_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

-- Structured error log with self-healing linkage
CREATE TABLE IF NOT EXISTS agent_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_session_id INTEGER NOT NULL,
    action_id INTEGER,
    error_type TEXT NOT NULL,       -- 'sqlite.OperationalError', 'HTTPError', 'SchemaError', etc.
    message TEXT NOT NULL,
    context_snapshot TEXT,          -- JSON of state when error occurred
    retryable INTEGER DEFAULT 0,
    handled INTEGER DEFAULT 0,
    playbook_id INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    resolved_at TEXT,
    resolution_notes TEXT,
    FOREIGN KEY (agent_session_id) REFERENCES agent_sessions(id),
    FOREIGN KEY (action_id) REFERENCES action_log(id),
    FOREIGN KEY (playbook_id) REFERENCES agent_playbooks(id)
);

-- =============================================================================
-- PLAYBOOKS (learned patterns & self-healing strategies)
-- =============================================================================

-- Playbooks - self-healing strategies triggered by error patterns
CREATE TABLE IF NOT EXISTS agent_playbooks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,       -- 'migration_sqlite_locked', 'schema_mismatch_customers', etc.
    category TEXT,                  -- 'recovery', 'optimization', 'validation'
    trigger_pattern TEXT NOT NULL,  -- regex or pattern string
    detection_query TEXT,           -- SQL to detect the situation
    remediation_steps_json TEXT NOT NULL, -- ordered JSON steps
    preconditions_json TEXT,        -- safety checks before execution
    postconditions_json TEXT,       -- verification after execution
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0.0,
    last_used_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- =============================================================================
-- MEMORY & LEARNING (project-scoped reflections & patterns)
-- =============================================================================

-- Agent memories - reflections, decisions, learned patterns
CREATE TABLE IF NOT EXISTS agent_memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    workspace_id INTEGER,
    agent_session_id INTEGER,
    category TEXT NOT NULL,        -- 'reflection', 'decision', 'pattern', 'constraint', 'optimization'
    title TEXT NOT NULL,
    content TEXT NOT NULL,         -- short, human-readable insight
    metadata_json TEXT,            -- tags, related IDs, timestamps
    importance INTEGER DEFAULT 1,  -- 1-5 scale
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
    FOREIGN KEY (agent_session_id) REFERENCES agent_sessions(id)
);

-- =============================================================================
-- KNOWLEDGE BASE (search results, web crawls, indexed content)
-- =============================================================================

-- Knowledge items - collected from web, MCP crawls, files
CREATE TABLE IF NOT EXISTS knowledge_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    workspace_id INTEGER,
    source_type TEXT NOT NULL,      -- 'web', 'mcp_github', 'mcp_file', 'internal_file'
    source_id TEXT,                 -- URL, MCP path, file path
    title TEXT,
    snippet TEXT,
    content_hash TEXT,              -- for deduplication
    metadata_json TEXT,             -- domain, tags, relevance, etc.
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

-- Search queries log - track what Dexter has researched
CREATE TABLE IF NOT EXISTS search_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    agent_session_id INTEGER,
    query TEXT NOT NULL,
    provider TEXT,                  -- 'search_web', 'crawl_mcp', 'internal'
    result_count INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (agent_session_id) REFERENCES agent_sessions(id)
);

-- =============================================================================
-- HEALTH & RECOVERY (self-diagnostics)
-- =============================================================================

-- Health checks - periodic diagnostics for self-healing
CREATE TABLE IF NOT EXISTS health_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER,
    project_id INTEGER,
    name TEXT NOT NULL,
    target_type TEXT NOT NULL,      -- 'db_schema', 'file_integrity', 'integration_config', 'dependency'
    check_query_or_script TEXT NOT NULL,
    auto_fix_playbook_id INTEGER,
    last_run_at TEXT,
    last_status TEXT,               -- 'ok', 'warn', 'fail'
    last_message TEXT,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (auto_fix_playbook_id) REFERENCES agent_playbooks(id)
);

-- Workspace snapshots - recovery baselines
CREATE TABLE IF NOT EXISTS workspace_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER NOT NULL,
    snapshot_type TEXT NOT NULL,    -- 'schema', 'config', 'dependencies', 'rules'
    label TEXT,
    content TEXT NOT NULL,          -- schema dump, JSON config, etc.
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

-- =============================================================================
-- ROADMAP & VISION (long-term planning, self-aware evolution)
-- =============================================================================

-- Dexter's roadmap - encodes the long-term vision and goals
CREATE TABLE IF NOT EXISTS roadmap (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phase INTEGER NOT NULL,         -- 1 (current), 2 (next), 3+ (future)
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'planned',  -- 'planned', 'in_progress', 'completed', 'blocked'
    motivation TEXT,                -- why this phase matters
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Roadmap items - discrete goals/features tied to phases
CREATE TABLE IF NOT EXISTS roadmap_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roadmap_id INTEGER NOT NULL,
    sequence INTEGER,               -- order within phase
    title TEXT NOT NULL,
    description TEXT,
    acceptance_criteria TEXT,       -- how to know when done
    status TEXT DEFAULT 'planned',  -- 'planned', 'active', 'completed', 'blocked'
    estimated_effort TEXT,          -- 'small', 'medium', 'large'
    dependencies_json TEXT,         -- JSON array of prerequisite item IDs
    related_playbooks_json TEXT,    -- JSON array of playbook IDs to enable
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (roadmap_id) REFERENCES roadmap(id)
);

-- Vision statements - Dexter's understanding of its purpose
CREATE TABLE IF NOT EXISTS vision_statements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,         -- 'core_mission', 'user_goals', 'technical_ideals', 'constraints'
    statement TEXT NOT NULL,        -- short, clear articulation
    rationale TEXT,                 -- why this matters
    linked_roadmap_items_json TEXT, -- JSON array of roadmap_items IDs
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Architecture decisions - capture why choices were made
CREATE TABLE IF NOT EXISTS architecture_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_date TEXT,
    title TEXT NOT NULL,
    context TEXT NOT NULL,          -- what problem did this solve?
    decision TEXT NOT NULL,         -- what we decided
    rationale TEXT NOT NULL,        -- why this is the best choice
    alternatives_considered TEXT,   -- JSON of rejected options
    trade_offs TEXT,                -- what we gave up
    status TEXT DEFAULT 'accepted', -- 'proposed', 'accepted', 'deprecated', 'superseded'
    superseded_by INTEGER,          -- ID of new decision if deprecated
    created_at TEXT DEFAULT (datetime('now'))
);

-- =============================================================================
-- DEFAULTS: INITIAL GUARDRAILS, DOMAINS, VISION, ROADMAP
-- =============================================================================

-- Default behavioral rules
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

-- Default domains
INSERT OR IGNORE INTO domains (name, description, path) VALUES
    ('hubspot', 'HubSpot CRM integration and automation', 'domains/hubspot'),
    ('google', 'Google Workspace (Gmail, Drive, Sheets, Apps Script)', 'domains/google'),
    ('automation', 'General automation scripts and workflows', 'domains/automation'),
    ('projects', 'Active project workspaces', 'domains/projects');

-- Core vision statements
INSERT OR IGNORE INTO vision_statements (category, statement, rationale) VALUES
    ('core_mission', 'Dexter is a self-aware, autonomous agent manager for hands-off task delegation and project execution', 'Clear identity and purpose'),
    ('core_mission', 'Every configuration, decision, memory, and error is queryable and persistable in the database', 'Total self-awareness and recovery capability'),
    ('user_goals', 'User delegates projects with scope, criteria, and role; Dexter handles research, planning, execution, and self-healing', 'Hands-off sufficiency'),
    ('user_goals', 'Dexter learns from every error and successful recovery to improve future autonomy', 'Continuous learning and improvement'),
    ('technical_ideals', 'Parse-efficient, non-redundant schema; every table has a clear purpose and foreign key relationships', 'Clean, maintainable architecture'),
    ('technical_ideals', 'All external config (Cursor settings, MCP, dependencies) is mirrored in the database for disaster recovery', 'Total control and reproducibility'),
    ('constraints', 'Dexter must always operate within guardrails defined in rules and project role_prompts', 'Safe autonomy'),
    ('constraints', 'Dexter asks for confirmation on destructive operations, schema changes, and external side effects', 'User remains in control');

-- Roadmap phases
INSERT OR IGNORE INTO roadmap (phase, title, description, status) VALUES
    (1, 'Foundation: Core schema & self-awareness', 'Build dexter.sql and schema.sql with session tracking, error handling, memory, and health checks', 'in_progress'),
    (2, 'Projects & Role-based Autonomy', 'Implement /project#_* commands, project-scoped roles, and scope-of-work binding', 'planned'),
    (3, 'MCP Crawling & Knowledge Base', 'Integrate crawling MCP for indexing research findings, building internal knowledge base', 'planned'),
    (4, 'Advanced Playbooks & Self-Optimization', 'Expand playbook library with optimization strategies, proactive health monitoring, and auto-remediation', 'planned'),
    (5, 'Multi-workspace & Team Scaling', 'Support multiple concurrent workspaces, shared playbooks, and team-level logging', 'planned');

-- Phase 1 items
INSERT OR IGNORE INTO roadmap_items (roadmap_id, sequence, title, description, acceptance_criteria, status) VALUES
    (1, 1, 'Agent sessions & error tracking', 'Full agent_sessions, agent_errors, and action_log with proper foreign keys', 'Dexter logs every session and error with context', 'in_progress'),
    (1, 2, 'Memory & reflections', 'agent_memories table allowing Dexter to record insights after each task', 'Dexter writes 1-3 memories per completed project', 'in_progress'),
    (1, 3, 'Playbooks & error recovery', 'agent_playbooks with remediation steps; errors trigger playbook lookup and execution', 'Dexter successfully recovers from at least 1 class of error', 'in_progress'),
    (1, 4, 'Health checks & snapshots', 'health_checks table with periodic diagnostics; workspace_snapshots for recovery baselines', 'Dexter can validate schema consistency and propose fixes', 'planned'),
    (1, 5, 'Vision & architecture records', 'roadmap, vision_statements, architecture_decisions tables for self-aware goal tracking', 'Dexter can query its own roadmap and explain design decisions', 'planned');

-- Core architecture decisions
INSERT OR IGNORE INTO architecture_decisions (decision_date, title, context, decision, rationale) VALUES
    ('2026-01-02', 'Separate control-plane (dexter.sql) from workspace (schema.sql)', 'Need clear separation between audit/rules/sessions (always) and workspace config/domain data (per workspace)', 'Two schema files: dexter.sql holds session/error/memory/rules; schema.sql holds workspaces/integrations/domain tables', 'Allows Dexter to reason about its own logs and errors without mixing with user data; enables multi-workspace support'),
    ('2026-01-02', 'All external config mirrored in database', 'Want total recovery capability if files are corrupted or lost; need reliable source of truth', 'workspace_settings table stores normalized Cursor config, .env vars, MCP settings; snapshot tables for baselines', 'Single DB query can rehydrate entire workspace; enables disaster recovery without relying on filesystem'),
    ('2026-01-02', 'Errors as first-class control-plane objects', 'Want Dexter to learn from and autonomously resolve errors', 'agent_errors table linked to agent_playbooks; on error, query playbooks and auto-execute remediation if safe', 'Errors become observable, queryable events; playbooks capture institutional knowledge about failure modes'),
    ('2026-01-02', 'Playbooks capture self-healing strategies', 'Need Dexter to handle common failures without user intervention', 'agent_playbooks table with trigger_pattern, detection_query, remediation_steps, success_rate metrics', 'Playbooks grow over time; success_rate tracks effectiveness; Dexter can prioritize high-confidence fixes'),
    ('2026-01-02', 'Roadmap & vision in database', 'Want Dexter to understand and track long-term goals; enable self-directed improvement', 'roadmap, roadmap_items, vision_statements, architecture_decisions tables', 'Dexter can query its own purpose, roadmap status, and architectural constraints; introspection enables self-aware decision-making');
