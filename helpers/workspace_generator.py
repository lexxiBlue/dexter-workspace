"""
Dexter Workspace Generator
Generates Cursor IDE configuration files from database settings.
"""

import json
from pathlib import Path
from typing import Optional

try:
    from .db_helper import get_workspace, get_rules, get_integrations, get_preference
except ImportError:
    from db_helper import get_workspace, get_rules, get_integrations, get_preference


def generate_mdc_rule(rule: dict) -> str:
    """Generate .mdc rule file content."""
    globs = rule.get("globs", "")
    if globs:
        globs_line = f'globs: {json.dumps(globs.split(","))}'
    else:
        globs_line = 'globs: ["**/*"]'
    
    return f"""---
description: {rule.get("description", rule["rule_name"])}
{globs_line}
ruleType: {rule.get("rule_type", "always")}
---

{rule["content"]}
"""


def generate_cursorignore() -> str:
    """Generate .cursorignore file content."""
    return """# Dependencies
node_modules/
vendor/
.venv/
venv/
__pycache__/

# Build outputs
dist/
build/
*.log
*.pyc

# Secrets and environment
.env
.env.*
*.key
secrets/

# Large files
*.mp4
*.zip
*.tar.gz
data/

# IDE and system
.idea/
*.swp
.DS_Store
Thumbs.db

# Database
*.db
*.sqlite
"""


def generate_cursorindexignore() -> str:
    """Generate .cursorindexignore file content."""
    return """# Test fixtures
tests/fixtures/
__mocks__/

# Documentation (allow manual access)
docs/
*.md

# Compiled files
*.pyc
*.class
*.o
"""


def generate_vscode_settings() -> str:
    """Generate .vscode/settings.json content."""
    settings = {
        "editor.fontSize": 14,
        "editor.tabSize": int(get_preference("tab_size") or 4),
        "editor.formatOnSave": get_preference("format_on_save") == "true",
        "files.autoSave": "afterDelay" if get_preference("auto_save") == "true" else "off",
        "files.autoSaveDelay": 1000,
        "python.defaultInterpreterPath": "python3",
        "python.formatting.provider": "black",
        "[python]": {
            "editor.tabSize": 4
        }
    }
    return json.dumps(settings, indent=2)


def generate_cli_config() -> str:
    """Generate .cursor/cli-config.json content."""
    config = {
        "version": 1,
        "editor": {
            "vimMode": get_preference("vim_mode") == "true"
        },
        "permissions": {
            "allow": [
                "Shell(ls)",
                "Shell(cat)",
                "Shell(echo)",
                "Shell(python)",
                "Shell(pip)",
                "Shell(git)"
            ],
            "deny": [
                "Shell(rm -rf /)"
            ]
        }
    }
    return json.dumps(config, indent=2)


def generate_workspace(workspace_id: int, output_dir: Path):
    """Generate all workspace configuration files."""
    workspace = get_workspace(workspace_id)
    if not workspace:
        raise ValueError(f"Workspace {workspace_id} not found")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cursor_dir = output_dir / ".cursor"
    rules_dir = cursor_dir / "rules"
    vscode_dir = output_dir / ".vscode"
    
    rules_dir.mkdir(parents=True, exist_ok=True)
    vscode_dir.mkdir(parents=True, exist_ok=True)
    
    rules = get_rules(workspace_id)
    for rule in rules:
        rule_file = rules_dir / f"{rule['rule_name']}.mdc"
        rule_file.write_text(generate_mdc_rule(rule))
        print(f"Generated: {rule_file}")
    
    cursorignore = output_dir / ".cursorignore"
    cursorignore.write_text(generate_cursorignore())
    print(f"Generated: {cursorignore}")
    
    cursorindexignore = output_dir / ".cursorindexignore"
    cursorindexignore.write_text(generate_cursorindexignore())
    print(f"Generated: {cursorindexignore}")
    
    settings_file = vscode_dir / "settings.json"
    settings_file.write_text(generate_vscode_settings())
    print(f"Generated: {settings_file}")
    
    cli_config = cursor_dir / "cli-config.json"
    cli_config.write_text(generate_cli_config())
    print(f"Generated: {cli_config}")
    
    print(f"\nWorkspace '{workspace['name']}' generated at {output_dir}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python workspace_generator.py <workspace_id> <output_dir>")
        sys.exit(1)
    
    workspace_id = int(sys.argv[1])
    output_dir = Path(sys.argv[2])
    
    generate_workspace(workspace_id, output_dir)
