# Dexter Workspace

## Overview
Dexter is an AI-first Cursor IDE workspace. Single database as source of truth, autonomous operation with guardrails.

## Structure
- `dexter.sql` - Database schema (rules, action log, context, domains)
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
