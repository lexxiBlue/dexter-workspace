# Cursor Commands for Dexter Workspace

This file defines slash commands and startup behaviors for Cursor when working in the `dexter-workspace` repo.

## /Handoff

**Goal**: One-shot sync from GitHub into your local workspace and hand control to the automation agent once you open Cursor in this repo.

### What it does

When you type `/Handoff` in Cursor chat while inside this workspace, the agent will:

1. **Sync from GitHub**
   - Fetch latest changes from `origin`
   - Switch to the `main` branch
   - Pull latest commits

2. **Initialize Dexter Workspace**
   - Ensure `.env` exists (clone from `.env.template` if missing)
   - Ensure `dexter.db` exists and is initialized from `dexter.sql` + `schema.sql`

3. **Summarize Changes for You**
   - Show a short summary of new commits since your last local state
   - Highlight modified files that may impact current work

4. **Prepare Agent Context**
   - Load key files into context:
     - `README.md`
     - `dexter.sql` and `schema.sql`
     - `helpers/db_helper.py`
     - `helpers/integration_clients.py`
     - `.cursormcp-servers.json`

### Contract for the Agent

Cursor agent should follow this protocol when `/Handoff` is invoked:

1. **Workspace Assumptions**
   - Current directory is the repo root (`dexter-workspace`)
   - Git remote `origin` points to `git@github.com:lexxiBlue/dexter-workspace.git` or HTTPS equivalent

2. **Git Sync Sequence**

   ```bash
   # Fetch and fast-forward main
   git fetch origin
   git checkout main
   git pull --ff-only origin main
   ```

   - If fast-forward fails (local divergence), the agent must:
     - Stop and notify: "Local branch diverged from origin/main; manual resolution required."
     - Not attempt merges or rebases autonomously.

3. **Environment Setup**

   ```bash
   # Ensure .env exists
   if [ ! -f .env ] && [ -f .env.template ]; then
     cp .env.template .env
   fi

   # Ensure database exists
   if [ ! -f dexter.db ]; then
     sqlite3 dexter.db < dexter.sql
     if [ -f schema.sql ]; then
       sqlite3 dexter.db < schema.sql
     fi
   fi
   ```

   - Agent must not modify `.env` contents; only create from template if missing.
   - Agent must not drop or recreate `dexter.db` if it already exists without explicit user confirmation.

4. **Change Summary**

   ```bash
   # Show recent commits and changed files
   git log -5 --oneline
   git diff --name-status HEAD@{1} HEAD || true
   ```

   - Present a concise summary in chat, e.g.:
     - "Pulled 2 new commits on main. Modified: helpers/db_helper.py, README.md"

5. **Context Priming**

   After sync, agent should:
   - Open the following files in the editor or load them into context:
     - `README.md`
     - `dexter.sql`
     - `schema.sql`
     - `helpers/db_helper.py`
     - `helpers/integration_clients.py`
     - `.cursormcp-servers.json`

   - Then respond with a short status message, for example:

     > Handoff complete: repo synced from origin/main, DB initialized, core files loaded. What would you like to do next?

## Startup Behavior

On first chat message in this workspace (even without `/Handoff`), the agent should:

1. Detect if this is the `dexter-workspace` repo (presence of `dexter.sql` and `helpers/db_helper.py`).
2. Gently suggest running `/Handoff` if:
   - `git status` shows behind `origin/main`, or
   - `dexter.db` is missing, or
   - `.env` is missing but `.env.template` exists.

Suggested prompt from agent:

> This looks like the Dexter workspace. You can type `/Handoff` to sync from GitHub, initialize the DB, and load core files before we start.

## Safety Rules

- Never push to `origin` as part of `/Handoff`.
- Never perform merges/rebases without explicit instructions.
- Never delete or overwrite `dexter.db` if it exists, unless user explicitly asks.
- Treat `/Handoff` as **read-mostly**: pull, initialize, summarize, but do not alter business data.
