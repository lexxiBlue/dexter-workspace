# Dexter

AI-first Cursor workspace. Single database, autonomous operation with guardrails.

## Structure

```
dexter/
  .cursor/rules/dexter.mdc   # Operating protocol
  dexter.sql                  # Database schema (single source of truth)
  domains/
    hubspot/
    google/
    automation/
    projects/
```

## Setup

1. Copy to your machine
2. Open in Cursor IDE
3. Initialize database: `sqlite3 dexter.db < dexter.sql`

## How Dexter Works

- Autonomous on clear tasks
- Pauses on destructive operations
- Logs all actions to database
- Verifies changes before moving on
- Stays within explicit scope
