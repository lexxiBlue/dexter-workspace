# Dexter

A Cursor IDE workspace configuration framework with SQL database and Python helpers.

## Overview

Dexter provides a structured way to manage Cursor IDE configurations, AI rules, and integration settings for your development workspace.

## Structure

```
dexter/
├── .cursor/
│   ├── rules/          # AI behavior rules
│   │   ├── core.mdc    # Core development guidelines
│   │   ├── python.mdc  # Python-specific rules
│   │   ├── database.mdc # Database guidelines
│   │   ├── integrations.mdc # API integration rules
│   │   └── automation.mdc # Automation guidelines
│   └── cli-config.json # Cursor CLI configuration
├── .vscode/
│   └── settings.json   # VS Code/Cursor settings
├── helpers/
│   ├── db_helper.py    # Database operations
│   ├── workspace_generator.py # Config file generator
│   └── integration_clients.py # API client wrappers
├── schema.sql          # Database schema
├── .cursorignore       # Files to exclude from Cursor
├── .cursorindexignore  # Files to exclude from indexing
├── .env.template       # Environment variables template
└── README.md
```

## Setup

1. Clone this repository
2. Copy `.env.template` to `.env` and fill in your API keys
3. Initialize the database:
   ```bash
   python helpers/db_helper.py
   ```

## Cursor Rules

The `.cursor/rules/` directory contains `.mdc` files that guide Cursor AI behavior:

- **core.mdc** - General coding standards
- **python.mdc** - Python-specific guidelines
- **database.mdc** - SQL and database best practices
- **integrations.mdc** - API integration patterns
- **automation.mdc** - Scripting and automation rules

## Integrations Supported

- Google Workspace (Gmail, Drive, Sheets, Apps Script)
- HubSpot CRM
- OpenAI
- Tavily Search
- GitHub

## Usage

### Generate Workspace Config

```python
from helpers.workspace_generator import generate_workspace
generate_workspace(workspace_id=1, output_dir="./my-project")
```

### Database Operations

```python
from helpers.db_helper import create_workspace, add_rule, add_integration

# Create workspace
ws_id = create_workspace("my-project", "My awesome project", "web")

# Add custom rule
add_rule(ws_id, "custom", "My custom rules content", "Custom guidelines")

# Add integration
add_integration(ws_id, "openai", "OpenAI GPT-4", '{"model": "gpt-4"}', "OPENAI_API_KEY")
```

## License

MIT
