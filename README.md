# Dexter Workspace

**AI-first Cursor IDE framework with strong guardrails, MCP integration, and a single SQLite source of truth.**

Dexter is a structured workspace for running autonomous or semi-autonomous agents inside Cursor IDE against a well-defined SQLite schema, Python helper layer, and domain-specific integrations.

---

## Overview

Dexter focuses on four things:

- **Single source of truth**: `dexter.sql` and `schema.sql` define all persistent state (control-plane and workspace domains).
- **Guardrailed autonomy**: Agents can work freely for non-destructive tasks; state changes and schema edits are tightly controlled.
- **First-class Cursor support**: `.cursor/` contains rules, MCP config, custom commands, and ignore files aligned with Cursor 0.46+.
- **Auditability and structure**: All meaningful actions flow through helpers and are designed to be logged and inspected.

---

## Architecture

### Mental model

```text
Agent request
   ↓
Dexter rules (.cursor/rules/*.mdc)
   ↓
Helpers (db_helper, integration_clients, workspace_generator)
   ↓
SQLite schema (dexter.sql + schema.sql)
   ↓
Domain data (customers, orders, integration_configs, …)
```

### Repository layout

```text
dexter-workspace/
├── .cursor/                  # Cursor rules, MCP config, commands, docs
│   ├── rules/                # Agent behavior + domain rules (.mdc / .md)
│   ├── commands.json         # /Handoff and other custom commands
│   ├── cursor-config.md      # Detailed Cursor 0.46+ configuration
│   ├── README.md             # Agent quickstart
│   └── SETUP.md              # Team onboarding for Cursor
├── .github/
│   └── workflows/            # CI/CD (lint, test, build)
├── domains/                  # Domain-specific integrations
│   ├── automation/           # Internal orchestration
│   ├── google/               # Google Workspace
│   ├── hubspot/              # HubSpot CRM
│   └── projects/             # Project-scoped helpers
├── helpers/
│   ├── db_helper.py          # Database access + guardrails
│   ├── integration_clients.py# External system abstraction
│   └── workspace_generator.py# Meta-tooling / scaffolding
├── tests/                    # Smoke tests + fixtures
├── dexter.sql                # Core/control schema
├── schema.sql                # Workspace + domain schema (customers, orders, etc.)
├── dexter.db                 # Runtime SQLite database (dev/local only)
├── .env.template             # Environment configuration template
└── README.md                 # This file
```

### Key data layers

- **Control-plane schema (`dexter.sql`)**  
  Core tables for workflows, automation logs, control rules, context registry, automation state, session cache, and audit log.

- **Workspace + domain schema (`schema.sql`)**  
  Tables for workspaces, branches, merge/pull requests, reviews, commits, issues, discussions, plus domain tables such as `customers`, `orders`, and `integration_configs`.

- **Helper layer (`helpers/`)**  
  All DB writes and external calls flow through well-defined helpers:
  - `db_helper.py`: parameterized SQL only, centralizes DB access and migrations.
  - `integration_clients.py`: wraps external services (Google, HubSpot, etc.).
  - `workspace_generator.py`: scaffolding and workspace automation.

---

## Getting started

### Prerequisites

- Python 3.9+
- SQLite 3
- Git
- Cursor IDE (or VS Code with Cursor extension) for AI-driven workflows

### Local setup

```bash
# 1. Clone the repository
git clone https://github.com/lexxiBlue/dexter-workspace.git
cd dexter-workspace

# 2. Create environment file from template
cp .env.template .env
# Populate .env with your settings (API keys, DB path, etc.)

# 3. Initialize the database
sqlite3 dexter.db < dexter.sql
sqlite3 dexter.db < schema.sql

# 4. (Optional) Create and activate a virtualenv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

# 5. Install Python dependencies
pip install -r requirements.txt

# 6. Open in Cursor
cursor .
```

### Sanity checks

```bash
# Check tables exist
sqlite3 dexter.db "SELECT name FROM sqlite_master WHERE type='table';"

# Verify helpers import
python -c "from helpers.db_helper import *; print('✓ db_helper loaded')"
python -c "from helpers.integration_clients import *; print('✓ integration_clients loaded')"
```

---

## Using Dexter in Cursor

Dexter is designed to be driven primarily through Cursor with a structured bootstrap flow.

### 1. Run the `/Handoff` command

In Cursor, with this repository open:

1. Open the chat panel.
2. Type `/Handoff` and send.
3. Wait for the agent to:
   - Inspect the repository layout.
   - Load schemas from `dexter.sql` and `schema.sql`.
   - Read core rules from `.cursor/rules/` (`core.mdc`, `database.mdc`, `dexter.mdc`).
   - Skim supporting rules (`python.mdc`, `automation.mdc`, `integrations.mdc`, `dexter-context.md`, `project-rules.md`, `common-pitfalls.md`).
   - Inspect helper modules (`helpers/db_helper.py`, `helpers/integration_clients.py`, `helpers/workspace_generator.py`).
   - Check for `.cursor/mcp.json` to determine MCP GitHub/filesystem availability.

The agent’s first reply after `/Handoff` is expected to:

- Summarize key schema tables and their purpose.
- List the main helpers and what they do.
- Confirm which rules were loaded from `.cursor/rules/`.
- State whether MCP GitHub/filesystem tools are configured.
- Present a short, numbered plan for your requested task.

### 2. Day-to-day agent usage

- Use natural language to describe automation, data, or integration tasks.
- Let Dexter propose a plan (tests, code changes, migrations, PR flow).
- Confirm any destructive operation before it is executed (schema changes, mass updates, external side effects).

For detailed Cursor/MCP behavior, see [`.cursor/cursor-config.md`](./.cursor/cursor-config.md).

---

## Cursor & MCP configuration

Dexter ships a complete Cursor 0.46+ configuration, aligned with current documentation.

### Core files

- **`.cursor/mcp.json`** – Official MCP config:  
  - `github` server: issues, PRs, repo search (uses `GITHUB_TOKEN`).  
  - `filesystem` server: file reads, directory listing, search (uses `ALLOWED_DIRECTORIES`).

- **`.cursor/rules/`** – Behavior and domain rules:  
  - Core rules: `core.mdc`, `database.mdc`, `dexter.mdc`.  
  - Context rules: `python.mdc`, `automation.mdc`, `integrations.mdc`.  
  - Reference/context: `common-pitfalls.md`, `dexter-context.md`, `project-rules.md`, `github-integration.md`, `handoff.md`.

- **`.cursor/commands.json`** – Custom commands:  
  - `/Handoff`: standardized bootstrap for new sessions (see above).

- **`.cursor/cursor-config.md`** – In-depth explanation of all of the above, including legacy vs. current patterns.

### Ignore & indexing behavior

- **`.cursorignore`** – Best-effort AI and context block list:
  - Secrets: `.env`, `.env.*`, `*.key`, `secrets/`, `.aws/`, `.kube/`.
  - Dependencies: `node_modules/`, `.venv/`, `__pycache__/`, `*.egg-info/`.
  - Build artifacts, logs, large binaries and databases.

- **`.cursorindexingignore`** – Indexing-only control:
  - Test fixtures: `tests/fixtures/`, `__mocks__/`.
  - Compiled/codegen files: `*.pyc`, `*.class`, `*.o`.
  - Cache dirs: `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`.

The combination keeps Cursor’s index tight and fast while protecting secrets and noisy artifacts from being pulled into AI context.

---

## Safety & guardrails

Dexter is designed to be safe-by-default for AI agents:

- **Parameterized SQL only**: Helpers enforce `?` placeholders; no string-concatenated SQL.
- **Controlled schema evolution**: Agents must propose a migration plan and get explicit approval before schema changes.
- **No table/column invention**: Agents must rely on `dexter.sql`, `schema.sql`, and `dexter-context.md` as the source of truth.
- **Secret handling**: API keys and credentials live in `.env` and environment variables, never hard-coded or logged.
- **Scoped autonomy**: Read/analysis is autonomous; writes and external side effects require confirmation.
- **Auditability**: The schema is structured so that important actions can be logged and later inspected.

---

## Development workflow

### Database changes

1. Update `dexter.sql` and/or `schema.sql` to reflect the new canonical schema.
2. Apply locally to a fresh dev DB:

   ```bash
   rm -f dexter.db
   sqlite3 dexter.db < dexter.sql
   sqlite3 dexter.db < schema.sql
   ```

3. Run smoke tests under `tests/`.
4. Commit schema + tests together.

### Coding & testing

```bash
# Lint
ruff check helpers/ domains/

# Run tests
pytest tests/
```

When making non-trivial changes, prefer:

- Adding/updating tests in `tests/`.
- Letting Dexter propose tests when using Cursor.
- Running CI locally before pushing if possible.

### Git & PR flow

- Prefer feature branches over direct commits to `main`.
- When MCP GitHub tools are available in Cursor, let the agent:
  - Create branches.  
  - Open pull requests.  
  - Add context from issues and existing PRs.

---

## Troubleshooting

**Database looks wrong**

```bash
# Rebuild dev DB from canonical schema
rm -f dexter.db
sqlite3 dexter.db < dexter.sql
sqlite3 dexter.db < schema.sql
```

**Agent ignores rules or schema**

- Confirm Cursor is opened at the repo root.  
- Check `.cursor/rules/` files exist and are valid.  
- Rerun `/Handoff` to re-bootstrap the session.  
- If still inconsistent, restart Cursor and try again.

**MCP GitHub/filesystem not available**

- Ensure `.cursor/mcp.json` is present and valid JSON.
- Set `GITHUB_TOKEN` and any other required environment variables.
- Restart Cursor so MCP servers are re-discovered.

For more in-depth operational notes, see `.cursor/SETUP.md` and `.cursor/cursor-config.md`.

---

## Roadmap

- Expand domain implementations (Google, HubSpot, internal automation).
- Harden migration tooling and schema versioning.
- Broaden test coverage across helpers and domains.
- Add production deployment and backup patterns.
- Improve multi-workspace orchestration support.

---

## Contributing

This repository is primarily a personal/teams workspace framework, but it is structured to be forked and adapted:

1. Fork the repo.
2. Customize `domains/` to match your integrations.
3. Adjust `.cursor/rules/` to encode your own agent protocol.
4. Evolve `dexter.sql` and `schema.sql` to match your data model.
5. Update `.cursor/cursor-config.md` and this README for your team.

---

## License & contact

- **License**: MIT (see `LICENSE`).
- **Maintainer**: [@lexxiBlue](https://github.com/lexxiBlue).
