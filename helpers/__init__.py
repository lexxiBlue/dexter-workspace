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
from .utils import generate_workspace, get_client

# Reliability and utility modules (consolidated)
from . import reliability
from . import utils

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
    # Workspace generation and integration clients (from utils)
    "generate_workspace",
    "get_client",
    # Reliability modules (consolidated)
    "reliability",
    "utils",
]
