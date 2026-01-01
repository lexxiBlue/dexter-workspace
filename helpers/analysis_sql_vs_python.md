# Analysis: Python Scripts vs SQL Scripts

## Summary
**74 SQL operations** across 6 Python files. Some could be SQL views/scripts, but most need Python for logic.

## Candidates for SQL Conversion

### ✅ Good Candidates (Pure SQL Operations)

1. **Cleanup Operations** (`utils.py`)
   - `cleanup_expired_contexts()` - Simple DELETE
   - `cleanup_old_actions()` - Simple DELETE
   - **Recommendation**: SQL scripts (`cleanup.sql`)

2. **Simple Queries** (`db_helper.py`, `agent_brain.py`)
   - Many SELECT queries are just parameterized lookups
   - **Recommendation**: SQL views for common queries (e.g., `view_active_rules`, `view_recent_decisions`)

3. **Statistics Queries** (`utils.py`)
   - `get_system_stats()` - Multiple COUNT queries
   - `get_context_stats()` - Aggregation queries
   - **Recommendation**: SQL views (e.g., `view_system_stats`)

### ❌ Not Suitable (Need Python Logic)

1. **File Operations**
   - `rule_migration.py` - Parses frontmatter, file I/O
   - `rule_sync.py` - File system operations
   - `rule_loader.py` - String formatting for context

2. **Error Handling & Decorators**
   - `reliability.py` - Retry logic, decorators, validation
   - Needs Python control flow

3. **Integration Clients**
   - `utils.py` - API clients, HTTP requests
   - Needs Python libraries

4. **Complex Logic**
   - `agent_brain.py` - `learn_from_decision()` has conditional logic
   - `update_pattern_success()` - Moving average calculation
   - Needs Python for calculations

## Recommendations

### Option 1: SQL Views (Low Risk)
Create views for common queries:
```sql
CREATE VIEW view_active_rules AS
SELECT * FROM cursor_rules WHERE is_active = 1;

CREATE VIEW view_recent_decisions AS
SELECT * FROM agent_decisions 
WHERE created_at > datetime('now', '-7 days')
ORDER BY created_at DESC;
```

### Option 2: SQL Scripts for Cleanup (Medium Risk)
Move cleanup to SQL scripts:
```sql
-- cleanup_expired_contexts.sql
DELETE FROM context 
WHERE expires_at IS NOT NULL 
AND expires_at < datetime('now');
```

### Option 3: Keep Python (Current State)
- Python provides type safety, error handling, testing
- SQLite doesn't support stored procedures
- Python functions are reusable and composable

## Verdict

**Keep Python for most operations.** SQL views/scripts only for:
1. Simple cleanup operations (SQL scripts)
2. Common read-only queries (SQL views)

**Reason**: Python provides better error handling, type safety, and composability. SQLite limitations (no stored procedures) mean complex logic stays in Python.
