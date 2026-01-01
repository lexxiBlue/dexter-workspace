# Dexter Workspace

## Overview
Dexter is an AI-first Cursor IDE workspace. Single database as source of truth, autonomous operation with guardrails.

## Structure
- `schema.sql` - Database schema (all tables: workspace config + runtime)
- `.cursor/rules/dexter.mdc` - AI operating protocol
- `domains/` - Organized work areas (hubspot, google, automation, projects)

## User Preferences
- No background processes
- AI-first (no human-readable bloat)
- Database-driven configuration
- Autonomous but verified operation

## Dexter Guardrails
- Log all actions to database
- Pause on destructive operations
- Verify after every change
- Stay within explicit scope
- Ask once if ambiguous, then proceed
