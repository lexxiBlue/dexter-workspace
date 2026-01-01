"""Dexter workspace helpers package."""

from .db_helper import (
    init_database,
    create_workspace,
    get_workspace,
    list_workspaces,
    add_rule,
    get_rules,
    add_integration,
    get_integrations,
    get_preference,
    set_preference,
    get_template,
    list_templates,
    log_action,
    get_context,
    set_context,
)
from .workspace_generator import generate_workspace
from .integration_clients import get_client

# Reliability and validation modules (consolidated)
from . import reliability
from . import monitoring

__all__ = [
    # Database helpers
    "init_database",
    "create_workspace",
    "get_workspace",
    "list_workspaces",
    "add_rule",
    "get_rules",
    "add_integration",
    "get_integrations",
    "get_preference",
    "set_preference",
    "get_template",
    "list_templates",
    "log_action",
    "get_context",
    "set_context",
    # Workspace generation
    "generate_workspace",
    # Integration clients
    "get_client",
    # Reliability modules (consolidated)
    "reliability",
    "monitoring",
]
