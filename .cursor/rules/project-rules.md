---
description: project-rules
ruleType: always
---

# Dexter Workspace: Project Rules & Quality Gates

**Purpose**: Enforce consistency across codebase via Cursor agent rules.

---

## Architecture Principles

### Layered Structure
```
/dexter-workspace
  /helpers/           → DB queries, client wrappers, auth
  /domain/            → Business logic (customers, orders, integrations)
  /api/               → HTTP endpoints (Flask/FastAPI)
  /tests/             → Unit + integration tests
  schema.sql          → Consolidated schema + seed data (single source of truth)
  requirements.txt    → Pinned versions (poetry.lock preferred)
```

### Import Rules
- ✅ **Local**: `from helpers.db_helper import query_db`
- ✅ **Third-party**: `from fastapi import FastAPI` (pinned in `requirements.txt`)
- ❌ **Circular**: No `helpers/` importing from `domain/` or `api/`
- ❌ **Relative parent**: Never `from ..helpers import` (use absolute paths)

---

## Code Quality Checklist

### Python Standards
1. **Type hints** for all public functions (PEP 484)
   ```python
   # Good
   def get_customer_by_id(customer_id: str) -> dict | None:
       return db.query(f"SELECT * FROM customers WHERE id = ?", (customer_id,))
   
   # Bad
   def get_customer_by_id(customer_id):
       return db.query(f"SELECT * FROM customers WHERE id = {customer_id}")
   ```

2. **Docstrings** (Google style) for all functions
   ```python
   def process_order(order_id: str, status: str) -> bool:
       """Process an order and update its status.
       
       Args:
           order_id: UUID of the order
           status: New status (pending, completed, failed)
       
       Returns:
           True if update succeeded, False otherwise
       
       Raises:
           ValueError: If status is invalid
       """
   ```

3. **No hardcoded secrets**
   - ❌ `password="super_secret_123"` in code
   - ✅ `password = os.getenv("DB_PASSWORD")`

4. **SQL injection prevention**
   - ❌ `f"SELECT * FROM orders WHERE id = {order_id}"`
   - ✅ `"SELECT * FROM orders WHERE id = ?", (order_id,)` (parameterized)

5. **Timezone-aware datetimes**
   - ❌ `datetime.now()`
   - ✅ `datetime.now(timezone.utc)`

6. **Exception handling** (never bare `except:`)
   ```python
   try:
       result = db.query(query)
   except sqlite3.OperationalError as e:
       logger.error(f"DB error: {e}")
       return None
   ```

### Testing Standards
- **Coverage**: Minimum 80% for `helpers/` and `domain/`
- **Test structure**: `test_<function_name>.py` or `test_<module>.py`
- **Fixtures**: Use `conftest.py` for shared DB setup
- **Mocking**: Mock external APIs (don't make real HTTP calls in tests)

---

## Database Rules

### Schema Management
1. **All tables in `schema.sql`** (single source of truth)
2. **No direct `CREATE TABLE` in migration files** (modify `schema.sql` instead)
3. **Seed data** in `schema.sql` after schema definition
4. **Foreign keys enabled** at connection time:
   ```python
   conn.execute("PRAGMA foreign_keys = ON")
   ```

### Query Patterns
- ✅ Use `helpers/db_helper.py` for all DB access
- ❌ Raw SQL in domain logic
- ✅ Return typed dicts: `dict[str, Any]` with field validation
- ❌ Raw tuples from `fetchall()`

---

## File Organization Rules

### What lives where

| Path | Purpose | Example |
|------|---------|----------|
| `helpers/db_helper.py` | DB queries, connection mgmt | `query_db()`, `get_or_create_customer()` |
| `helpers/integration_clients.py` | HTTP clients, external APIs | `HubSpotClient`, `ShopifyClient` |
| `domain/customers.py` | Customer business logic | `Customer` class, validation |
| `domain/orders.py` | Order business logic | `Order` class, status workflows |
| `api/routes.py` | HTTP endpoints | `@app.get("/customers/{id}")` |
| `tests/test_helpers.py` | Unit tests for helpers | Mock DB, test queries |
| `tests/test_integration.py` | End-to-end tests | Real DB in temp file |

---

## Naming Conventions

### Variables & Functions
- snake_case: `customer_id`, `get_total_price()`
- Booleans start with `is_`, `has_`, `can_`: `is_active`, `has_address`
- Private functions: `_internal_helper()` (one leading underscore)

### Classes
- PascalCase: `Customer`, `OrderProcessor`
- Don't suffix with `_Class` or `_Impl`

### Constants
- UPPER_SNAKE_CASE: `MAX_RETRY_COUNT = 3`
- Define at module level

### Database
- snake_case tables: `customers`, `orders`, `integration_configs`
- snake_case columns: `customer_id`, `created_at`, `is_active`
- IDs as UUID: `id` (primary key), `<entity>_id` (foreign key)

---

## Git Workflow Rules (enforced in Cursor)

1. **Branch naming**: `feature/`, `fix/`, `docs/`, `chore/`
   ```bash
   feature/customer-search
   fix/db-connection-leak
   docs/api-endpoints
   ```

2. **Commit messages**: Start with emoji + verb + scope
   ```
   🌟 feat(customers): Add bulk import endpoint
   🐛 fix(db): Close connection in exception handler
   📄 docs(readme): Update setup instructions
   ```
   Emojis: `🌟 feat`, `🐛 fix`, `📄 docs`, `⚡ perf`, `🧪 refactor`, `✍️ test`

3. **No direct commits to `main`** → All changes via PR

4. **PR title format**: `[type] Description`
   ```
   [feat] Add customer search API
   [fix] Resolve timezone issue in order timestamps
   [docs] Update deployment guide
   ```

---

## Anti-Patterns (Cursor should reject)

### Dangerous Patterns
| Pattern | Why Bad | Fix |
|---------|--------|-----|
| `from *` | Pollutes namespace | Explicit imports |
| `exec()`, `eval()` | Code injection risk | Use safe alternatives |
| Global mutable state | Hard to test | Pass as args |
| Bare `except:` | Silently fails | Catch specific exceptions |
| `print()` for logging | Can't control level/format | Use `logging` module |
| Sleeps in tests | Flaky CI | Use mocking/fixtures |
| Hardcoded paths | Breaks on different systems | Use `pathlib.Path`, env vars |

---

## Environment & Configuration

### `.env` Rules
- ✅ Commit `.env.template` (no values)
- ❌ Never commit `.env` (add to `.gitignore`)
- ✅ Load via `python-dotenv`:
  ```python
  from dotenv import load_dotenv
  load_dotenv()
  db_path = os.getenv("DB_PATH", "dexter.db")
  ```

### Required env vars
```
DB_PATH=dexter.db
LOG_LEVEL=INFO
GITHUB_TOKEN=<your-token>
```

---

## Cursor Agent Checklist

Before accepting LM-generated code:
- [ ] Passes `mypy --strict` (type checking)
- [ ] Passes `ruff check` (linting)
- [ ] Has docstrings + type hints
- [ ] No `eval()`, `exec()`, hardcoded secrets
- [ ] Uses parameterized SQL queries
- [ ] Creates test cases
- [ ] No circular imports
- [ ] Follows naming conventions
- [ ] Handles exceptions explicitly
