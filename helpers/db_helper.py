"""
Dexter Database Helper
SQLite database operations for workspace configuration management.
"""

import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager


DB_PATH = Path(__file__).parent.parent / "dexter.db"


@contextmanager
def get_connection(db_path: Path = DB_PATH):
    """Get database connection with automatic cleanup."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database(db_path: Path = DB_PATH, schema_path: Optional[Path] = None):
    """Initialize database with schema."""
    if schema_path is None:
        schema_path = Path(__file__).parent.parent / "schema.sql"
    
    with open(schema_path, "r") as f:
        schema = f.read()
    
    with get_connection(db_path) as conn:
        conn.executescript(schema)
    
    print(f"Database initialized at {db_path}")


def create_workspace(name: str, description: str = "", project_type: str = "general"):
    """Create a new workspace configuration."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO workspaces (name, description, project_type)
            VALUES (?, ?, ?)
            """,
            (name, description, project_type)
        )
        return cursor.lastrowid


def get_workspace(workspace_id: int) -> Optional[dict]:
    """Get workspace by ID."""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM workspaces WHERE id = ?",
            (workspace_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def list_workspaces() -> list[dict]:
    """List all workspaces."""
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM workspaces ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]


def add_rule(workspace_id: int, rule_name: str, content: str, 
             description: str = "", globs: str = "", rule_type: str = "always"):
    """Add a Cursor rule to workspace."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO cursor_rules (workspace_id, rule_name, description, globs, rule_type, content)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (workspace_id, rule_name, description, globs, rule_type, content)
        )
        return cursor.lastrowid


def get_rules(workspace_id: int) -> list[dict]:
    """Get all rules for a workspace."""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM cursor_rules WHERE workspace_id = ? AND is_active = 1",
            (workspace_id,)
        )
        return [dict(row) for row in cursor.fetchall()]


def add_integration(workspace_id: int, integration_type: str, name: str,
                   config_json: str = "{}", api_key_env_var: str = ""):
    """Add an integration to workspace."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO integrations (workspace_id, integration_type, name, config_json, api_key_env_var)
            VALUES (?, ?, ?, ?, ?)
            """,
            (workspace_id, integration_type, name, config_json, api_key_env_var)
        )
        return cursor.lastrowid


def get_integrations(workspace_id: int) -> list[dict]:
    """Get all integrations for a workspace."""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM integrations WHERE workspace_id = ? AND is_active = 1",
            (workspace_id,)
        )
        return [dict(row) for row in cursor.fetchall()]


def get_preference(key: str) -> Optional[str]:
    """Get a preference value."""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT value FROM preferences WHERE key = ?",
            (key,)
        )
        row = cursor.fetchone()
        return row["value"] if row else None


def set_preference(key: str, value: str, description: str = ""):
    """Set a preference value."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO preferences (key, value, description)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = CURRENT_TIMESTAMP
            """,
            (key, value, description, value)
        )


def get_template(name: str) -> Optional[dict]:
    """Get a workspace template by name."""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM templates WHERE name = ?",
            (name,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def list_templates() -> list[dict]:
    """List all available templates."""
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM templates ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]


if __name__ == "__main__":
    init_database()
    print("Database helper ready")
