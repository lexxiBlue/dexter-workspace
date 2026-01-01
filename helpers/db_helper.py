"""
Dexter Database Helper
SQLite database operations for workspace configuration management.
"""

import os
import sqlite3
import logging
from pathlib import Path
from typing import Optional, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Get DB path from environment or use default
_DEFAULT_DB_PATH = Path(__file__).parent.parent / "dexter.db"
DB_PATH = Path(os.getenv("DB_PATH", str(_DEFAULT_DB_PATH)))


@contextmanager
def get_connection(db_path: Path = DB_PATH):
    """Get database connection with automatic cleanup.
    
    Args:
        db_path: Path to SQLite database file
        
    Yields:
        sqlite3.Connection: Database connection with Row factory
        
    Raises:
        sqlite3.Error: If connection fails
    """
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()


def init_database(db_path: Path = DB_PATH, 
                  dexter_sql_path: Optional[Path] = None,
                  schema_sql_path: Optional[Path] = None) -> None:
    """Initialize database with schema files.
    
    Loads schema.sql first (creates workspaces table), then dexter.sql 
    (runtime tables that reference workspaces).
    
    Args:
        db_path: Path to SQLite database file
        dexter_sql_path: Path to dexter.sql file (defaults to workspace root)
        schema_sql_path: Path to schema.sql file (defaults to workspace root)
        
    Raises:
        FileNotFoundError: If schema files don't exist
        sqlite3.Error: If schema execution fails
    """
    workspace_root = Path(__file__).parent.parent
    
    if schema_sql_path is None:
        schema_sql_path = workspace_root / "schema.sql"
    if dexter_sql_path is None:
        dexter_sql_path = workspace_root / "dexter.sql"
    
    # Ensure database directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove existing database if it exists (for clean initialization)
    if db_path.exists():
        logger.warning(f"Removing existing database at {db_path}")
        db_path.unlink()
    
    # Load schema.sql first (creates workspaces table)
    if not schema_sql_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_sql_path}")
    
    with open(schema_sql_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    
    # Load dexter.sql (runtime tables that reference workspaces)
    if not dexter_sql_path.exists():
        raise FileNotFoundError(f"Core schema file not found: {dexter_sql_path}")
    
    with open(dexter_sql_path, "r", encoding="utf-8") as f:
        dexter_schema = f.read()
    
    # Execute schemas in correct order: schema.sql first, then dexter.sql
    with get_connection(db_path) as conn:
        conn.executescript(schema_sql)
        conn.executescript(dexter_schema)
    
    logger.info(f"Database initialized at {db_path}")
    print(f"Database initialized at {db_path}")


def create_workspace(name: str, description: str = "", project_type: str = "general") -> int:
    """Create a new workspace configuration.
    
    Args:
        name: Workspace name (must be unique)
        description: Optional workspace description
        project_type: Type of project (default: "general")
        
    Returns:
        int: ID of the created workspace
        
    Raises:
        sqlite3.IntegrityError: If workspace name already exists
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO workspaces (name, description, project_type)
            VALUES (?, ?, ?)
            """,
            (name, description, project_type)
        )
        return cursor.lastrowid


def get_workspace(workspace_id: int) -> Optional[dict[str, Any]]:
    """Get workspace by ID.
    
    Args:
        workspace_id: ID of the workspace
        
    Returns:
        dict[str, Any]: Workspace data as dictionary, or None if not found
    """
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM workspaces WHERE id = ?",
            (workspace_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def list_workspaces() -> list[dict[str, Any]]:
    """List all workspaces.
    
    Returns:
        list[dict[str, Any]]: List of all workspaces ordered by name
    """
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM workspaces ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]


def add_rule(workspace_id: int, rule_name: str, content: str, 
             description: str = "", globs: str = "", rule_type: str = "always") -> int:
    """Add a Cursor rule to workspace.
    
    Args:
        workspace_id: ID of the workspace
        rule_name: Name of the rule
        content: Rule content/markdown
        description: Optional rule description
        globs: Comma-separated glob patterns
        rule_type: Type of rule (default: "always")
        
    Returns:
        int: ID of the created rule
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO cursor_rules (workspace_id, rule_name, description, globs, rule_type, content)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (workspace_id, rule_name, description, globs, rule_type, content)
        )
        return cursor.lastrowid


def get_rules(workspace_id: int) -> list[dict[str, Any]]:
    """Get all active rules for a workspace.
    
    Args:
        workspace_id: ID of the workspace
        
    Returns:
        list[dict[str, Any]]: List of active rules
    """
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM cursor_rules WHERE workspace_id = ? AND is_active = 1",
            (workspace_id,)
        )
        return [dict(row) for row in cursor.fetchall()]


def add_integration(workspace_id: int, integration_type: str, name: str,
                   config_json: str = "{}", api_key_env_var: str = "") -> int:
    """Add an integration to workspace.
    
    Args:
        workspace_id: ID of the workspace
        integration_type: Type of integration (e.g., "google", "hubspot")
        name: Name of the integration
        config_json: JSON configuration string
        api_key_env_var: Environment variable name for API key
        
    Returns:
        int: ID of the created integration
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO integrations (workspace_id, integration_type, name, config_json, api_key_env_var)
            VALUES (?, ?, ?, ?, ?)
            """,
            (workspace_id, integration_type, name, config_json, api_key_env_var)
        )
        return cursor.lastrowid


def get_integrations(workspace_id: int) -> list[dict[str, Any]]:
    """Get all active integrations for a workspace.
    
    Args:
        workspace_id: ID of the workspace
        
    Returns:
        list[dict[str, Any]]: List of active integrations
    """
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


def get_template(name: str) -> Optional[dict[str, Any]]:
    """Get a workspace template by name.
    
    Args:
        name: Template name
        
    Returns:
        dict[str, Any]: Template data as dictionary, or None if not found
    """
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM templates WHERE name = ?",
            (name,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def list_templates() -> list[dict[str, Any]]:
    """List all available templates.
    
    Returns:
        list[dict[str, Any]]: List of all templates ordered by name
    """
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM templates ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]


def log_action(workspace_id: Optional[int], action_type: str, target: Optional[str] = None,
               description: Optional[str] = None, status: str = "completed") -> int:
    """Log an action to the action_log table.
    
    Args:
        workspace_id: ID of the workspace (optional)
        action_type: Type of action performed
        target: Target of the action (optional)
        description: Description of the action (optional)
        status: Status of the action (default: "completed")
        
    Returns:
        int: ID of the logged action
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO action_log (workspace_id, action_type, target, description, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (workspace_id, action_type, target, description, status)
        )
        return cursor.lastrowid


def get_context(workspace_id: Optional[int], key: str) -> Optional[str]:
    """Get context value for a workspace and key.
    
    Args:
        workspace_id: ID of the workspace (optional)
        key: Context key
        
    Returns:
        str: Context value, or None if not found or expired
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT value FROM context 
            WHERE workspace_id = ? AND key = ? 
            AND (expires_at IS NULL OR expires_at > datetime('now'))
            """,
            (workspace_id, key)
        )
        row = cursor.fetchone()
        return row["value"] if row else None


def set_context(workspace_id: Optional[int], key: str, value: str, 
                expires_at: Optional[str] = None) -> None:
    """Set context value for a workspace and key.
    
    Args:
        workspace_id: ID of the workspace (optional)
        key: Context key
        value: Context value
        expires_at: Optional expiration timestamp (ISO format)
    """
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO context (workspace_id, key, value, expires_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(workspace_id, key) DO UPDATE SET
                value = excluded.value,
                expires_at = excluded.expires_at,
                updated_at = CURRENT_TIMESTAMP
            """,
            (workspace_id, key, value, expires_at)
        )


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        init_database()
        print("Database helper ready")
    else:
        print("Usage: python db_helper.py init")
        print("This will initialize the database from schema.sql and dexter.sql")
