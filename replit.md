# Dexter Workspace

## Overview
Dexter is a Cursor IDE workspace configuration framework with SQL database and Python helpers. This is a static file project - no running servers or background processes.

## Project Structure
- `schema.sql` - SQLite database schema for workspace configurations
- `.cursor/rules/*.mdc` - Cursor AI behavior rules
- `helpers/*.py` - Python helper scripts (not executed on Replit)
- `.cursorignore`, `.cursorindexignore` - Cursor file exclusion configs
- `.vscode/settings.json` - VS Code/Cursor editor settings
- `.cursor/cli-config.json` - Cursor CLI configuration
- `push-to-github.js` - Script to push files to GitHub

## User Preferences
- No background processes or running servers
- Cost-efficient setup (no credit-consuming workflows)
- Files to be pushed to GitHub for use in Cursor IDE

## Usage
Run `npm run push` to push all files to your GitHub repository.

## Recent Changes
- Initial setup with Cursor workspace configuration files
- SQL schema for workspace management
- Python helpers for database and integration management
