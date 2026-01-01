"""
Monitoring and health check utilities for Dexter workspace.
"""

import logging
import sqlite3
from typing import Dict, Any
from datetime import datetime
from pathlib import Path
from helpers.db_helper import get_connection, DB_PATH

logger = logging.getLogger(__name__)


def health_check() -> Dict[str, Any]:
    """Perform comprehensive health check of the system.
    
    Returns:
        dict: Health check results
    """
    results = {
        'timestamp': datetime.now().isoformat(),
        'database': _check_database(),
        'schema': _check_schema(),
        'performance': _check_performance(),
        'status': 'healthy'
    }
    
    # Determine overall status
    if any(check.get('status') != 'ok' for check in [results['database'], results['schema']]):
        results['status'] = 'degraded'
    if any(check.get('status') == 'error' for check in [results['database'], results['schema']]):
        results['status'] = 'unhealthy'
    
    return results


def _check_database() -> Dict[str, Any]:
    """Check database connectivity and integrity."""
    try:
        if not DB_PATH.exists():
            return {'status': 'error', 'message': 'Database file does not exist'}
        
        with get_connection() as conn:
            # Check integrity
            cursor = conn.execute("PRAGMA integrity_check;")
            integrity = cursor.fetchone()[0]
            
            if integrity != 'ok':
                return {'status': 'error', 'message': f'Database integrity check failed: {integrity}'}
            
            # Check foreign keys
            cursor = conn.execute("PRAGMA foreign_key_check;")
            fk_errors = cursor.fetchall()
            
            if fk_errors:
                return {'status': 'error', 'message': f'Foreign key violations: {len(fk_errors)}'}
            
            # Check file size
            file_size_mb = DB_PATH.stat().st_size / (1024 * 1024)
            
            return {
                'status': 'ok',
                'file_size_mb': round(file_size_mb, 2),
                'integrity': 'ok',
                'foreign_keys': 'ok'
            }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def _check_schema() -> Dict[str, Any]:
    """Check schema completeness."""
    required_tables = [
        'workspaces', 'cursor_rules', 'integrations', 'action_log',
        'rules', 'context', 'domains', 'checkpoints'
    ]
    
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            existing_tables = {row[0] for row in cursor.fetchall()}
            
            missing_tables = [t for t in required_tables if t not in existing_tables]
            
            if missing_tables:
                return {
                    'status': 'error',
                    'message': f'Missing tables: {missing_tables}'
                }
            
            # Check indexes
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
            )
            indexes = [row[0] for row in cursor.fetchall()]
            
            return {
                'status': 'ok',
                'tables': len(existing_tables),
                'indexes': len(indexes)
            }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def _check_performance() -> Dict[str, Any]:
    """Check database performance metrics."""
    try:
        with get_connection() as conn:
            # Check table sizes
            cursor = conn.execute("""
                SELECT name, 
                       (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=m.name) as row_count
                FROM sqlite_master m
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            
            # Get actual row counts
            tables = {}
            for row in cursor.fetchall():
                table_name = row[0]
                try:
                    count_cursor = conn.execute(f"SELECT COUNT(*) as cnt FROM {table_name}")
                    tables[table_name] = count_cursor.fetchone()['cnt']
                except:
                    tables[table_name] = 0
            
            # Check for large tables
            large_tables = {k: v for k, v in tables.items() if v > 10000}
            
            return {
                'status': 'ok',
                'table_counts': tables,
                'large_tables': large_tables,
                'total_tables': len(tables)
            }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def get_system_stats() -> Dict[str, Any]:
    """Get system statistics.
    
    Returns:
        dict: System statistics
    """
    try:
        with get_connection() as conn:
            stats = {}
            
            # Action log stats
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending
                FROM action_log
            """)
            stats['actions'] = dict(cursor.fetchone())
            
            # Workspace stats
            cursor = conn.execute("SELECT COUNT(*) as count FROM workspaces")
            stats['workspaces'] = cursor.fetchone()['count']
            
            # Context stats
            cursor = conn.execute("SELECT COUNT(*) as count FROM context")
            stats['context_entries'] = cursor.fetchone()['count']
            
            # Integration stats
            cursor = conn.execute("""
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN is_active = 1 THEN 1 END) as active
                FROM integrations
            """)
            stats['integrations'] = dict(cursor.fetchone())
            
            return stats
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return {'error': str(e)}
