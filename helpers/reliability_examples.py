"""
Examples of using reliability features in Dexter workspace.
This file demonstrates best practices for AI reliability.
"""

from helpers.reliability import (
    validate_workspace_id,
    validate_sql_query,
    validate_json,
    sanitize_string,
    ValidationError,
)
from helpers.reliability import (
    retry_with_backoff,
    require_safety_check,
    rate_limit,
    log_execution_time,
    _db_write_limiter,
)
from helpers.reliability import require_verification, ActionVerifier
from helpers.reliability import recover_from_error, RecoveryStrategy, log_error_with_context
from helpers.utils import cleanup_expired_contexts, set_context_with_ttl


# Example 1: Validated database operation
@retry_with_backoff(max_retries=3, exceptions=(Exception,))
@log_execution_time
@log_error_with_context
def safe_create_workspace(name: str, description: str = ""):
    """Example of a safe workspace creation with validation."""
    # Validate inputs
    name = sanitize_string(name, max_length=100)
    description = sanitize_string(description, max_length=500, allow_newlines=True)
    
    # Rate limit database writes
    @rate_limit(_db_write_limiter, 'db_write')
    def _create():
        from helpers.db_helper import create_workspace
        return create_workspace(name, description)
    
    return _create()


# Example 2: Destructive operation with safety checks
@require_safety_check()
@require_verification
@recover_from_error(strategy=RecoveryStrategy.ROLLBACK)
def safe_delete_workspace(workspace_id: int, confirm: bool = False):
    """Example of safe workspace deletion."""
    # Validate workspace ID
    workspace_id = validate_workspace_id(workspace_id)
    
    # Safety check requires confirm=True
    if not confirm:
        raise ValueError("Deletion requires confirm=True")
    
    # Note: require_verification decorator automatically creates action_id
    # For checkpoint creation, you would use ActionVerifier.create_checkpoint()
    # after the action_id is available from the decorator
    
    # Perform deletion (implementation would go here)
    # This is just an example
    pass


# Example 3: SQL query with validation
def safe_query(query: str, params: tuple = ()):
    """Example of safe SQL query execution."""
    # Validate query
    validated_query = validate_sql_query(query, allow_ddl=False)
    
    # Execute query (implementation would go here)
    from helpers.db_helper import get_connection
    with get_connection() as conn:
        cursor = conn.execute(validated_query, params)
        return cursor.fetchall()


# Example 4: Context management with TTL
def set_temporary_context(workspace_id: int, key: str, value: str, ttl_minutes: int = 60):
    """Example of setting context with automatic expiration."""
    set_context_with_ttl(workspace_id, key, value, ttl_seconds=ttl_minutes * 60)


# Example 5: Cleanup job
def maintenance_cleanup():
    """Example maintenance cleanup job."""
    # Clean expired contexts
    expired_count = cleanup_expired_contexts()
    print(f"Cleaned up {expired_count} expired contexts")
    
    # Clean old actions (older than 30 days)
    from helpers.monitoring import cleanup_old_actions
    old_actions_count = cleanup_old_actions(days=30)
    print(f"Cleaned up {old_actions_count} old actions")


# Example 6: Health monitoring
def check_system_health():
    """Example health check."""
    from helpers.utils import health_check, get_system_stats
    
    health = health_check()
    stats = get_system_stats()
    
    print(f"System status: {health['status']}")
    print(f"Database: {health['database']['status']}")
    print(f"Schema: {health['schema']['status']}")
    print(f"Statistics: {stats}")
