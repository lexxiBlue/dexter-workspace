# Dexter Vision & Operational Architecture

**Dexter** is a self-aware, autonomous agent manager that runs inside Cursor IDE and orchestrates hands-off task delegation and project execution.

This document encodes the vision, schema design, and operational principles so that Dexter can introspect, learn, and evolve itself.

---

## Core Mission

- **Dexter is a house for AI**: A persistent, queryable database that holds configuration, decisions, memory, errors, and recovery strategies.
- **User delegates, Dexter executes**: User says "I need X" (or "/project1_X"), and Dexter researches, analyzes, asks clarifying questions, and performs the work within its role.
- **Self-sufficient & self-healing**: Every configuration, error, and learned pattern is stored in the database. If something breaks, Dexter can diagnose, recover, and improve.
- **Hands-off for the user**: User focuses on what matters; Dexter handles the rest.

---

## Architecture Overview

### Two-Layer Database Design

#### Layer 1: Control-Plane (`dexter.sql`)

Holds Dexter's own state: sessions, errors, recovery strategies, memory, and long-term goals.

**Tables:**
- `rules` – behavioral guardrails (no_blind_delete, learn_from_errors, recover_proactively, etc.)
- `action_log` – every operation Dexter performs
- `checkpoints` – snapshots before/after destructive ops
- `context` – working memory for current session
- `agent_sessions` – each time user opens `/Handoff` or `/project#_*`
- `agent_errors` – structured errors with playbook linkage
- `agent_playbooks` – self-healing strategies (trigger → remediation)
- `agent_memories` – reflections, decisions, learned patterns
- `knowledge_items`, `search_queries` – indexed research findings
- `health_checks`, `workspace_snapshots` – self-diagnostics & recovery baselines
- `roadmap`, `roadmap_items` – long-term goals and tracking
- `vision_statements`, `architecture_decisions` – self-awareness and rationale

**Purpose:** Audit trail, error recovery, learning, and goal tracking. Dexter can query this to understand what happened, why, and what to do next.

#### Layer 2: Workspace (`schema.sql`)

Holds workspace configuration and domain data: integrations, projects, templates, preferences, and business logic.

**Tables:**
- `workspaces` – workspace identity
- `workspace_settings` – mirrored Cursor config, .cursorignore, .env, mcp.json
- `workspace_dependencies` – packages/tools to install at handoff
- `projects`, `project_runs` – scoped work with role & success criteria
- `cursor_rules`, `integrations`, `mcp_servers`, `templates`, `preferences` – Cursor configuration
- `customers`, `orders`, `integration_configs` – domain models (equipment rental example)

**Purpose:** Current config, integrations, projects, and domain data. If workspace config files are corrupted, Dexter can rehydrate from the database.

### Why Two Layers?

- **No redundancy**: dexter.sql ≠ schema.sql; they are orthogonal.
- **Clear separation of concerns**: Control-plane for Dexter's own reasoning; workspace for the "house" (user's config and domain).
- **Multi-workspace ready**: Each workspace has its own schema.sql; all workspaces share dexter.sql for audit and learning.
- **Self-aware**: Dexter can query its own logs, errors, decisions, and roadmap without mixing with user data.

---

## Operational Model

### Entry Points

#### `/Handoff`
Bootstrap the agent into the workspace.

1. Create `agent_sessions` row with `entry_command = '/Handoff'`, `status = 'running'`.
2. Read `workspace_settings`, `workspace_dependencies`, `mcp_servers`, `preferences`; validate setup.
3. Load rules from `.cursor/rules/`; confirm guardrails are understood.
4. Propose environment checks (dependencies installed? schema valid? integrations configured?).
5. Load recent `agent_memories` and `roadmap` items to remind Dexter of progress and goals.
6. Ready to accept user request.

#### `/project#_name`
Bootstrap the agent into a scoped project.

1. Look up or create `projects` row with `slug = 'projectN_name'`.
2. Create `agent_sessions` row linked to that project.
3. Read project's `role_prompt`, `scope_json`, `success_criteria_json`.
4. Load project-scoped `agent_memories` and `knowledge_items`.
5. Query `project_runs` for recent history and lessons learned.
6. Present role, scope, and success criteria to user; ready to work.

### Execution Flow

1. **Plan**: Dexter researches, analyzes, asks clarifying questions.
   - Logs searches to `search_queries` and `knowledge_items`.
   - Creates `agent_memories` with decisions and reasoning.
2. **Propose**: Dexter outlines plan and asks for confirmation (especially for destructive ops).
   - Checks `rules` for constraints (no_blind_delete, verify_after_change, etc.).
3. **Execute**: Dexter performs the work.
   - Logs each action to `action_log`.
   - Creates `checkpoints` before/after important changes.
   - On error: insert into `agent_errors`, query `agent_playbooks` for auto-remediation, execute if safe.
4. **Reflect**: After completion, Dexter writes `agent_memories` (what worked, what failed, patterns learned).
   - Updates `agent_playbooks.success_rate` if error was handled.
   - Updates `project_runs` with summary and error count.
   - Marks `agent_sessions` as completed.

### Self-Healing & Learning

When Dexter encounters an error:

1. Insert into `agent_errors` with `error_type`, `message`, `context_snapshot`.
2. Query `agent_playbooks` for matching `trigger_pattern`:
   - If found, check `preconditions` (is it safe to run?).
   - If safe, execute `remediation_steps_json` (retry, resync, check health, etc.).
   - Mark `agent_errors.handled = 1` with `resolution_notes`.
   - Update `agent_playbooks.success_count` and `success_rate`.
3. If no playbook or preconditions fail:
   - Mark `agent_errors.handled = 0`; ask user for help.
   - Store context for later playbook creation.
4. Over time, `agent_playbooks` grows and becomes more effective; Dexter becomes more autonomous.

### Proactive Health Monitoring

On `/handoff` or periodically:

1. Run all `health_checks` for the workspace (schema consistency, file integrity, dependency versions, integration connectivity).
2. If a check fails:
   - Log to `health_checks.last_status`.
   - Query linked `auto_fix_playbook_id`.
   - Execute remediation if available and safe.
3. Keep `workspace_snapshots` for known-good baselines; use them in recovery.

---

## Roadmap & Goals

Stored in `roadmap` and `roadmap_items` tables:

### Phase 1: Foundation (Current)

- [x] Core schema: `dexter.sql` (rules, sessions, errors, memory, goals)
- [x] Workspace config: `schema.sql` (settings, dependencies, projects)
- [ ] Agent sessions & error tracking with recovery
- [ ] Playbooks and basic self-healing
- [ ] Health checks and snapshot recovery
- [ ] Vision & architecture record

**Success**: Dexter logs every session and error; can recover from at least one error class; can query its own roadmap.

### Phase 2: Projects & Autonomy

- Implement `/project#_*` commands with role-prompt binding.
- Project-scoped memories and success criteria.
- Advanced scope negotiation (user describes goal, Dexter asks clarifying questions).

**Success**: User can delegate entire projects; Dexter executes within scope; user reviews results.

### Phase 3: MCP Crawling & Knowledge Base

- Integrate crawling MCP for indexing research, GitHub docs, internal files.
- `knowledge_items` table for internal knowledge base.
- Dexter reuses research across sessions instead of re-querying.

**Success**: Dexter builds an internal wiki; future tasks benefit from past research.

### Phase 4: Advanced Playbooks & Optimization

- Expand playbook library (not just error recovery, but optimization).
- Proactive health monitoring and auto-remediation.
- Multi-step recovery strategies.

**Success**: Dexter prevents failures, not just recovers from them.

### Phase 5: Multi-workspace & Scaling

- Support multiple concurrent workspaces.
- Shared playbooks and cross-workspace learning.
- Team-level logging and audit.

**Success**: Dexter scales to multiple users and projects.

---

## Design Principles

### 1. Everything in the Database

No configuration lives only in the filesystem. Mirror everything:
- Cursor settings → `workspace_settings`
- Dependencies → `workspace_dependencies`
- MCP config → `mcp_servers`, `workspace_settings`
- Errors → `agent_errors` (not just logs)
- Memories → `agent_memories` (not just conversation history)

**Why**: Total control and recovery. If files are corrupted, Dexter can rehydrate.

### 2. Parse Efficient & Non-Redundant

- Two separate schema files: control-plane and workspace.
- Clear foreign key relationships; no duplication.
- Every table has a single, clear purpose.
- Indexes on frequently queried columns.

**Why**: Fast queries, easy to reason about, no conflicting state.

### 3. Queryable Self-Awareness

Dexter can introspect its own state:

```sql
-- What errors has Dexter encountered?
SELECT error_type, COUNT(*) FROM agent_errors GROUP BY error_type;

-- Which playbooks are most effective?
SELECT key, success_rate FROM agent_playbooks ORDER BY success_rate DESC;

-- What has Dexter learned about this project?
SELECT category, content FROM agent_memories WHERE project_id = 1;

-- Are we on track with the roadmap?
SELECT title, status FROM roadmap_items WHERE roadmap_id = 1;

-- What might cause issues in recovery?
SELECT name, last_status FROM health_checks WHERE last_status IN ('warn', 'fail');
```

**Why**: Dexter makes better decisions by understanding its own history and constraints.

### 4. Safe Autonomy

Guardrails are rules, not just prompts:

- `no_blind_delete` → must create checkpoint, confirm with user
- `log_all_actions` → every action inserted into `action_log` before execution
- `learn_from_errors` → playbooks updated on successful recovery
- `recover_proactively` → health checks trigger playbooks

**Why**: Autonomy without risk. User always has audit trail and can override.

### 5. Persistence & Recovery

If Dexter crashes or the workspace breaks:

1. Restart and run `/handoff`.
2. Query `agent_sessions` to resume context.
3. Check `health_checks` and run recovery playbooks.
4. Rehydrate workspace config from `workspace_settings`.
5. Continue where you left off.

**Why**: Resilient, hands-off operation.

---

## Example Workflows

### Workflow 1: Error Recovery

**Scenario**: Dexter tries to create a table but gets `sqlite3.OperationalError: database is locked`.

1. Log error to `agent_errors` with `error_type = 'sqlite.OperationalError'`, `message = 'database is locked'`.
2. Query `agent_playbooks` where `trigger_pattern ~ 'database is locked'`.
3. Find playbook: "migration_sqlite_locked"
   - Preconditions: check if another process is using DB (query `lsof`)
   - Remediation: wait 2 seconds, retry with pragma busy_timeout = 5000, then retry migration
4. Execute remediation; migration succeeds.
5. Mark `agent_errors.handled = 1`; update playbook `success_count` and `success_rate`.
6. Write `agent_memory` category='pattern' content='SQLite locks are transient; retry with backoff works 95% of time'.

### Workflow 2: Project Delegation

**Scenario**: User types `/project1_automation-suite`.

1. Create `agent_sessions` row with `entry_command = '/project1_automation-suite'`, `project_id = 1`.
2. Query `projects` where `slug = 'project1_automation-suite'`.
3. Load `role_prompt`: "You are the automation engine. Focus on workflow orchestration, error handling, and reporting."
4. Load `scope_json`: "Features: scheduled tasks, error alerts, retry logic. Constraints: no manual intervention, all changes logged."
5. Load `success_criteria_json`: "All tasks execute on schedule; errors detected <1min; 99.9% uptime."
6. Load recent `agent_memories`: "Last run: 3 failed tasks due to API timeout; implemented backoff strategy."
7. Dexter: "I'm ready. Here's the plan: [3-step plan]. Any adjustments?"
8. User: "Go ahead."
9. Dexter executes, logs to `action_log`, writes final `agent_memory`.

### Workflow 3: Self-Healing on Startup

**Scenario**: User opens Cursor after a crash and runs `/handoff`.

1. Create `agent_sessions` row.
2. Run health checks:
   - Schema: missing `customers` table? → Found playbook "create_missing_table_customers"; execute.
   - Dependencies: ruff version outdated? → Update dependency in `workspace_dependencies`; suggest `pip install --upgrade`.
   - MCP: GitHub token invalid? → Flag in `health_checks`; ask user to refresh.
3. Propose: "Workspace recovered. 1 dependency updated, MCP token needs refresh."
4. User: "Update dep; I'll refresh token later."
5. Dexter: "Ready to work."

---

## Future Extensions

### Crawling MCP Integration

When crawling MCP is added:

1. `/project1_research-best-practices` → Dexter queries `search_queries` and `knowledge_items` first.
2. If results are stale, invoke crawling MCP to index new docs.
3. Write results to `knowledge_items` with `source_type = 'mcp_crawl'`.
4. Link to `search_queries` for audit.
5. Future runs reuse indexed results.

### Team & Workspace Sharing

When multi-workspace is added:

1. `agent_playbooks` can be workspace-scoped or global (shared).
2. `agent_memories` can be personal or project-wide.
3. `action_log` aggregated for team audit.

### Optimization & Proactive Monitoring

As Dexter matures:

1. Playbooks expand to include optimization (not just recovery).
2. Health checks run continuously, not just on startup.
3. `roadmap_items` auto-update as Dexter achieves milestones.
4. `agent_memories` inform future project planning.

---

## Getting Started

### Setup

1. Clone the repo.
2. `sqlite3 dexter.db < dexter.sql` – initialize control-plane.
3. `sqlite3 dexter.db < schema.sql` – initialize workspace.
4. Populate `.env` with your settings and API keys.
5. Open in Cursor.

### First Run

1. Type `/handoff`.
2. Dexter loads schema, rules, and dependencies; proposes a plan.
3. Delegate your first task or create a project.
4. Watch Dexter log actions, handle errors, and learn.

### Monitoring

Query the database to understand what Dexter has done:

```bash
# Recent sessions
sqlite3 dexter.db "SELECT id, entry_command, status, action_count, error_count FROM agent_sessions ORDER BY id DESC LIMIT 5;"

# Playbook effectiveness
sqlite3 dexter.db "SELECT key, success_count, failure_count, success_rate FROM agent_playbooks ORDER BY success_rate DESC;"

# Roadmap status
sqlite3 dexter.db "SELECT title, status FROM roadmap_items;"
```

---

## Summary

Dexter is a **self-aware house for AI**. Every decision, error, and learned pattern is stored in the database. When you delegate work, Dexter researches, analyzes, executes, recovers from failures, and improves. You focus on what matters; Dexter handles the rest.

The schema is the blueprint. The prompts are the personality. The actions are the proof.
