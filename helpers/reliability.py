"""
Reliability enhancements and input validation for Dexter workspace.
Includes retry logic, rate limiting, safety checks, error recovery, action verification, and validation.
Consolidated for convenience - security blocks minimized.
"""

import time
import functools
import logging
import traceback
import re
import json
from typing import Callable, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps
from pathlib import Path

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    pass


class SafetyCheckFailed(Exception):
    """Raised when safety check fails."""
    pass


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class RateLimiter:
    """Rate limiter for API operations."""
    
    def __init__(self, max_calls: int, time_window: int):
        """Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = defaultdict(list)
    
    def check_limit(self, key: str) -> None:
        """Check if rate limit is exceeded.
        
        Args:
            key: Rate limit key (e.g., 'api_call', 'db_write')
            
        Raises:
            RateLimitError: If rate limit is exceeded
        """
        now = time.time()
        window_start = now - self.time_window
        
        # Remove old calls outside the window
        self.calls[key] = [call_time for call_time in self.calls[key] if call_time > window_start]
        
        # Check limit
        if len(self.calls[key]) >= self.max_calls:
            raise RateLimitError(
                f"Rate limit exceeded for '{key}': {self.max_calls} calls per {self.time_window}s"
            )
        
        # Record this call
        self.calls[key].append(now)


# Global rate limiters
_db_write_limiter = RateLimiter(max_calls=100, time_window=60)  # 100 writes per minute
_api_call_limiter = RateLimiter(max_calls=50, time_window=60)    # 50 API calls per minute


def retry_with_backoff(max_retries: int = 3, initial_delay: float = 1.0, 
                      backoff_factor: float = 2.0, exceptions: tuple = (Exception,)):
    """Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Factor to multiply delay by on each retry
        exceptions: Tuple of exceptions to catch and retry on
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}: {e}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


def require_safety_check(check_func: Optional[Callable] = None):
    """Decorator to require safety check before executing function.
    
    Args:
        check_func: Optional function to call for safety check
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check if this is a destructive operation
            func_name = func.__name__.lower()
            is_destructive = any(keyword in func_name for keyword in 
                                ['delete', 'remove', 'drop', 'truncate', 'clear'])
            
            if is_destructive:
                if check_func:
                    if not check_func(*args, **kwargs):
                        raise SafetyCheckFailed(
                            f"Safety check failed for {func.__name__}. Operation blocked."
                        )
                else:
                    # Default safety check: require explicit confirmation
                    logger.warning(
                        f"Destructive operation {func.__name__} requires explicit confirmation"
                    )
                    # In production, this would check for a confirmation flag
                    if not kwargs.get('confirm', False):
                        raise SafetyCheckFailed(
                            f"Destructive operation {func.__name__} requires 'confirm=True' parameter"
                        )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def rate_limit(limiter: RateLimiter, key: str):
    """Decorator to rate limit function calls.
    
    Args:
        limiter: RateLimiter instance
        key: Rate limit key
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            limiter.check_limit(key)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def verify_action_result(expected_result: Any = None, verify_func: Optional[Callable] = None):
    """Decorator to verify action results.
    
    Args:
        expected_result: Expected result value
        verify_func: Function to verify result
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            if verify_func:
                if not verify_func(result):
                    raise ValueError(f"Action result verification failed for {func.__name__}")
            elif expected_result is not None:
                if result != expected_result:
                    logger.warning(
                        f"Action {func.__name__} returned unexpected result: "
                        f"expected {expected_result}, got {result}"
                    )
            
            return result
        
        return wrapper
    return decorator


def log_execution_time(func: Callable) -> Callable:
    """Decorator to log function execution time.
    
    Args:
        func: Function to wrap
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"{func.__name__} executed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"{func.__name__} failed after {execution_time:.3f}s: {e}"
            )
            raise
    
    return wrapper


def validate_transaction(func: Callable) -> Callable:
    """Decorator to validate transaction before execution.
    
    Args:
        func: Function to wrap
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Check for required transaction context
        # This is a placeholder - implement based on your transaction management
        logger.debug(f"Validating transaction for {func.__name__}")
        return func(*args, **kwargs)
    
    return wrapper


class RecoveryStrategy:
    """Defines recovery strategies for different error types."""
    
    RETRY = "retry"
    ROLLBACK = "rollback"
    SKIP = "skip"
    FAIL = "fail"


def recover_from_error(strategy: str = RecoveryStrategy.FAIL, 
                       max_retries: int = 3,
                       initial_delay: float = 1.0,
                       backoff_factor: float = 2.0):
    """Decorator to recover from errors using specified strategy.
    
    Enhanced version that uses exponential backoff for retry strategy.
    
    Args:
        strategy: Recovery strategy (retry, rollback, skip, fail)
        max_retries: Maximum retry attempts (for retry strategy)
        initial_delay: Initial delay in seconds (for retry strategy)
        backoff_factor: Factor to multiply delay by on each retry
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_msg = f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}"
                    
                    if strategy == RecoveryStrategy.RETRY:
                        if attempt < max_retries:
                            logger.warning(f"{error_msg}. Retrying in {delay}s...")
                            time.sleep(delay)
                            delay *= backoff_factor
                            continue
                        else:
                            logger.error(f"{error_msg}. Max retries exceeded.")
                            raise
                    
                    elif strategy == RecoveryStrategy.ROLLBACK:
                        logger.error(f"{error_msg}. Attempting rollback...")
                        # Try to rollback if possible
                        try:
                            if 'action_id' in kwargs:
                                # ActionVerifier is now in this module
                                ActionVerifier.rollback_action(
                                    kwargs['action_id'],
                                    f"Error recovery rollback: {str(e)}"
                                )
                        except Exception as rollback_error:
                            logger.error(f"Rollback failed: {rollback_error}")
                        raise
                    
                    elif strategy == RecoveryStrategy.SKIP:
                        logger.warning(f"{error_msg}. Skipping operation.")
                        return None
                    
                    else:  # FAIL
                        logger.error(f"{error_msg}. Failing operation.")
                        raise
        
        return wrapper
    return decorator


def log_error_with_context(func: Callable) -> Callable:
    """Decorator to log errors with full context.
    
    Args:
        func: Function to wrap
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_context = {
                'function': func.__name__,
                'args': str(args),
                'kwargs': str(kwargs),
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            
            logger.error(
                f"Error in {func.__name__}: {e}\n"
                f"Context: {error_context}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            
            # Log to action_log if workspace_id is available
            workspace_id = kwargs.get('workspace_id') or (args[0] if args and isinstance(args[0], int) else None)
            if workspace_id:
                try:
                    from helpers.db_helper import log_action
                    log_action(
                        workspace_id=workspace_id,
                        action_type=f"error_{func.__name__}",
                        description=f"Error: {str(e)}",
                        status='failed'
                    )
                except Exception:
                    pass  # Don't fail on logging errors
            
            raise
    
    return wrapper


def validate_before_execute(validation_func: Callable) -> Callable:
    """Decorator to validate inputs before execution.
    
    Args:
        validation_func: Function to validate inputs
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                validation_func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Validation failed for {func.__name__}: {e}")
                raise ValueError(f"Input validation failed: {e}") from e
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


class ActionVerifier:
    """Verifies actions before and after execution (compliance/audit).
    
    Provides checkpoint and rollback capabilities for compliance tracking.
    """
    
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
        from helpers.db_helper import get_connection
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
        from helpers.db_helper import get_connection
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
        from helpers.db_helper import get_connection
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
        from helpers.db_helper import get_connection
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
    """Decorator to require action verification and audit logging (compliance).
    
    This decorator ensures all actions are logged to action_log for compliance/audit purposes.
    Security: Preserves all security checks while adding compliance tracking.
    
    Args:
        func: Function to wrap
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from helpers.db_helper import get_connection, log_action
        
        # Log action start (compliance requirement)
        workspace_id = kwargs.get('workspace_id') or (args[0] if args and isinstance(args[0], int) else None)
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
            
            # Verify completion (compliance check)
            ActionVerifier.verify_action_completion(action_id)
            
            # Update status to completed
            with get_connection() as conn:
                conn.execute(
                    "UPDATE action_log SET status = 'completed' WHERE id = ?",
                    (action_id,)
                )
            
            return result
            
        except Exception as e:
            # Update status to failed (compliance logging)
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


# Input validation functions (consolidated for convenience - minimal security blocks)
def validate_workspace_id(workspace_id: Any) -> int:
    """Validate workspace ID."""
    if not isinstance(workspace_id, int):
        try:
            workspace_id = int(workspace_id)
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid workspace_id: must be an integer, got {type(workspace_id)}")
    if workspace_id <= 0:
        raise ValidationError(f"Invalid workspace_id: must be positive, got {workspace_id}")
    return workspace_id


def validate_sql_query(query: str, allow_ddl: bool = False) -> str:
    """Validate SQL query - minimal checks for convenience."""
    if not isinstance(query, str):
        raise ValidationError("Query must be a string")
    # Only check for obvious dangerous patterns
    dangerous = ['DROP TABLE', 'TRUNCATE', 'DELETE FROM', '; DROP', '; DELETE']
    query_upper = query.upper()
    if not allow_ddl:
        dangerous.extend(['CREATE TABLE', 'ALTER TABLE', 'DROP '])
    for pattern in dangerous:
        if pattern in query_upper:
            raise ValidationError(f"Query contains dangerous pattern: {pattern}")
    return query


def validate_json(json_str: str, schema: Optional[dict] = None) -> dict:
    """Validate JSON string."""
    if not isinstance(json_str, str):
        raise ValidationError("JSON must be a string")
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON: {e}")
    if not isinstance(data, dict):
        raise ValidationError("JSON must be a dictionary")
    if schema:
        for key, expected_type in schema.items():
            if key not in data:
                continue
            if not isinstance(data[key], expected_type):
                raise ValidationError(f"JSON key '{key}' must be {expected_type.__name__}")
    return data


def validate_file_path(file_path: str, must_exist: bool = False, 
                      allowed_extensions: Optional[list] = None) -> Path:
    """Validate file path - minimal checks."""
    if not isinstance(file_path, str):
        raise ValidationError("File path must be a string")
    path = Path(file_path)
    if '..' in str(path):
        raise ValidationError("Path traversal detected")
    if allowed_extensions and path.suffix not in allowed_extensions:
        raise ValidationError(f"File extension must be one of {allowed_extensions}")
    if must_exist and not path.exists():
        raise ValidationError(f"File does not exist: {path}")
    return path


def validate_action_status(status: str) -> str:
    """Validate action status."""
    valid_statuses = ['pending', 'in_progress', 'completed', 'failed', 'cancelled']
    if status not in valid_statuses:
        raise ValidationError(f"Invalid status: must be one of {valid_statuses}")
    return status


def sanitize_string(value: str, max_length: Optional[int] = None, 
                   allow_newlines: bool = False) -> str:
    """Sanitize string input - minimal sanitization."""
    if not isinstance(value, str):
        raise ValidationError("Value must be a string")
    if allow_newlines:
        sanitized = ''.join(c for c in value if c.isprintable() or c == '\n')
    else:
        sanitized = ''.join(c for c in value if c.isprintable())
    if max_length and len(sanitized) > max_length:
        raise ValidationError(f"String exceeds maximum length of {max_length}")
    return sanitized.strip()


def validate_integration_type(integration_type: str) -> str:
    """Validate integration type."""
    valid_types = ['google_gmail', 'google_drive', 'google_sheets', 'google_appscript',
                   'hubspot', 'openai', 'tavily', 'github']
    if integration_type not in valid_types:
        raise ValidationError(f"Invalid integration_type: must be one of {valid_types}")
    return integration_type
