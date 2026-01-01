# Cursor IDE Configuration: Dexter Workspace

**Status**: ✅ Production-ready

**Last updated**: Jan 1, 2026

---

## What's Here

This directory contains **production-grade Cursor IDE setup** for AI-assisted development of the Dexter equipment procurement system.

Files:
```
.cursor/
├── README.md                        ← This file
├── SETUP.md                         ← Installation + daily workflow guide
├── commands.md                      ← Custom Cursor commands (/Handoff, /test, etc.)
├── context.md                       ← Schema quick-reference (pin this in chat)
├── rules/
│  ├── github-integration.md            ← GitHub + LM context management
│  ├── project-rules.md                ← Code quality, naming, architecture
│  ├── common-pitfalls.md              ← Cursor-specific anti-patterns (FROM COMMUNITY)
│  ├── dexter-context.md               ← Business domain + data model
├── .cursormcp-servers.json          ← MCP integration + agent behavior
```

---

## Quick Start (30 seconds)

```bash
# 1. Clone + enter repo
git clone https://github.com/lexxiBlue/dexter-workspace.git
cd dexter-workspace

# 2. Open in Cursor
cursor .

# 3. Open Chat (Cmd+L)
# 4. Type: /Handoff
# 5. Wait for: "Handoff complete"

# Now ask anything, e.g.:
# "Add a function to validate order status transitions"
```

That's it. Everything else is automatic.

---

## File Guide

### `SETUP.md` ⭐ START HERE
**Read this first.** Installation checklist + daily workflow.

- Install Cursor
- Enable GitHub Copilot
- Clone repo + test
- How to start every day
- Do's & don'ts

### `commands.md`
**Custom `/` commands** that automate common tasks.

- `/Handoff` → Load context + pull latest
- `/test` → Run test suite
- `/lint` → Lint + type check
- `/commit <msg>` → Stage + commit

### `rules/` Directory
**Four critical rule files. Read in order:**

#### 1. `github-integration.md`
**GitHub LM + context optimization.**
- How to use GitHub Copilot with Cursor
- Context window management (token budgets)
- Long-context caching (saves 90% token cost)
- GitHub Actions integration
- Rate limiting & cost control

#### 2. `project-rules.md`
**Code quality standards + architecture.**
- Import rules (no circular deps)
- Type hints + docstring requirements
- SQL injection prevention
- Naming conventions (snake_case, PascalCase, UPPER_SNAKE_CASE)
- Database rules (schema management)
- Git workflow (branch naming, commit format)
- Anti-patterns table (what to reject)

#### 3. `common-pitfalls.md`
**Cursor-specific gotchas + fixes (from community).**
- Top 5 complaints:
  1. Context lost between sessions → Use `/Handoff` + context pinning
  2. Broken tests → Always run locally + use fixtures
  3. Forgot to update related files → Multi-file refactor + test suite
  4. SQL hallucination → Pin schema + test in REPL
  5. Token overflow → Split large files + use stubs
- Emergency checklist
- When to reject LM output

#### 4. `dexter-context.md`
**Business domain + Dexter-specific rules.**
- Data model (customers, orders, integrations)
- Order workflow (pending → quoted → confirmed → shipped → completed)
- Pricing + sync behavior
- Code patterns (domain layer, helpers, integrations)
- What LM should NOT do (hardcoded prices, deleting history, etc.)
- Testing patterns
- Success criteria

### `.cursormcp-servers.json`
**MCP (Model Context Protocol) configuration.**

Enables Cursor agent to:
- Access GitHub API (create PRs, read issues)
- Read filesystem (load files into context)
- Manage context window (pinning, caching)
- Integrate with GitHub Copilot

**Key settings:**
```json
{
  "pinnedFiles": ["dexter.sql", "schema.sql", "helpers/"],
  "longContextCaching": true,  // Saves token cost
  "autoCommit": false,          // Never auto-commit
  "prDriven": true,             // All changes via PR
  "secretScannerEnabled": true  // Block hardcoded secrets
}
```

---

## How It All Works Together

### Session Flow

```
1. Open Cursor
   ⮕ Load rules from .cursor/rules/ (auto)
   ⮕ Load MCP from .cursormcp-servers.json (auto)
   ⮕ Chat ready

2. Type /Handoff
   ⮕ Agent pulls latest main
   ⮕ Initializes .env + dexter.db
   ⮕ Pins dexter.sql + schema.sql + helpers/ (context)
   ⮕ Shows recent commits + changed files
   ⮕ "Ready for your next task"

3. Ask LM something
   ⮕ LM reads pinned context (dexter-context.md rules apply)
   ⮕ LM respects project-rules.md (no SQL injection, type hints, etc.)
   ⮕ LM avoids common-pitfalls (doesn't hallucinate schema)
   ⮕ LM generates code

4. Review + test
   ⮕ pytest tests/ -v
   ⮕ ruff check . && mypy --strict

5. Commit + PR
   ⮕ git add . && git commit -m "[type] Description"
   ⮕ Create PR (never push to main directly)

6. Merge when ready
   ⮕ GitHub Actions runs CI/CD
   ⮕ On next /Handoff: pulls latest
```

### The Rule Hierarchy

```
1. common-pitfalls.md
   ⮕ "Reject if: SQL injection, secrets, bare except"
   ⮕ Applies to ALL code

2. project-rules.md
   ⮕ "Use parameterized SQL, type hints, docstrings"
   ⮕ Applies to ALL code

3. github-integration.md
   ⮕ "Cache schema, use long-context caching"
   ⮕ Applies to LM context

4. dexter-context.md
   ⮕ "Order status rules, no hardcoded prices"
   ⮕ Applies to Dexter-specific code

Result: LM respects all four rule sets
```

---

## What Gets Pinned in Context

When you run `/Handoff`, these files are pinned (always available to LM):

```
✅ dexter.sql              (20k tokens) ← Schema + seed data
✅ schema.sql             (5k tokens)  ← Schema only
✅ helpers/db_helper.py   (3k tokens)  ← DB query patterns
✅ helpers/integration_clients.py (5k tokens) ← API client patterns
✅ .cursor/commands.md    (2k tokens)  ← Custom commands
✅ .cursor/rules/dexter-context.md (8k tokens) ← Domain rules

Total: ~40k tokens (reserved)
Available for your conversation: ~120k tokens
```

This stays in context for the entire session (until you start new chat).

---

## Common Scenarios

### Scenario 1: "Build a feature"
```
/Handoff

Write a function get_orders_by_status() in domain/orders.py
Include:
- Type hints
- Docstring
- Error handling
- Unit test with 100% coverage
```

LM will:
1. Read pinned dexter-context.md (knows Order data model)
2. Check project-rules.md (type hints required)
3. Avoid common-pitfalls (no SQL injection)
4. Generate working code

### Scenario 2: "Fix a bug"
```
/Handoff

Bug: Tests fail in CI but pass locally
File: tests/test_orders.py

Task: Diagnose and fix
```

LM will:
1. Check common-pitfalls.md ("Tests fail in CI" section)
2. Suggest fixes (mock external APIs, use fixtures)
3. Verify with `/test`

### Scenario 3: "Refactor large file"
```
/Handoff

Refactor: Split helpers/db_helper.py into smaller modules
Provide diffs for all affected files
Update imports everywhere
```

LM will:
1. Check project-rules.md ("File Organization")
2. Avoid circular imports
3. Update all import statements
4. Provide diffs for 3-4 files together

---

## Maintenance

### When to Update These Files

| File | Update when |
|------|-------------|
| `commands.md` | New workflow command needed |
| `project-rules.md` | Adding naming convention, architecture pattern |
| `common-pitfalls.md` | Community finds new Cursor issue |
| `dexter-context.md` | Business rules change, new entities added |
| `.cursormcp-servers.json` | MCP capabilities updated |

### Adding a New Rule

1. Identify which file (project-rules, common-pitfalls, dexter-context)
2. Add rule + explanation + example
3. Add to "Checklist" section if critical
4. Commit: `git commit -m "[docs] Add rule: ..."` (no code changes)
5. Next `/Handoff` loads new rule automatically

---

## Troubleshooting

### "Rules not loading"
```bash
# Verify files exist
ls -la .cursor/rules/

# Restart Cursor
Cmd+Shift+P → "Developer: Reload Window"
```

### "MCP not working"
```bash
# Check MCP servers installed
npm list -g @modelcontextprotocol/

# Check GitHub token
echo $GITHUB_TOKEN

# Restart Cursor
```

### "Context window overflowing"
```
/Handoff  (resets context)

Or start new chat
```

---

## Next Steps

1. **Read** `SETUP.md` (installation)
2. **Follow** checklist in `SETUP.md`
3. **Test**: Type `/Handoff` in Cursor
4. **Review**: Each rule file (5 min each)
5. **Code**: Ask LM something
6. **Iterate**: `pytest` + `ruff check` + commit

---

## Summary

**You now have:**
- ✅ Custom `/Handoff` command (auto-loads schema + context)
- ✅ 4 rule files (no hallucinations, quality gates)
- ✅ MCP integration (GitHub + filesystem access)
- ✅ Community-sourced pitfall prevention
- ✅ Dexter domain knowledge (business rules, data model)
- ✅ Context caching (saves 90% tokens)
- ✅ Automated quality checks (`/test`, `/lint`)

**Result**: LM stops making mistakes, code quality goes up, development speed 2-3x faster.

---

**Questions?** See individual files or check Cursor docs: https://cursor.sh/docs

**Ready?** Run `/Handoff` and start building. 🚀
