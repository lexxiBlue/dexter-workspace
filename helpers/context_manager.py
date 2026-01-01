"""
Context management with automatic expiration cleanup.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from helpers.db_helper import get_connection, set_context, get_context

logger = logging.getLogger(__name__)


def cleanup_expired_contexts() -> int:
    """Remove expired context entries.
    
    Returns:
        int: Number of expired contexts removed
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            DELETE FROM context 
            WHERE expires_at IS NOT NULL 
            AND expires_at < datetime('now')
            """
        )
        deleted_count = cursor.rowcount
        logger.info(f"Cleaned up {deleted_count} expired context entries")
        return deleted_count


def set_context_with_ttl(workspace_id: Optional[int], key: str, value: str, 
                         ttl_seconds: int) -> None:
    """Set context with time-to-live.
    
    Args:
        workspace_id: ID of the workspace
        key: Context key
        value: Context value
        ttl_seconds: Time to live in seconds
    """
    expires_at = (datetime.now() + timedelta(seconds=ttl_seconds)).isoformat()
    set_context(workspace_id, key, value, expires_at)
    logger.debug(f"Set context {key} with TTL of {ttl_seconds}s")


def cleanup_old_actions(days: int = 30) -> int:
    """Remove old completed actions from action_log.
    
    Args:
        days: Number of days to keep actions
        
    Returns:
        int: Number of actions removed
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            DELETE FROM action_log 
            WHERE status = 'completed' 
            AND timestamp < datetime('now', '-' || ? || ' days')
            """,
            (days,)
        )
        deleted_count = cursor.rowcount
        logger.info(f"Cleaned up {deleted_count} old completed actions (older than {days} days)")
        return deleted_count


def get_context_stats(workspace_id: Optional[int] = None) -> dict:
    """Get context statistics.
    
    Args:
        workspace_id: Optional workspace ID to filter by
        
    Returns:
        dict: Statistics about context entries
    """
    with get_connection() as conn:
        if workspace_id:
            cursor = conn.execute(
                """
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at < datetime('now') THEN 1 END) as expired,
                    COUNT(CASE WHEN expires_at IS NULL THEN 1 END) as permanent
                FROM context
                WHERE workspace_id = ?
                """,
                (workspace_id,)
            )
        else:
            cursor = conn.execute(
                """
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN expires_at IS NOT NULL AND expires_at < datetime('now') THEN 1 END) as expired,
                    COUNT(CASE WHEN expires_at IS NULL THEN 1 END) as permanent
                FROM context
                """
            )
        
        row = cursor.fetchone()
        return {
            'total': row['total'],
            'expired': row['expired'],
            'permanent': row['permanent'],
            'active': row['total'] - row['expired']
        }
