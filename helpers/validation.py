"""
Input validation and sanitization helpers for Dexter workspace.
Enhances AI reliability by validating all inputs before processing.
"""

import re
import json
from typing import Any, Optional
from pathlib import Path


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_workspace_id(workspace_id: Any) -> int:
    """Validate workspace ID.
    
    Args:
        workspace_id: Workspace ID to validate
        
    Returns:
        int: Valid workspace ID
        
    Raises:
        ValidationError: If workspace_id is invalid
    """
    if not isinstance(workspace_id, int):
        try:
            workspace_id = int(workspace_id)
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid workspace_id: must be an integer, got {type(workspace_id)}")
    
    if workspace_id <= 0:
        raise ValidationError(f"Invalid workspace_id: must be positive, got {workspace_id}")
    
    return workspace_id


def validate_sql_query(query: str, allow_ddl: bool = False) -> str:
    """Validate SQL query for safety.
    
    Args:
        query: SQL query string
        allow_ddl: Whether to allow DDL statements (CREATE, DROP, ALTER)
        
    Returns:
        str: Validated query
        
    Raises:
        ValidationError: If query contains dangerous patterns
    """
    if not isinstance(query, str):
        raise ValidationError("Query must be a string")
    
    query_upper = query.upper().strip()
    
    # Dangerous patterns
    dangerous_patterns = [
        r'DROP\s+TABLE',
        r'DROP\s+DATABASE',
        r'TRUNCATE\s+TABLE',
        r'DELETE\s+FROM\s+\w+\s*(?:;|\s*$)',  # DELETE without WHERE
        r'UPDATE\s+\w+\s+SET\s+(?!.*WHERE)',  # UPDATE without WHERE
    ]
    
    if not allow_ddl:
        dangerous_patterns.extend([
            r'CREATE\s+TABLE',
            r'ALTER\s+TABLE',
            r'DROP\s+',
        ])
    
    for pattern in dangerous_patterns:
        if re.search(pattern, query_upper, re.IGNORECASE):
            raise ValidationError(f"Query contains dangerous pattern: {pattern}")
    
    # Check for SQL injection patterns
    injection_patterns = [
        r';\s*DROP',
        r';\s*DELETE',
        r';\s*UPDATE',
        r'--\s*$',
        r'/\*.*\*/',
        r'UNION\s+SELECT',
        r'EXEC\s*\(',
        r'EXECUTE\s*\(',
    ]
    
    for pattern in injection_patterns:
        if re.search(pattern, query_upper, re.IGNORECASE):
            raise ValidationError(f"Query contains potential SQL injection pattern: {pattern}")
    
    return query


def validate_json(json_str: str, schema: Optional[dict] = None) -> dict:
    """Validate JSON string.
    
    Args:
        json_str: JSON string to validate
        schema: Optional JSON schema for validation
        
    Returns:
        dict: Parsed JSON object
        
    Raises:
        ValidationError: If JSON is invalid or doesn't match schema
    """
    if not isinstance(json_str, str):
        raise ValidationError("JSON must be a string")
    
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON: {e}")
    
    if not isinstance(data, dict):
        raise ValidationError("JSON must be a dictionary")
    
    # Basic schema validation
    if schema:
        for key, expected_type in schema.items():
            if key not in data:
                continue
            if not isinstance(data[key], expected_type):
                raise ValidationError(
                    f"JSON key '{key}' must be {expected_type.__name__}, "
                    f"got {type(data[key]).__name__}"
                )
    
    return data


def validate_file_path(file_path: str, must_exist: bool = False, 
                      allowed_extensions: Optional[list] = None) -> Path:
    """Validate file path for safety.
    
    Args:
        file_path: File path to validate
        must_exist: Whether file must exist
        allowed_extensions: List of allowed file extensions (e.g., ['.py', '.sql'])
        
    Returns:
        Path: Validated Path object
        
    Raises:
        ValidationError: If path is invalid or unsafe
    """
    if not isinstance(file_path, str):
        raise ValidationError("File path must be a string")
    
    path = Path(file_path)
    
    # Check for path traversal attempts
    if '..' in str(path):
        raise ValidationError("Path traversal detected in file path")
    
    # Check for absolute paths outside workspace (if needed)
    # This is a basic check - adjust based on your security requirements
    
    # Check extension
    if allowed_extensions:
        if path.suffix not in allowed_extensions:
            raise ValidationError(
                f"File extension must be one of {allowed_extensions}, got {path.suffix}"
            )
    
    # Check existence
    if must_exist and not path.exists():
        raise ValidationError(f"File does not exist: {path}")
    
    return path


def validate_action_status(status: str) -> str:
    """Validate action status.
    
    Args:
        status: Status string to validate
        
    Returns:
        str: Validated status
        
    Raises:
        ValidationError: If status is invalid
    """
    valid_statuses = ['pending', 'in_progress', 'completed', 'failed', 'cancelled']
    
    if status not in valid_statuses:
        raise ValidationError(
            f"Invalid status: must be one of {valid_statuses}, got '{status}'"
        )
    
    return status


def sanitize_string(value: str, max_length: Optional[int] = None, 
                   allow_newlines: bool = False) -> str:
    """Sanitize string input.
    
    Args:
        value: String to sanitize
        max_length: Maximum length allowed
        allow_newlines: Whether to allow newline characters
        
    Returns:
        str: Sanitized string
        
    Raises:
        ValidationError: If string is invalid
    """
    if not isinstance(value, str):
        raise ValidationError("Value must be a string")
    
    # Remove control characters except newlines if allowed
    if allow_newlines:
        sanitized = ''.join(c for c in value if c.isprintable() or c == '\n')
    else:
        sanitized = ''.join(c for c in value if c.isprintable())
    
    # Check length
    if max_length and len(sanitized) > max_length:
        raise ValidationError(
            f"String exceeds maximum length of {max_length} characters"
        )
    
    return sanitized.strip()


def validate_integration_type(integration_type: str) -> str:
    """Validate integration type against known types.
    
    Args:
        integration_type: Integration type to validate
        
    Returns:
        str: Validated integration type
        
    Raises:
        ValidationError: If integration type is unknown
    """
    valid_types = [
        'google_gmail', 'google_drive', 'google_sheets', 'google_appscript',
        'hubspot', 'openai', 'tavily', 'github'
    ]
    
    if integration_type not in valid_types:
        raise ValidationError(
            f"Invalid integration_type: must be one of {valid_types}, got '{integration_type}'"
        )
    
    return integration_type
