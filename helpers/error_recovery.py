"""
Error recovery mechanisms for Dexter workspace.
"""

import logging
import traceback
from typing import Optional, Callable, Any
from functools import wraps
from helpers.db_helper import get_connection, log_action

logger = logging.getLogger(__name__)


class RecoveryStrategy:
    """Defines recovery strategies for different error types."""
    
    RETRY = "retry"
    ROLLBACK = "rollback"
    SKIP = "skip"
    FAIL = "fail"


def recover_from_error(strategy: str = RecoveryStrategy.FAIL, 
                       max_retries: int = 3):
    """Decorator to recover from errors using specified strategy.
    
    Args:
        strategy: Recovery strategy (retry, rollback, skip, fail)
        max_retries: Maximum retry attempts (for retry strategy)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            
            while attempt < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    error_msg = f"{func.__name__} failed (attempt {attempt}/{max_retries}): {e}"
                    
                    if strategy == RecoveryStrategy.RETRY:
                        if attempt < max_retries:
                            logger.warning(f"{error_msg}. Retrying...")
                            continue
                        else:
                            logger.error(f"{error_msg}. Max retries exceeded.")
                            raise
                    
                    elif strategy == RecoveryStrategy.ROLLBACK:
                        logger.error(f"{error_msg}. Attempting rollback...")
                        # Try to rollback if possible
                        try:
                            if 'action_id' in kwargs:
                                from helpers.action_verifier import ActionVerifier
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
    @wraps(func)
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
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                validation_func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Validation failed for {func.__name__}: {e}")
                raise ValueError(f"Input validation failed: {e}") from e
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
