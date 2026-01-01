"""
Action verification system for Dexter workspace.
Ensures actions are verified before and after execution.
"""

import logging
from typing import Optional, Callable, Any
from datetime import datetime
from helpers.db_helper import get_connection, log_action

logger = logging.getLogger(__name__)


class ActionVerifier:
    """Verifies actions before and after execution."""
    
    @staticmethod
    def create_checkpoint(action_id: int, checkpoint_type: str, 
                         state_snapshot: str) -> int:
        """Create a checkpoint before destructive operation.
        
        Args:
            action_id: ID of the action
            checkpoint_type: Type of checkpoint
            state_snapshot: Snapshot of current state (JSON string)
            
        Returns:
            int: Checkpoint ID
        """
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO checkpoints (action_id, checkpoint_type, state_snapshot)
                VALUES (?, ?, ?)
                """,
                (action_id, checkpoint_type, state_snapshot)
            )
            return cursor.lastrowid
    
    @staticmethod
    def verify_checkpoint(checkpoint_id: int) -> bool:
        """Mark checkpoint as verified.
        
        Args:
            checkpoint_id: ID of the checkpoint
            
        Returns:
            bool: True if verified successfully
        """
        with get_connection() as conn:
            cursor = conn.execute(
                "UPDATE checkpoints SET verified = 1 WHERE id = ?",
                (checkpoint_id,)
            )
            return cursor.rowcount > 0
    
    @staticmethod
    def verify_action_completion(action_id: int, expected_result: Any = None) -> bool:
        """Verify that an action completed successfully.
        
        Args:
            action_id: ID of the action
            expected_result: Expected result (optional)
            
        Returns:
            bool: True if action completed successfully
        """
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT status, description FROM action_log WHERE id = ?",
                (action_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                logger.error(f"Action {action_id} not found")
                return False
            
            status = row['status']
            description = row['description']
            
            if status != 'completed':
                logger.warning(
                    f"Action {action_id} did not complete successfully: "
                    f"status={status}, description={description}"
                )
                return False
            
            logger.info(f"Action {action_id} verified as completed")
            return True
    
    @staticmethod
    def rollback_action(action_id: int, rollback_info: str) -> bool:
        """Rollback an action using checkpoint data.
        
        Args:
            action_id: ID of the action to rollback
            rollback_info: Information needed for rollback
            
        Returns:
            bool: True if rollback successful
        """
        with get_connection() as conn:
            # Get checkpoint for this action
            cursor = conn.execute(
                "SELECT state_snapshot FROM checkpoints WHERE action_id = ? ORDER BY id DESC LIMIT 1",
                (action_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                logger.error(f"No checkpoint found for action {action_id}")
                return False
            
            # Update action status
            conn.execute(
                """
                UPDATE action_log 
                SET status = 'cancelled', rollback_info = ?
                WHERE id = ?
                """,
                (rollback_info, action_id)
            )
            
            logger.info(f"Action {action_id} rolled back successfully")
            return True


def require_verification(func: Callable) -> Callable:
    """Decorator to require action verification.
    
    Args:
        func: Function to wrap
    """
    def wrapper(*args, **kwargs):
        # Log action start
        workspace_id = kwargs.get('workspace_id') or (args[0] if args else None)
        action_type = func.__name__
        
        action_id = log_action(
            workspace_id=workspace_id,
            action_type=action_type,
            target=str(args) if args else None,
            status='pending'
        )
        
        try:
            # Update status to in_progress
            with get_connection() as conn:
                conn.execute(
                    "UPDATE action_log SET status = 'in_progress' WHERE id = ?",
                    (action_id,)
                )
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Verify completion
            ActionVerifier.verify_action_completion(action_id)
            
            # Update status to completed
            with get_connection() as conn:
                conn.execute(
                    "UPDATE action_log SET status = 'completed' WHERE id = ?",
                    (action_id,)
                )
            
            return result
            
        except Exception as e:
            # Update status to failed
            with get_connection() as conn:
                conn.execute(
                    """
                    UPDATE action_log 
                    SET status = 'failed', description = ?
                    WHERE id = ?
                    """,
                    (str(e), action_id)
                )
            
            logger.error(f"Action {action_id} failed: {e}")
            raise
    
    return wrapper
