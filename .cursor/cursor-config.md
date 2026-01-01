# Cursor IDE Configuration (0.46+)

This document explains the **current** Cursor setup for this workspace, aligned with Cursor v0.46+ official specifications.

## File Structure

```
.cursor/
├── rules/                    # Rule files (.mdc) loaded at startup
│   ├── core.mdc             # Python + general best practices
│   ├── database.mdc         # SQLite + parameterized SQL (enforced)
│   ├── dexter.mdc           # Dexter-specific guidelines
│   ├── automation.mdc       # CI/CD patterns
│   ├── python.mdc           # Python conventions
│   ├── integrations.mdc     # Integration patterns
│   ├── common-pitfalls.md   # Known failure modes (reference)
│   ├── dexter-context.md    # Schema + domain documentation
│   ├── github-integration.md # GitHub workflow patterns
│   ├── handoff.md           # Multi-thread handoff guidelines
│   ├── project-rules.md     # Team standards
│   └── (auto-indexed by Cursor)
├── commands.json            # Custom commands (e.g., /Handoff)
├── commands.md              # Command documentation
├── mcp.json                 # MCP server config (official Cursor format)
├── cli-config.json          # CLI behavior settings
├── README.md                # Agent quickstart
└── SETUP.md                 # Team onboarding guide

.cursorignore               # Block from AI access + indexing (secrets, noise)
.cursorindexingignore       # Control indexing only (compiled files, caches)
```

## Key Configuration Files

### 1. `.cursor/mcp.json` (Official MCP Config)

**Purpose:** Configure Model Context Protocol (MCP) servers that Cursor can invoke.

**Current servers:**
- `github`: Create/read issues, PRs, search repos (requires `GITHUB_TOKEN`)
- `filesystem`: Read files, list directories, search within project

**Format:** Follows Cursor's official MCP JSON schema with top-level `mcpServers` object.

**Why this location:**
- Cursor automatically discovers and loads `.cursor/mcp.json` in project root
- Alternative: `~/.cursor/mcp.json` for global/user-wide MCP config
- ❌ NOT `.cursormcp-servers.json` (custom name, not auto-discovered)

### 2. `.cursor/rules/` (Rule Files)

**Purpose:** Define guardrails, patterns, and domain constraints for AI agents.

**Loading:**
- Cursor automatically discovers all `.mdc` and `.md` files in `.cursor/rules/`
- Rules are applied as hard constraints during code generation
- Agents see all rules when `/Handoff` command is invoked

**Rule types:**
- **Core rules** (always enforced): `core.mdc`, `database.mdc`, `dexter.mdc`
  - Parameterized SQL mandatory
  - No table invention allowed
  - Schema changes require explicit user confirmation
- **Context rules** (apply by file type): `python.mdc`, `automation.mdc`, `integrations.mdc`
- **Reference rules** (for agent context): `common-pitfalls.md`, `dexter-context.md`, `project-rules.md`

**Legacy note:** `.cursorrules` (root-level single file) is still supported but **deprecated**. Current setup uses `.cursor/rules/` (directory) instead, which is the recommended pattern.

### 3. `.cursorignore` (Best-Effort AI Block)

**Purpose:** Prevent Cursor from accessing sensitive or noisy files.

**Coverage:**
- ✅ Secrets: `.env`, `.env.*`, `*.key`, `secrets/`, `.aws/`, `.kube/`
- ✅ Dependencies: `node_modules/`, `.venv/`, `__pycache__/`, `.egg-info/`
- ✅ Build artifacts: `dist/`, `build/`, `*.log`, `*.pyc`
- ✅ Large files: `*.mp4`, `*.zip`, `data/`
- ✅ Databases: `*.db`, `*.sqlite`, `.cache/`
- ✅ IDE files: `.idea/`, `.vscode/`, `.git/`

**Behavior:** Cursor will **not show or index** these files to AI; they remain invisible to agents.

### 4. `.cursorindexingignore` (Indexing-Only Control)

**Purpose:** Control what Cursor indexes for search/context **without blocking AI access**.

**Usage:** Prevent search pollution from auto-generated files while keeping them available for manual inspection.

**Current patterns:**
- Test fixtures: `tests/fixtures/`, `__mocks__/`
- Compiled files: `*.pyc`, `*.class`, `*.o`
- Cache dirs: `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`

**Inheritance:** Automatically inherits patterns from `.gitignore`, so you don't need to repeat them.

**Correct filename:** ``.cursorindexingignore`` (with "ing" suffix)
- ❌ `.cursorindexignore` (legacy, may still work but not documented)
- ✅ `.cursorindexingignore` (current Cursor 0.46+ spec)

### 5. `.cursor/commands.json` (Custom Commands)

**Purpose:** Define custom `/CommandName` shortcuts that agents can invoke.

**Current command:**
```json
{
  "name": "handoff",
  "title": "Dexter Handoff",
  "description": "Bootstrap Dexter workspace session with schema, rules, and helpers loaded into context.",
  "prompt": [/* multi-line setup instructions */]
}
```

**Invocation:** In Cursor, type `/Handoff` to trigger the multi-step bootstrap.

**Benefits:**
- Ensures consistent session initialization across threads
- Loads schema, helpers, rules in predictable order
- Summarizes state and presents task plan to user

## Security & Performance Tuning

### AI Safety

✅ **Parameterized SQL enforced:** `database.mdc` rule makes `?` placeholders mandatory
✅ **Secrets blocked:** `.cursorignore` hides `.env`, `*.key`, `.aws/`
✅ **No table invention:** `dexter.mdc` rule forbids undocumented SQL tables
✅ **Schema is source of truth:** Schema files + `dexter-context.md` match exactly

### Context Efficiency

✅ **Cache exclusion:** `.cursorindexingignore` skips `__pycache__`, `.mypy_cache/`
✅ **Large file handling:** `*.mp4`, `*.zip` blocked; docs not indexed (manual access only)
✅ **Tight index:** Only source code, schema, rules, and tests are searchable

## Troubleshooting

### MCP Servers Not Connecting

1. Verify `.cursor/mcp.json` exists and is valid JSON:
   ```bash
   jq . .cursor/mcp.json
   ```

2. Check environment variables:
   ```bash
   echo $GITHUB_TOKEN  # Must be set for GitHub MCP
   ```

3. Restart Cursor IDE (sometimes required for MCP discovery)

### Rules Not Applying

1. Verify rule files are in `.cursor/rules/` (not root `.cursorrules`)
2. Check file extensions: `.mdc` or `.md` only
3. Restart Cursor to reload rules
4. Check rule syntax (must be valid YAML frontmatter for `.mdc` files)

### Index Out of Sync

After major schema changes:
1. Open Cursor Settings > Features > Codebase Indexing
2. Click "Resync Codebase Index"
3. Wait for re-indexing to complete

## References

- **Cursor Official Docs:** https://docs.cursor.com/context/rules
- **MCP Protocol:** https://docs.cursor.com/context/mcp
- **Ignore Files:** https://docs.cursor.com/context/ignore-files
- **GitHub MCP Server:** https://github.com/modelcontextprotocol/servers/tree/main/src/github

## Version Info

- **Cursor:** v0.46+ (current as of 2026-01)
- **MCP Schema:** Current (per Cursor docs)
- **Rule Format:** `.mdc` (recommended) + `.md` (legacy but supported)
- **Config Location:** `.cursor/` at project root (not `~/.cursor` for project-specific config)
