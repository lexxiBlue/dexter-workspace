# GitHub & Language Model Integration Rules

**Scope**: Cursor agent optimization for GitHub-first workflows with production LM quality gates.

---

## GitHub Integration Principles

### Context Window Management
- **Max context**: 200k tokens (reserve 20% for responses)
- **Prioritize**: `schema.sql`, `helpers/`, active branch diffs
- **Skip**: `.git/` objects, build artifacts, node_modules, `.venv/`
- **Lazy load**: Load full files only if directly modified; use file snippets for reference

### Branch Strategy in Cursor
1. **Always work on feature branches** (`/Handoff` ensures `main` pull)
2. **PR-driven workflow**: Create PR → Request LM review → Iterate → Merge
3. **Avoid direct main commits**: Every change pushed as draft PR first

### GitHub LM (Claude/GPT via Copilot)
- **Enable**: GitHub Copilot for Cursor (requires GitHub Pro or Team)
- **Model selection**: Use `gpt-4o` for complex logic, `claude-3.5-sonnet` for quick fixes
- **Telemetry**: Accept GitHub Copilot telemetry to improve suggestions
- **Cache**: Enable long-context caching for `schema.sql` (saves tokens ~90%)

---

## Language Model Quality Standards

### Code Generation Gate
Before accepting LM output, verify:
- [ ] No hallucinated dependencies (check `requirements.txt` against PyPI)
- [ ] SQL syntax valid (test in SQLite REPL or via `.mcp-server` SQL tool)
- [ ] Python types consistent (use `mypy` on generated code)
- [ ] Error handling present (try/except for DB ops, HTTP calls)
- [ ] No hardcoded secrets (check for AWS keys, DB passwords in plaintext)

### Context Injection Rules
**When asking LM to write code:**
1. Provide exact file path + current content snippet
2. Include schema context if DB-related (`schema.sql` relevant sections)
3. Show test case or expected behavior
4. Reference existing patterns from `helpers/`

**Example prompt pattern:**
```
File: `helpers/db_helper.py` (lines 45-60)
[existing code snippet]

Task: Add `get_integration_by_id(id: str)` function
Schema context: `integration_id` is UUID primary key in `integrations` table
Expected behavior: Return dict or None if not found
Test: `get_integration_by_id('abc-123')` should match schema
```

### Reject LM Output If:
- ❌ Introduces `eval()`, `exec()`, or unsafe unpickling
- ❌ Uses `datetime.now()` without timezone (use `datetime.now(timezone.utc)`)
- ❌ Missing docstrings for public functions
- ❌ SQL queries vulnerable to injection (not using parameterized queries)
- ❌ Hardcoded DB paths (use env vars via `.env`)

---

## GitHub Actions Context for LM

### Before asking LM to write workflows:
1. Check latest GitHub Actions syntax (search "GitHub Actions `uses:`")
2. Provide repo secrets list (without values): `GITHUB_TOKEN`, `DB_SEED_SQL`, etc.
3. Specify Python version from `.github/workflows/` existing jobs

### LM should NOT:
- Suggest deprecated actions (`actions/setup-python@v2` → v4+)
- Add self-hosted runners without justification
- Use `run: pip install` without locking versions (`pip-compile`, `poetry.lock`)
- Hardcode credentials (use GitHub Secrets)

---

## Rate Limiting & Cost Control

### Cursor + GitHub Copilot defaults:
- **Requests per minute**: ~60 (soft limit; don't spam multi-line completions)
- **Cost model**: Pay-as-you-go ($20/month seat) or Team ($30/user/month)
- **Cache impact**: Long context caching reduces token cost ~10x

### Optimization in practice:
- Use `/Handoff` to load schema once at session start
- Pin `schema.sql` in chat context (reusable across requests)
- Batch similar tasks (e.g., "Write 3 helper functions" in one prompt)
- Avoid regenerating same logic; ask for tweaks instead

---

## Cursor Agent Behavior with GitHub

### When `/Handoff` runs:
1. Agent pulls latest `main`
2. Initializes `.env` + `dexter.db` (if missing)
3. Shows recent commits + changed files
4. **Then agent is ready** for follow-up commands like:
   - `/test` → Run test suite
   - `/lint` → Run linter
   - `/commit <message>` → Stage + commit (don't push yet)
   - `/pr <title>` → Create draft PR from current branch

### Agent should NOT:
- ❌ Push to `main` directly (always PR-gated)
- ❌ Merge PRs without explicit user command
- ❌ Run `git rebase` (use `git merge` for safety)
- ❌ Delete branches without confirmation
- ❌ Modify `.env` file (only create from `.env.template`)

---

## Pro Tips for GitHub LM in Cursor

1. **Use GitHub Copilot Chat, not inline completions** for complex logic
   - Inline is fast but prone to hallucination
   - Chat allows you to provide context + iterate

2. **Reference PR comments in chat**
   - "Based on PR #42 feedback, update the function to..."
   - LM can read recent PR comments via Copilot API

3. **Test before commit**
   - Always run `/test` after LM generates test files
   - LM sometimes generates broken fixtures

4. **Pin your schema**
   - Start every session: "Context: [paste schema.sql]"
   - Then ask to write queries
   - Prevents hallucinated columns

5. **Use `@github` context in Copilot Chat**
   - Directly reference issues/PRs: "@github #42"
   - LM pulls issue/PR context automatically

---

## Checklist: GitHub + LM Setup

- [ ] GitHub Copilot enabled in Cursor (`Extensions > GitHub Copilot`)
- [ ] Signed into GitHub via Cursor (Accounts menu)
- [ ] `.github/workflows/` configured (CI/CD auto-runs on PR)
- [ ] `.env.template` committed (never `.env`)
- [ ] `schema.sql` in Cursor project root
- [ ] `.cursormcp-servers.json` has GitHub MCP config
- [ ] Tested `/Handoff` command locally
- [ ] Reviewed and accepted telemetry prompt (improves suggestions)
