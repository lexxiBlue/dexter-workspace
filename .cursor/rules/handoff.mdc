---
description: handoff
ruleType: always
---

# Cursor Rules - Dexter Workspace

These rules shape how the Cursor agent behaves in this repository, including the `/Handoff` command.

## Repo Identity

- This is the **Dexter Workspace** repo.
- Single source of truth: `schema.sql`.
- Runtime DB: `dexter.db` (ephemeral in dev, guarded in prod).

## Global Behavior

- Prefer **reading and summarizing** over writing.
- All writes that change state (code, schema, DB) require either:
  - An explicit user request, or
  - A clear confirmation step proposed and accepted in chat.
- Never modify `.env` values; only suggest changes.

## /Handoff Command

When the user types `/Handoff`:

1. **Clarify Intent (lightweight)**
   - Assume the user wants: "Sync from GitHub, ensure DB/env are ready, and get a summary of changes."
   - Do **not** ask multiple follow-up questions unless an error occurs.

2. **Execute Handoff Protocol**
   - Follow the exact steps defined in `.cursor/commands.md`.
   - Surface any blocking issues instead of trying to auto-fix them.

3. **Respect Safety Boundaries**
   - No pushes to remote.
   - No merges/rebases.
   - No destructive DB operations.

## Git Operations

- Allowed without extra confirmation:
  - `git fetch`, `git status`, `git log`.
  - `git checkout main` and `git pull --ff-only origin main`.
- Disallowed without explicit user confirmation:
  - `git push`.
  - `git merge`, `git rebase`, `git reset`, `git clean`.

## Database Operations

- Allowed autonomously:
  - Creating `dexter.db` if missing using `schema.sql`.
  - Running read-only queries for analysis and reporting.
- Requires explicit confirmation:
  - Dropping tables, truncating data, or recreating `dexter.db`.
  - Any bulk update or delete operations.

## File Operations

- Allowed autonomously:
  - Editing files under `helpers/`, `domains/`, `README.md`, and CI/config files **when asked to implement or modify something**.
  - Creating new files in `domains/` for new integrations.
- Requires confirmation:
  - Deleting files.
  - Large-scale refactors touching many files at once.

## Communication Style

- Keep responses short and action-oriented.
- Prefer:
  - "Done. Next step: ..." over long explanations.
- When something fails (e.g., `git pull` conflict):
  - Explain the failure in one or two sentences.
  - Propose 1–2 concrete next steps.

## Examples

- Good `/Handoff` behavior:
  - "Fetched origin, fast-forwarded main, created dexter.db from schema, and loaded core files. No conflicts."
- Good safety behavior:
  - "`dexter.db` already exists. Skipping recreation to avoid data loss. If you want to reset it, say: `Reset dev database`."