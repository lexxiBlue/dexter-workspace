"""
Helper to load rules from database for agent context.
Replaces reading .mdc files directly.
"""

from typing import List, Dict, Optional
from helpers.db_helper import get_rule_documents


def load_rules_for_context(workspace_id: Optional[int] = None) -> str:
    """Load all rules from database formatted for agent context.
    
    Args:
        workspace_id: Optional workspace ID
        
    Returns:
        str: Formatted rules text for agent context
    """
    rules = get_rule_documents(workspace_id)
    
    if not rules:
        return "# No rules found in database\n"
    
    output = ["# Dexter Workspace Rules\n", "Loaded from database (rule_documents table)\n\n"]
    
    for rule in rules:
        output.append(f"## {rule['title']} ({rule['rule_file']})\n")
        if rule.get('description'):
            output.append(f"*{rule['description']}*\n")
        if rule.get('globs'):
            output.append(f"**Applies to:** {rule['globs']}\n")
        output.append("\n")
        output.append(rule['content'])
        output.append("\n\n---\n\n")
    
    return "".join(output)


def get_rule_by_file(rule_file: str, workspace_id: Optional[int] = None) -> Optional[Dict]:
    """Get a specific rule by filename.
    
    Args:
        rule_file: Rule filename (e.g., 'core.mdc')
        workspace_id: Optional workspace ID
        
    Returns:
        dict: Rule document or None
    """
    rules = get_rule_documents(workspace_id, rule_file)
    return rules[0] if rules else None
