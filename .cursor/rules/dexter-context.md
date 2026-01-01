# Dexter Domain Context for Cursor Agent

**Purpose**: Help Cursor LM understand Dexter's business domain, data model, and integration patterns.

---

## Project Overview

**Dexter** = Equipment rental & procurement management system for equipment orders (forklifts, excavators, etc.).

- **Core entities**: Customers, Orders, Equipment, Integrations (HubSpot, Shopify)
- **Tech stack**: Python + SQLite (local), Flask/FastAPI (API), MCP servers (GitHub integration)
- **Goal**: Automate equipment procurement pipeline with domain intelligence

---

## Data Model (Quick Reference)

### Customers
```sql
CREATE TABLE customers (
    id TEXT PRIMARY KEY,           -- UUID
    name TEXT NOT NULL,             -- Customer name
    email TEXT UNIQUE NOT NULL,     -- Email for contact
    company TEXT,                   -- Company affiliation
    integration_type TEXT,          -- 'hubspot' | 'shopify' | 'manual'
    integration_id TEXT,            -- External system ID
    is_active BOOLEAN DEFAULT 1,    -- Soft delete flag
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Orders
```sql
CREATE TABLE orders (
    id TEXT PRIMARY KEY,            -- UUID
    customer_id TEXT NOT NULL,      -- FK to customers
    equipment_type TEXT NOT NULL,   -- 'forklift' | 'excavator' | ...
    quantity INTEGER DEFAULT 1,     -- Units ordered
    total_price REAL NOT NULL,      -- Final price in USD
    status TEXT DEFAULT 'pending',  -- pending|quoted|confirmed|shipped|completed|cancelled
    notes TEXT,                     -- Internal notes
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE CASCADE
);
```

### Integrations (Config)
```sql
CREATE TABLE integration_configs (
    id TEXT PRIMARY KEY,            -- UUID
    customer_id TEXT NOT NULL,      -- FK to customers
    integration_type TEXT NOT NULL, -- 'hubspot' | 'shopify'
    api_key TEXT NOT NULL,          -- Encrypted in production
    api_base_url TEXT,              -- Integration endpoint
    sync_status TEXT DEFAULT 'active', -- active|paused|error
    last_sync_at DATETIME,          -- Timestamp of last successful sync
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    UNIQUE(customer_id, integration_type)
);
```

---

## Business Rules for LM

### Order Workflow
1. **Pending** → New order received (from UI, integration, or API)
2. **Quoted** → Price calculated, waiting for customer approval
3. **Confirmed** → Customer approved, order is binding
4. **Shipped** → Equipment dispatched
5. **Completed** → Delivered and signed off
6. **Cancelled** → Order rejected or voided

**LM constraint**: 
- Never allow status downgrade (e.g., Shipped → Quoted)
- Cannot delete confirmed+ orders; must mark `cancelled`
- `cancelled` orders should not be re-opened

### Pricing Rules
- Equipment prices stored in external CMS or as configuration
- Never hardcode prices in code (fetch from `integration_clients.py`)
- Apply discounts based on customer tier (stored in customer record)
- Total price = (equipment_price * quantity) * (1 - discount_rate)

### Integration Sync Behavior
- **HubSpot**: Syncs customer info, pull orders from CRM
- **Shopify**: Syncs products as equipment catalog, orders as Dexter orders
- **Sync logic**: Read-only by default (import only, no push back unless explicitly configured)
- **Error handling**: Log sync errors, alert user, don't crash app

---

## Code Patterns LM Should Follow

### Domain Layer (What to write)
```python
# domain/orders.py
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class Order:
    """Order entity with business logic."""
    id: str
    customer_id: str
    equipment_type: str
    quantity: int
    total_price: float
    status: str  # pending|quoted|confirmed|shipped|completed|cancelled
    created_at: datetime
    updated_at: datetime
    
    def can_transition_to(self, new_status: str) -> bool:
        """Check if status transition is allowed."""
        allowed_transitions = {
            'pending': ['quoted', 'cancelled'],
            'quoted': ['confirmed', 'cancelled'],
            'confirmed': ['shipped', 'cancelled'],
            'shipped': ['completed'],
            'completed': [],
            'cancelled': [],
        }
        return new_status in allowed_transitions.get(self.status, [])
    
    def confirm(self) -> bool:
        """Transition to confirmed status."""
        if not self.can_transition_to('confirmed'):
            return False
        self.status = 'confirmed'
        self.updated_at = datetime.now(timezone.utc)
        return True
```

### Helper Layer (How to access data)
```python
# helpers/db_helper.py
from typing import Any

def query_db(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    """Execute SELECT query, return list of dicts."""
    conn = sqlite3.connect(os.getenv("DB_PATH", "dexter.db"))
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.OperationalError as e:
        logger.error(f"Query failed: {e}")
        raise
    finally:
        conn.close()

def get_order_by_id(order_id: str) -> dict[str, Any] | None:
    """Fetch order by ID."""
    results = query_db(
        "SELECT * FROM orders WHERE id = ?",
        (order_id,)
    )
    return results[0] if results else None
```

### Integration Layer (How to sync)
```python
# helpers/integration_clients.py
class HubSpotClient:
    """Sync customers and orders from HubSpot."""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
    
    def get_contacts(self) -> list[dict]:
        """Fetch contacts from HubSpot CRM."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = requests.get(
            f"{self.base_url}/crm/v3/objects/contacts",
            headers=headers,
        )
        response.raise_for_status()
        return response.json().get("results", [])
    
    def sync_to_dexter(self) -> bool:
        """Import HubSpot contacts as Dexter customers."""
        try:
            contacts = self.get_contacts()
            for contact in contacts:
                # Upsert customer in Dexter
                pass
            return True
        except requests.RequestException as e:
            logger.error(f"HubSpot sync failed: {e}")
            return False
```

---

## What LM Should NOT Do

### Anti-Patterns (Cursor agent must reject)

| Pattern | Why Bad | Example |
|---------|--------|----------|
| Hardcoded prices | Prices change; code becomes stale | `total = equipment_type * 1000` |
| No transaction handling | DB corruption on concurrent writes | `conn.execute()` without `BEGIN TRANSACTION` |
| Unencrypted API keys | Security breach risk | `api_key="sk-abc123"` in code |
| Sync to external systems without approval flag | Overwrites customer data | Send order back to Shopify without explicit flag |
| Delete historical orders | Audit trail lost | `DELETE FROM orders WHERE status = 'cancelled'` |
| Status downgrades | Orders can't regress | `UPDATE orders SET status = 'pending' WHERE status = 'shipped'` |

---

## Testing Patterns

### Test Structure (for LM to replicate)
```python
# tests/test_orders.py
import pytest
from domain.orders import Order

class TestOrderTransitions:
    """Test order status state machine."""
    
    def test_can_transition_from_pending_to_quoted(self):
        """Pending orders can move to quoted."""
        order = Order(
            id="test-1",
            customer_id="cust-1",
            equipment_type="forklift",
            quantity=1,
            total_price=5000.0,
            status="pending",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert order.can_transition_to("quoted") is True
    
    def test_cannot_transition_from_completed_to_anything(self):
        """Completed orders are terminal."""
        order = Order(..., status="completed")
        assert order.can_transition_to("pending") is False
        assert order.can_transition_to("shipped") is False
```

---

## Cursor Commands for Dexter

### `/Handoff` 
Loads schema + recent commits + shows git status.

### `/test`
Runs `pytest tests/ -v` with coverage report.

### `/lint`
Runs `ruff check . && mypy --strict helpers/ domain/`

### `/integrations`
Tests all integration clients (HubSpot, Shopify).

### `/db-reset`
(Dangerous!) Recreates `dexter.db` from `dexter.sql` scratch. Requires confirmation.

---

## When to Ask for Clarification

Cursor agent should ask user before proceeding if:
- Implementing new order status (impacts workflow)
- Adding new integration type (requires testing framework)
- Modifying pricing logic (business decision)
- Syncing data back to external systems (risk of data loss)
- Deleting any historical data (audit trail implication)

---

## Success Criteria

✅ **LM-generated code is good if:**
- Follows domain rules (status transitions, pricing logic)
- Uses helper layer (never raw SQL in domain)
- Includes type hints + docstrings
- Handles exceptions explicitly
- Passes `pytest`, `ruff`, `mypy`
- Parameterized SQL queries (no injection risk)
- Tests included with >80% coverage

❌ **Reject if:**
- Hardcoded business logic (prices, status rules)
- Circular imports across domain/helpers/api
- Missing error handling
- SQL injection risk
- Violates workflow rules
