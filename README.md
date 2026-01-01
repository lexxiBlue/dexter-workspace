# Dexter Workspace

**AI-First Cursor IDE Framework with Guardrails**

Dexter is a structured workspace framework designed for autonomous AI agent operation within Cursor IDE. It provides a single SQLite database as the source of truth, domain-segregated integrations, and Python helper layers that enforce safety guardrails while enabling powerful automation.

## Architecture Philosophy

### Core Principles

- **Single Source of Truth**: `schema.sql` defines all persistent state
- **Domain Segregation**: Integrations organized by concern (`google/`, `hubspot/`, `automation/`, `projects/`)
- **Guardrailed Autonomy**: Autonomous for non-destructive tasks, explicit confirmation for state changes
- **Audit Trail**: All meaningful actions logged via DB and workspace helpers
- **Framework-Ready**: Minimal implementation surface, maximum structural clarity

### Safety Model

```
Agent Request → db_helper.py → SQLite (dexter.db)
                     ↓
              Validation Layer
                     ↓
            Audit Log + Execute
```

**Guardrails in Practice**:
- DB writes go through `helpers/db_helper.py` only
- External API calls route through `helpers/integration_clients.py`
- Destructive operations require explicit confirmation
- All actions logged with timestamp, user, and change details
- Agent scope limited to workspace boundaries

## Repository Structure

```
dexter-workspace/
├── .cursor/              # Cursor IDE rules and agent protocol
│   └── rules/            # Agent behavior constraints
├── .github/              # CI/CD automation
│   └── workflows/        # GitHub Actions pipelines
├── domains/              # Domain-specific integrations (empty = framework ready)
│   ├── automation/       # Internal workflow orchestration
│   ├── google/           # Google Workspace integrations
│   ├── hubspot/          # HubSpot CRM workflows
│   └── projects/         # Per-project scaffolding
├── helpers/              # Core control layer
│   ├── db_helper.py               # DB access + guardrails
│   ├── reliability.py             # Error handling, validation, decorators
│   └── utils.py                   # Health checks, integrations, workspace gen
├── schema.sql            # Consolidated database schema (source of truth)
├── dexter.db             # Runtime SQLite database (ephemeral in dev)
├── .env.template         # Configuration template
└── README.md             # This file
```

### Key Files

| File | Purpose | Mutability |
|------|---------|------------|
| `schema.sql` | Canonical DB schema | Version controlled, manual edits only |
| `dexter.db` | Runtime database | Ephemeral in dev, backed up in prod |
| `helpers/db_helper.py` | DB access layer | Core contract, test thoroughly |
| `helpers/integration_clients.py` | External API layer | Core contract, extend per domain |
| `.cursor/rules/` | Agent behavior rules | Defines autonomy boundaries |

## Quick Start

### Prerequisites

- Python 3.9+
- Cursor IDE (or VS Code with Cursor extension)
- SQLite 3
- Git

### Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/lexxiBlue/dexter-workspace.git
cd dexter-workspace

# 2. Create environment file from template
cp .env.template .env
# Edit .env with your configuration (API keys, workspace settings)

# 3. Initialize the database
sqlite3 dexter.db < schema.sql

# 4. Install Python dependencies
pip install -r requirements.txt  # If requirements.txt exists

# 5. Open in Cursor IDE
cursor .
```

### Verify Setup

```bash
# Check database initialized
sqlite3 dexter.db "SELECT name FROM sqlite_master WHERE type='table';"

# Test helper imports
python3 -c "from helpers.db_helper import *; print('✓ DB helper loaded')"
python3 -c "from helpers.utils import get_client; print('✓ Integration clients loaded')"
```

## Agent Operation

### Autonomy Boundaries

**Autonomous (No Confirmation Required)**:
- Read operations (DB queries, file reads)
- Log entries and audit trails
- Non-destructive analysis and reporting
- Scoped within workspace boundaries

**Requires Confirmation**:
- Database writes (INSERT, UPDATE, DELETE)
- External API calls (Google, HubSpot, etc.)
- File creation/modification outside workspace
- Destructive operations

### Example Workflows

#### Safe: Query and Report
```python
from helpers.db_helper import query_db

# Agent can autonomously query and report
results = query_db("SELECT * FROM tasks WHERE status='pending'")
print(f"Found {len(results)} pending tasks")
```

#### Guarded: Write Operations
```python
from helpers.db_helper import execute_with_confirmation

# Agent must request confirmation before executing
execute_with_confirmation(
    "UPDATE tasks SET status='completed' WHERE id=?",
    (task_id,),
    description="Mark task as completed"
)
```

## Development Guidelines

### Adding New Domains

1. Create domain folder: `domains/new_domain/`
2. Add domain-specific helpers: `domains/new_domain/helpers.py`
3. Extend `integration_clients.py` if external APIs needed
4. Update schema if domain needs persistent state
5. Add tests to CI pipeline

### Database Changes

```bash
# 1. Edit schema.sql (version controlled)
# 2. Test migration
sqlite3 test.db < schema.sql
# 3. Apply to dev database
sqlite3 dexter.db < migration.sql
# 4. Commit schema changes
git add schema.sql
git commit -m "Add schema for new_feature"
```

### Testing Strategy

```bash
# Run Python linting
ruff check helpers/ domains/

# Run tests (if test suite exists)
pytest tests/

# Validate database schema
sqlite3 dexter.db ".schema" > schema_current.sql
diff <(sqlite3 temp.db < schema.sql && sqlite3 temp.db ".schema") schema_current.sql
```

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci-python-docker.yml`) runs on every push:

1. **Lint**: Ruff checks Python code quality
2. **Test**: pytest validates helper functions
3. **Build**: Docker image packages workspace for deployment
4. **Publish**: Tagged releases pushed to container registry

## MCP Integration

Dexter supports Model Context Protocol (MCP) servers for enhanced agent capabilities:

- **GitHub MCP**: Repository operations (files, PRs, issues)
- **Filesystem MCP**: Local file access and multi-file edits

See `.cursormcp-servers.json` for configuration.

## Security & Safety

### Environment Variables

**NEVER commit `.env` to version control**. Use `.env.template` as a guide.

```bash
# Add to .gitignore (already included)
echo ".env" >> .gitignore
echo "dexter.db" >> .gitignore  # Ephemeral in dev
```

### Database Backups

**Development**: `dexter.db` is ephemeral; recreate from `schema.sql`

**Production**: Implement automated backups
```bash
# Example backup script
sqlite3 dexter.db ".backup dexter_$(date +%Y%m%d_%H%M%S).db"
```

### Access Control

- Limit API keys to minimum required scopes
- Use read-only credentials where possible
- Rotate keys regularly
- Log all authenticated operations

## Troubleshooting

### Database Issues

```bash
# Reset dev database
rm dexter.db
sqlite3 dexter.db < schema.sql
```

### Agent Not Following Rules

Check `.cursor/rules/` for behavior constraints and verify Cursor settings.

### Import Errors

```bash
# Verify Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## Roadmap

- [ ] Complete domain implementations (Google, HubSpot)
- [ ] Comprehensive test coverage for helpers
- [ ] Database migration tooling
- [ ] Production deployment documentation
- [ ] Multi-workspace orchestration

## Contributing

This is a personal workspace framework. If adapting for your use:

1. Fork the repository
2. Customize domains for your integrations
3. Update `.cursor/rules/` for your agent protocol
4. Modify `schema.sql` for your schema

## License

MIT License - See LICENSE file for details

## Contact

Maintained by [@lexxiBlue](https://github.com/lexxiBlue)
