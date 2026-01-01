#!/usr/bin/env python3
"""
Database validation script for Dexter workspace.
Validates schema integrity and data consistency.
"""

import sys
import sqlite3
from pathlib import Path
from typing import List, Tuple


def validate_schema(db_path: Path) -> Tuple[bool, List[str]]:
    """Validate database schema integrity.
    
    Args:
        db_path: Path to database file
        
    Returns:
        Tuple of (is_valid, list of errors)
    """
    errors = []
    
    if not db_path.exists():
        return False, [f"Database file not found: {db_path}"]
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Check integrity
        cursor = conn.execute("PRAGMA integrity_check;")
        integrity_result = cursor.fetchone()[0]
        if integrity_result != "ok":
            errors.append(f"Integrity check failed: {integrity_result}")
        
        # Check required tables exist
        required_tables = [
            "workspaces",
            "cursor_rules",
            "integrations",
            "integration_types",
            "templates",
            "mcp_servers",
            "preferences",
            "action_log",
            "rules",
            "context",
            "domains",
            "checkpoints",
        ]
        
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        existing_tables = {row[0] for row in cursor.fetchall()}
        
        for table in required_tables:
            if table not in existing_tables:
                errors.append(f"Required table missing: {table}")
        
        # Check foreign key constraints
        cursor = conn.execute("PRAGMA foreign_key_check;")
        fk_errors = cursor.fetchall()
        if fk_errors:
            for error in fk_errors:
                errors.append(
                    f"Foreign key violation: {error[0]}.{error[1]} "
                    f"references {error[2]}.{error[3]}"
                )
        
        conn.close()
        
    except sqlite3.Error as e:
        errors.append(f"Database error: {e}")
    
    return len(errors) == 0, errors


def validate_data(db_path: Path) -> Tuple[bool, List[str]]:
    """Validate data consistency.
    
    Args:
        db_path: Path to database file
        
    Returns:
        Tuple of (is_valid, list of warnings)
    """
    warnings = []
    
    try:
        conn = sqlite3.connect(str(db_path))
        
        # Check for orphaned records
        cursor = conn.execute("""
            SELECT COUNT(*) FROM cursor_rules cr
            LEFT JOIN workspaces w ON cr.workspace_id = w.id
            WHERE w.id IS NULL AND cr.workspace_id IS NOT NULL
        """)
        orphaned_rules = cursor.fetchone()[0]
        if orphaned_rules > 0:
            warnings.append(f"Found {orphaned_rules} orphaned cursor_rules")
        
        cursor = conn.execute("""
            SELECT COUNT(*) FROM integrations i
            LEFT JOIN workspaces w ON i.workspace_id = w.id
            WHERE w.id IS NULL AND i.workspace_id IS NOT NULL
        """)
        orphaned_integrations = cursor.fetchone()[0]
        if orphaned_integrations > 0:
            warnings.append(f"Found {orphaned_integrations} orphaned integrations")
        
        conn.close()
        
    except sqlite3.Error as e:
        warnings.append(f"Data validation error: {e}")
    
    return len(warnings) == 0, warnings


def main():
    """Main validation function."""
    import os
    
    workspace_root = Path(__file__).parent.parent
    db_path = Path(os.getenv("DB_PATH", workspace_root / "dexter.db"))
    
    print(f"Validating database: {db_path}")
    print("-" * 60)
    
    # Schema validation
    schema_valid, schema_errors = validate_schema(db_path)
    if schema_valid:
        print("✓ Schema validation passed")
    else:
        print("✗ Schema validation failed:")
        for error in schema_errors:
            print(f"  - {error}")
    
    # Data validation
    data_valid, data_warnings = validate_data(db_path)
    if data_valid:
        print("✓ Data validation passed")
    else:
        print("⚠ Data validation warnings:")
        for warning in data_warnings:
            print(f"  - {warning}")
    
    print("-" * 60)
    
    if schema_valid and data_valid:
        print("Database validation successful!")
        return 0
    else:
        print("Database validation found issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
