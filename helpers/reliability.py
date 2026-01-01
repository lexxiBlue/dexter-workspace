"""
Reliability enhancements for Dexter workspace.
Includes retry logic, rate limiting, safety checks, and error recovery.
"""

import time
import functools
import logging
import traceback
from typing import Callable, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    pass


class SafetyCheckFailed(Exception):
    """Raised when safety check fails."""
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
