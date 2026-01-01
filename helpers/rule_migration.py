"""
Migrate .mdc rule files to database.
Loads all rule files and stores them in rule_documents table.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, Optional

# Add workspace root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from helpers.db_helper import get_connection

RULES_DIR = Path(__file__).parent.parent / ".cursor" / "rules"


def parse_mdc_frontmatter(content: str) -> Dict[str, str]:
    """Parse frontmatter from .mdc file.
    
    Returns:
        dict: Parsed frontmatter and content
    """
    frontmatter = {}
    content_body = content
    
    # Check for frontmatter (--- delimited)
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter_text = parts[1].strip()
            content_body = parts[2].strip()
            
            # Parse key: value pairs
            for line in frontmatter_text.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    frontmatter[key.strip()] = value.strip().strip('"').strip("'")
    
    return {
        **frontmatter,
        "content": content_body
    }


def migrate_rules_to_database(workspace_id: Optional[int] = None) -> int:
    """Migrate all .mdc and .md rule files to database.
    
    Args:
        workspace_id: Optional workspace ID
        
    Returns:
        int: Number of rules migrated
    """
    if not RULES_DIR.exists():
        print(f"Rules directory not found: {RULES_DIR}")
        return 0
    
    migrated = 0
    
    with get_connection() as conn:
        for rule_file in RULES_DIR.glob("*.mdc"):
            migrate_file(conn, rule_file, workspace_id)
            migrated += 1
        
        for rule_file in RULES_DIR.glob("*.md"):
            migrate_file(conn, rule_file, workspace_id)
            migrated += 1
    
    return migrated


def migrate_file(conn, rule_file: Path, workspace_id: Optional[int]) -> None:
    """Migrate a single rule file to database."""
    content = rule_file.read_text(encoding='utf-8')
    parsed = parse_mdc_frontmatter(content)
    
    rule_name = rule_file.name
    title = parsed.get("description") or parsed.get("title") or rule_name.replace(".mdc", "").replace(".md", "")
    globs = parsed.get("globs", "")
    rule_type = parsed.get("ruleType") or parsed.get("rule_type", "always")
    content_body = parsed.get("content", content)
    
    conn.execute(
        """
        INSERT OR REPLACE INTO rule_documents 
        (workspace_id, rule_file, title, description, globs, rule_type, content, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (workspace_id, rule_name, title, title, globs, rule_type, content_body)
    )
    print(f"✓ Migrated: {rule_name}")


def get_rule_content(rule_file: str, workspace_id: Optional[int] = None) -> Optional[str]:
    """Get rule content from database.
    
    Args:
        rule_file: Name of rule file (e.g., 'core.mdc')
        workspace_id: Optional workspace ID
        
    Returns:
        str: Rule content, or None if not found
    """
    with get_connection() as conn:
        if workspace_id is not None:
            cursor = conn.execute(
                "SELECT content FROM rule_documents WHERE rule_file = ? AND workspace_id = ?",
                (rule_file, workspace_id)
            )
        else:
            cursor = conn.execute(
                "SELECT content FROM rule_documents WHERE rule_file = ? AND workspace_id IS NULL",
                (rule_file,)
            )
        row = cursor.fetchone()
        return row['content'] if row else None


def list_rules(workspace_id: Optional[int] = None) -> list:
    """List all rules in database.
    
    Args:
        workspace_id: Optional workspace ID
        
    Returns:
        list: List of rule documents
    """
    with get_connection() as conn:
        if workspace_id is not None:
            cursor = conn.execute(
                "SELECT rule_file, title, description, globs, rule_type FROM rule_documents WHERE workspace_id = ?",
                (workspace_id,)
            )
        else:
            cursor = conn.execute(
                "SELECT rule_file, title, description, globs, rule_type FROM rule_documents WHERE workspace_id IS NULL"
            )
        return [dict(row) for row in cursor.fetchall()]


if __name__ == "__main__":
    from helpers.db_helper import init_database, DB_PATH
    
    if not DB_PATH.exists():
        init_database()
    
    count = migrate_rules_to_database()
    print(f"\n✅ Migrated {count} rule files to database")
    
    # Show what's in database
    rules = list_rules()
    print(f"\nRules in database:")
    for rule in rules:
        print(f"  - {rule['rule_file']}: {rule['title']}")
