# Cursor Setup: Quick Start Guide

**TL;DR**: Run `/Handoff` at the start of every session. That's it. Everything else is automatic.

---

## Installation Checklist

### 1. Install Cursor IDE
```bash
# macOS
brew install cursor

# Linux / Windows
# Download from https://www.cursor.sh/
```

### 2. Enable GitHub Copilot
1. Open Cursor → **Extensions** (Cmd+Shift+X)
2. Search **GitHub Copilot** → Install
3. Sign in with GitHub account (Accounts menu, top-right)
4. Accept telemetry prompt (improves LM suggestions)
5. Verify: GitHub Copilot icon appears in bottom status bar

### 3. Install MCP Servers (Optional but Recommended)
```bash
# These enable Cursor agent to interact with GitHub API + filesystem
npm install -g @modelcontextprotocol/server-github
npm install -g @modelcontextprotocol/server-filesystem
```

### 4. Clone Repo & Set Env
```bash
git clone https://github.com/lexxiBlue/dexter-workspace.git
cd dexter-workspace

# Create .env from template
cp .env.template .env

# Set GitHub token (for MCP integration)
export GITHUB_TOKEN="your-github-pat-here"
```

### 5. Verify Setup
```bash
# Test Cursor can see project
ls .cursor/
# Output should show: commands.md rules/

# Test DB schema
sqlite3 dexter.db ".schema orders"
# Output should show: id, customer_id, total_price, status, etc.
```

---

## Daily Workflow

### At Session Start
1. **Open project in Cursor**
   ```bash
   cd ~/dexter-workspace
   cursor .
   ```

2. **Open Chat** (Cmd+L, or right sidebar Chat tab)

3. **Type `/Handoff`**
   - Agent pulls latest from GitHub
   - Initializes `.env` + `dexter.db` (if missing)
   - Shows recent commits + changed files
   - Loads schema + core files into context
   - **Output**: "Handoff complete. Ready to work."

4. **Now ask your question**, e.g.:
   ```
   Add a new function get_orders_by_customer_id() to domain/orders.py
   Include type hints, docstring, and test case
   ```

### During Work

#### Build a Feature
```
/Handoff

Task: Implement order status validation

Requirement: Write an Order class with:
1. Status field (pending|quoted|confirmed|shipped|completed|cancelled)
2. Method can_transition_to(new_status) that validates transitions
3. Unit tests with 100% coverage
4. No hardcoded business logic

Include:
- Type hints + docstrings
- Exception handling
- Test file structure
```

#### Fix a Bug
```
/Handoff

Bug: SQL queries are not parameterized (injection risk)
File affected: helpers/db_helper.py

Task: Audit all query() calls and ensure:
1. Use ? placeholders for parameters
2. Pass params tuple separately
3. Never use f-strings in SQL

Show diffs for all changes.
```

#### Refactor Code
```
/Handoff

Refactor: Split helpers/db_helper.py (currently 500+ lines)

New structure:
- helpers/db_helper.py (200 lines) - Connection, query()
- helpers/db_migrations.py (200 lines) - Schema updates
- helpers/db_fixtures.py (100 lines) - Test fixtures

Provide file diffs for:
1. What to delete from db_helper.py
2. New files to create
3. Updated imports in other modules
```

### Before Committing
```bash
# 1. Run tests
pytest tests/ -v

# 2. Lint
ruff check . && mypy --strict helpers/ domain/

# 3. Check coverage
pytest tests/ --cov=helpers --cov=domain

# 4. Review changed files
git diff

# 5. Stage + commit
git add .
git commit -m "[type] Description"

# 6. Create PR (don't push to main directly)
# In Cursor: Source Control panel → Create Pull Request
```

---

## Built-In Cursor Commands

### `/Handoff` (Most Important)
**When**: At session start or after switching branches
```
Action: Pull latest main, init DB, load schema, show context
Outcome: Agent ready for your requests
Tokens: 20k-30k (cached for rest of session)
```

### `/test`
**When**: After LM generates test files
```bash
pytest tests/ -v --tb=short
```
Check output for:
- All tests pass (PASSED)
- No errors (FAILED)
- Coverage > 80%

### `/lint`
**When**: Before committing code
```bash
ruff check .
mypy --strict helpers/ domain/
```

### `/commit <message>`
**When**: Ready to stage + commit
```
/commit [feat] Add order status validation

Agent will:
1. Stage changed files
2. Commit with message
3. Show git log
```

---

## Emergency Commands

### Context Lost or Stale
```
/Handoff

(Force reload everything)
```

### Need to Switch Branches
```
/Handoff

(Pulls latest, resets context)
```

### DB Corrupted
```
Run manually:
rm dexter.db
sqlite3 dexter.db < schema.sql

Then /Handoff
```

### LM Keeps Making Same Mistake
```
1. Document the error (paste code + expected output)
2. Create new chat (clear context window)
3. Paste:
   - Relevant file snippet (5-10 lines)
   - Schema context (schema.sql snippet)
   - Domain rule (from .cursor/rules/dexter-context.md)
   - Your specific request
4. Ask LM explicitly to avoid the mistake
```

---

## Do's & Don'ts

### ✅ DO
- Start every session with `/Handoff`
- Pin schema when asking for SQL
- Run `/test` + `/lint` before commit
- Ask LM to write one feature at a time
- Request multi-file diffs together
- Review generated code before accepting
- Test locally before push

### ❌ DON'T
- Commit directly to `main` (use PR)
- Trust LM-generated SQL without testing
- Ask for 10 unrelated refactors at once
- Hardcode secrets, prices, or business logic
- Use bare `except:` or untyped functions
- Let LM run `git push` (only you do that)
- Ignore test failures
- Skip `/lint` before commit

---

## Troubleshooting

### "Token limit reached"
**Cause**: Context window too full (>180k tokens)
**Fix**:
1. Start new chat
2. Run `/Handoff` to reset
3. Work on smaller tasks
4. Commit early + often

### "No such column: X"
**Cause**: LM hallucinated a column
**Fix**:
1. Paste schema: `SELECT sql FROM sqlite_master WHERE type='table' AND name='orders';`
2. Show LM exact columns
3. Ask LM to re-write query
4. Test in SQLite REPL before accepting

### "Type mismatch in import"
**Cause**: LM modified function signature but forgot related files
**Fix**:
1. Use Cmd+Shift+F to find all references
2. Ask LM for multi-file edit with all affected files
3. Run `/lint` to find remaining errors
4. Have LM fix them

### Tests Pass Locally but Fail in CI
**Cause**: Environment variables or DB state differs
**Fix**:
1. Check `.env.template` is complete
2. Verify tests don't rely on external services
3. Run tests with CI env: `pytest tests/ --env-file .env.ci`
4. Ask LM to mock external calls

---

## Files to Read Next

| File | Purpose |
|------|----------|
| `.cursor/commands.md` | What each `/command` does |
| `.cursor/rules/github-integration.md` | GitHub + LM best practices |
| `.cursor/rules/project-rules.md` | Code quality + naming conventions |
| `.cursor/rules/common-pitfalls.md` | What to watch out for |
| `.cursor/rules/dexter-context.md` | Business domain + data model |
| `.cursormcp-servers.json` | MCP config + context optimization |

---

## Support

**Cursor questions?**
- [Cursor Docs](https://cursor.sh/docs)
- [GitHub Issues](https://github.com/getcursor/cursor/issues)
- [Reddit r/Cursor](https://reddit.com/r/cursor)

**Dexter domain questions?**
- Check `.cursor/rules/dexter-context.md`
- Reference `schema.sql` for schema
- See `domain/` and `helpers/` for implementation patterns

---

## Success!

You're ready. Open Cursor, type `/Handoff`, and start building. 🚀
