"""
Rule management - sync between database and .cursor/rules/ files.
Consolidates rule migration and sync functionality.
Cursor IDE requires .mdc files to exist in .cursor/rules/ for auto-loading.
"""

import sys
from pathlib import Path
from typing import Optional, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

from helpers.db_helper import get_rule_documents, get_connection

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


def sync_rules_from_database(workspace_id: Optional[int] = None, dry_run: bool = False) -> int:
    """Sync rule files from database to .cursor/rules/ directory.
    
    Args:
        workspace_id: Optional workspace ID (None for global rules)
        dry_run: If True, only show what would be synced
        
    Returns:
        int: Number of files synced
    """
    if not RULES_DIR.exists():
        RULES_DIR.mkdir(parents=True, exist_ok=True)
    
    rules = get_rule_documents(workspace_id)
    synced = 0
    
    for rule in rules:
        rule_file = RULES_DIR / rule['rule_file']
        
        # Reconstruct frontmatter (only if not already present in content)
        content_body = rule['content']
        if not content_body.strip().startswith("---"):
            frontmatter_lines = ["---"]
            if rule.get('description'):
                frontmatter_lines.append(f"description: {rule['description']}")
            if rule.get('globs'):
                frontmatter_lines.append(f"globs: {rule['globs']}")
            if rule.get('rule_type'):
                frontmatter_lines.append(f"ruleType: {rule['rule_type']}")
            frontmatter_lines.append("---")
            frontmatter = "\n".join(frontmatter_lines) + "\n\n"
            content = frontmatter + content_body
        else:
            content = content_body
        
        if dry_run:
            print(f"Would sync: {rule['rule_file']}")
        else:
            rule_file.write_text(content, encoding='utf-8')
            print(f"✓ Synced: {rule['rule_file']}")
            synced += 1
    
    return synced


def sync_rules_to_database(workspace_id: Optional[int] = None) -> int:
    """Sync rule files from .cursor/rules/ to database.
    Useful for initial migration or when files are edited manually.
    
    Args:
        workspace_id: Optional workspace ID
        
    Returns:
        int: Number of files synced
    """
    if not RULES_DIR.exists():
        print(f"Rules directory not found: {RULES_DIR}")
        return 0
    
    migrated = 0
    
    with get_connection() as conn:
        for rule_file in RULES_DIR.glob("*.mdc"):
            _migrate_file(conn, rule_file, workspace_id)
            migrated += 1
        
        for rule_file in RULES_DIR.glob("*.md"):
            _migrate_file(conn, rule_file, workspace_id)
            migrated += 1
    
    return migrated


def _migrate_file(conn, rule_file: Path, workspace_id: Optional[int]) -> None:
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


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync rules between database and files")
    parser.add_argument("--to-files", action="store_true", help="Sync from database to .mdc files")
    parser.add_argument("--to-db", action="store_true", help="Sync from .mdc files to database")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be synced")
    
    args = parser.parse_args()
    
    if args.to_files:
        count = sync_rules_from_database(dry_run=args.dry_run)
        print(f"\n✅ Synced {count} rules from database to files")
    elif args.to_db:
        count = sync_rules_to_database()
        print(f"\n✅ Synced {count} rules from files to database")
    else:
        print("Use --to-files or --to-db")
        print("Example: python helpers/rule_sync.py --to-files")
