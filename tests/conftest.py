"""
Pytest configuration and fixtures for Dexter workspace tests.
"""

import os
import sqlite3
import tempfile
from pathlib import Path
import pytest

from helpers.db_helper import init_database, get_connection


@pytest.fixture
def temp_db():
    """Create a temporary database for testing.
    
    Yields:
        Path: Path to temporary database file
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    # Initialize database with schemas
    workspace_root = Path(__file__).parent.parent
    dexter_sql = workspace_root / "dexter.sql"
    schema_sql = workspace_root / "schema.sql"
    
    init_database(
        db_path=db_path,
        dexter_sql_path=dexter_sql if dexter_sql.exists() else None,
        schema_sql_path=schema_sql if schema_sql.exists() else None
    )
    
    yield db_path
    
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def db_connection(temp_db):
    """Get a database connection to temporary database.
    
    Args:
        temp_db: Temporary database path fixture
        
    Yields:
        sqlite3.Connection: Database connection
    """
    with get_connection(temp_db) as conn:
        yield conn
