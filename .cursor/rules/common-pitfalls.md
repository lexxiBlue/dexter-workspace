# Common Cursor Pitfalls & Workarounds

**Based on**: GitHub issues, Reddit r/Cursor, community feedback (Jan 2026)

---

## TOP 5 COMPLAINTS & FIXES

### 1. Context Lost Between Sessions 💥
**Problem**: Every new Cursor chat starts fresh; agent forgets schema, project structure, recent changes.

**Symptom**: 
- LM suggests columns that don't exist
- Hallucinated function signatures
- Repeats same mistakes across chats

**Fix**:
- **Use `/Handoff` to auto-load context** (pin files in chat)
- **Create `.cursor/context.md`** with schema summary
  ```markdown
  # Quick Schema Reference
  
  **customers** table:
  - id (UUID, PK)
  - name (TEXT, NOT NULL)
  - email (TEXT, UNIQUE)
  - is_active (BOOLEAN, DEFAULT 1)
  
  **orders** table:
  - id (UUID, PK)
  - customer_id (UUID, FK)
  - total_price (REAL)
  - status (TEXT: pending|completed|failed)
  ```
- **At chat start**, paste context or reference `.cursor/context.md`
- **Enable long-context caching** in GitHub Copilot settings (saves 90% tokens)

---

### 2. Code Generation Produces Broken Tests 💨
**Problem**: LM generates tests with incorrect mocks, missing fixtures, or false-positive passes.

**Symptom**:
- Tests pass locally but fail in CI
- LM mocks don't match real function signatures
- Missing setup/teardown in fixtures

**Fix**:
- **Always run tests locally before commit**
  ```bash
  # After LM generates test_*.py
  pytest tests/ -v --tb=short
  pytest tests/ --cov=helpers --cov=domain  # Check coverage
  ```
- **Use existing `conftest.py` pattern** (LM should replicate it)
  ```python
  # conftest.py
  @pytest.fixture
  def db_fixture():
      """Create temp DB, load schema, yield connection, then cleanup."""
      conn = sqlite3.connect(":memory:")
      conn.execute(open("dexter.sql").read())
      yield conn
      conn.close()
  ```
- **Request LM to write test STRUCTURE first**:
  ```
  Based on conftest.py pattern, write test file structure for order_service.py
  Include:
  1. Import statements
  2. Test class with setup/teardown
  3. 3 test methods (skeleton, no impl)
  ```
- **Then ask LM to fill in test bodies** (reduces hallucination)

---

### 3. Cursor Forgets to Update Related Files 📋
**Problem**: LM modifies function signature but forgets to update:
- Tests that call that function
- Type hints in `__init__.pyi` stub files
- Documentation/docstrings
- Other modules importing it

**Symptom**:
- Refactor one function → 5 other files break
- CI fails with import errors
- "Type mismatch" after LM changes

**Fix**:
- **Use "find all references" before LM modifies**
  - In Cursor: `Cmd+Shift+F` (Find in Project)
  - Search function name across codebase
  - Tell LM: "Function `query_db()` is used in X places:"
- **Ask LM to do atomic multi-file edits**
  ```
  Refactor: Change query_db() signature from (sql: str) to (sql: str, params: tuple)
  
  Files to update:
  1. helpers/db_helper.py → Function definition + docstring
  2. helpers/db_helper.pyi → Type stub
  3. tests/test_db_helper.py → All 6 test calls
  4. domain/customers.py → 3 calls to query_db()
  5. domain/orders.py → 2 calls
  
  Provide diffs for all 5 files in one response.
  ```
- **Always run full test suite after refactor**
  ```bash
  pytest tests/ -x  # Stop on first failure
  ruff check .      # Lint check
  ```

---

### 4. SQL Queries Get Hallucinated 📄
**Problem**: LM generates SQL with:
- Non-existent columns
- Wrong JOIN syntax for SQLite
- Unparameterized queries (SQL injection)
- Syntax errors (SQLite != MySQL)

**Symptom**:
- "no such column: X" errors at runtime
- Query works in LM response but fails in app
- Parameterization broken

**Fix**:
- **Pin schema BEFORE asking for SQL**
  ```
  Schema context (from dexter.sql):
  
  CREATE TABLE customers (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      email TEXT UNIQUE,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );
  
  CREATE TABLE orders (
      id TEXT PRIMARY KEY,
      customer_id TEXT NOT NULL,
      total_price REAL,
      status TEXT,
      FOREIGN KEY(customer_id) REFERENCES customers(id)
  );
  
  Task: Write a query to get all orders for customer_id with total > $100
  Format: Use ? for params, return list of dicts
  ```
- **Test SQL in SQLite REPL first**
  ```bash
  sqlite3 dexter.db
  sqlite> SELECT * FROM orders WHERE customer_id = ? AND total_price > ? LIMIT 10;
  sqlite> .schema orders  # Verify columns exist
  ```
- **Use `helpers/db_helper.py` wrapper** (validates queries before running)
  ```python
  def query_db(sql: str, params: tuple = ()) -> list[dict]:
      """Execute query with SQLite validation."""
      conn = sqlite3.connect(os.getenv("DB_PATH"))
      conn.row_factory = sqlite3.Row  # Return dicts
      try:
          cursor = conn.execute(sql, params)
          return [dict(row) for row in cursor.fetchall()]
      except sqlite3.OperationalError as e:
          logger.error(f"SQL error: {e}\nQuery: {sql}\nParams: {params}")
          raise
  ```

---

### 5. Large Files Cause Context Overflow 📅
**Problem**: If Cursor loads a 5000-line file, LM goes off the rails:
- Forgets top-of-file context
- Generates code inconsistent with early functions
- Makes changes that break earlier lines

**Symptom**:
- "Token limit reached" warnings
- LM suggests code contradicting earlier in same file
- Refactors break unexpectedly

**Fix**:
- **Keep files under 500 lines** (split large modules)
  ```
  # Before: helpers/db_helper.py (2000 lines)
  - DB connection logic
  - Query builders
  - Migration runners
  - Fixtures
  
  # After: Split into
  - helpers/db_helper.py (300 lines) - Connection + query()
  - helpers/db_migrations.py (200 lines) - Migration logic
  - helpers/db_fixtures.py (150 lines) - Test fixtures
  - tests/conftest.py (100 lines) - pytest fixtures
  ```
- **When asking LM to edit large file, give line range**
  ```
  File: helpers/db_helper.py (lines 150-200)
  Current code:
  [paste lines 145-205 with context]
  
  Task: Add error handling to query() function
  ```
- **Use stubs (`.pyi` files) for type hints** (lighter context)
  ```python
  # helpers/db_helper.pyi
  def query_db(sql: str, params: tuple) -> list[dict]: ...
  def get_customer(id: str) -> dict | None: ...
  ```

---

## ADDITIONAL GOTCHAS

### Context Window Management
- **Cursor chat window**: ~100k tokens (with Copilot)
- **How to check**: Look for "Token usage: X" in Copilot panel
- **When you hit limit**: Start new chat, paste summary of previous findings

### Multi-File Edits
- **Don’t ask LM to modify 10 files at once**
  - It forgets changes from file 1 by file 8
  - Break into groups of 3-4 files
- **Always show diffs** ("Here's file A before/after, now file B...")

### Git Workflow Issues
- **LM might forget to `git add` before `git commit`**
  - Workaround: Use Cursor's built-in Git panel (bottom-left)
  - Don't rely on LM for `git` commands
- **Never let LM force-push** (`git push --force`)
  - Always use: `/commit <msg>` then manually push via UI

### Environment Variable Handling
- **LM sometimes hardcodes env vars in generated code**
  - Rule: If LM generates code with `DB_PATH = "dexter.db"`, reject it
  - Require: `DB_PATH = os.getenv("DB_PATH", "dexter.db")`
- **Test env loading**
  ```bash
  # Create test .env
  echo "DB_PATH=test.db" > .env.test
  
  # Run with test env
  PYTHONPATH=. pytest tests/ --env-file .env.test
  ```

---

## CHECKLIST: Before Accepting LM Code

- [ ] **Schema pinned**: Did I paste `dexter.sql` relevant sections?
- [ ] **Test passes**: `pytest tests/ -v` runs clean?
- [ ] **Linting passes**: `ruff check .` has no errors?
- [ ] **No hallucinations**: Verify all functions/columns exist
- [ ] **Type hints**: `mypy --strict` passes?
- [ ] **No hardcoded secrets**: Search for passwords, tokens in code?
- [ ] **Parameterized SQL**: All `?` placeholders, no f-strings?
- [ ] **File references updated**: Related files (tests, imports) also updated?
- [ ] **Context preserved**: Changes don't break earlier in same file?
- [ ] **Git-safe**: No force-push, direct main commits, or destructive operations?

---

## WHEN TO REJECT LM OUTPUT

❌ **Always reject if:**
- Introduces SQL injection risk (f-strings in queries)
- Uses `eval()`, `exec()`, or `pickle.loads()` on untrusted data
- Hardcodes secrets (AWS keys, DB passwords)
- Has zero error handling (bare `try:` or no `except` clause)
- Breaks existing tests or imports
- Doesn’t follow project naming conventions

✅ **Safe to iterate if:**
- Syntax errors (LM will fix after you report)
- Missing type hints (ask LM to add)
- Incomplete docstrings (request expansion)
- Inefficient but correct logic (ask for optimization)

---

## REACHING OUT FOR HELP

If Cursor LM keeps making the same mistake:
1. **Document the error** (paste code + error message)
2. **Check Cursor GitHub issues** (https://github.com/getcursor/cursor/issues)
3. **Try rephrasing prompt** with explicit constraints
4. **Use a different LM model** (Cursor settings > Model: try Claude 3.5 vs GPT-4o)
5. **Pin more context** (full file, schema, related functions)
