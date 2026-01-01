"""
Agent Brain - Database-backed intelligence and memory system.
The database serves as the agent's persistent brain, storing knowledge, decisions, and learning.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from helpers.db_helper import get_connection

logger = logging.getLogger(__name__)


# Knowledge Management
def store_knowledge(workspace_id: Optional[int], topic: str, fact: str, 
                   source: Optional[str] = None, confidence: float = 1.0) -> int:
    """Store a fact in the agent's knowledge base.
    
    Args:
        workspace_id: Workspace ID
        topic: Topic/category of the fact
        fact: The fact to store
        source: Where this fact came from
        confidence: Confidence level (0.0 to 1.0)
        
    Returns:
        int: Knowledge ID
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO agent_knowledge (workspace_id, topic, fact, source, confidence)
            VALUES (?, ?, ?, ?, ?)
            """,
            (workspace_id, topic, fact, source, confidence)
        )
        return cursor.lastrowid


def recall_knowledge(workspace_id: Optional[int], topic: Optional[str] = None,
                    min_confidence: float = 0.5) -> List[Dict[str, Any]]:
    """Recall facts from the agent's knowledge base.
    
    Args:
        workspace_id: Workspace ID to filter by (None for global knowledge)
        topic: Optional topic to filter by
        min_confidence: Minimum confidence level
        
    Returns:
        list: List of knowledge entries
    """
    with get_connection() as conn:
        if topic:
            if workspace_id is not None:
                cursor = conn.execute(
                    """
                    SELECT * FROM agent_knowledge
                    WHERE workspace_id = ? AND topic = ? AND confidence >= ?
                    ORDER BY confidence DESC, usage_count DESC
                    """,
                    (workspace_id, topic, min_confidence)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM agent_knowledge
                    WHERE workspace_id IS NULL AND topic = ? AND confidence >= ?
                    ORDER BY confidence DESC, usage_count DESC
                    """,
                    (topic, min_confidence)
                )
        else:
            if workspace_id is not None:
                cursor = conn.execute(
                    """
                    SELECT * FROM agent_knowledge
                    WHERE workspace_id = ? AND confidence >= ?
                    ORDER BY confidence DESC, usage_count DESC
                    """,
                    (workspace_id, min_confidence)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM agent_knowledge
                    WHERE workspace_id IS NULL AND confidence >= ?
                    ORDER BY confidence DESC, usage_count DESC
                    """,
                    (min_confidence,)
                )
        return [dict(row) for row in cursor.fetchall()]


def update_knowledge_usage(knowledge_id: int) -> None:
    """Update knowledge usage statistics."""
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE agent_knowledge
            SET usage_count = usage_count + 1,
                last_used = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (knowledge_id,)
        )


# Decision Recording
def record_decision(workspace_id: Optional[int], decision_type: str, decision: str,
                   input_context: Optional[str] = None, reasoning: Optional[str] = None,
                   learned_from: Optional[int] = None) -> int:
    """Record a decision made by the agent.
    
    Args:
        workspace_id: Workspace ID
        decision_type: Type of decision (e.g., 'file_edit', 'query_execution')
        decision: The decision made
        input_context: Context that led to this decision
        reasoning: Agent's reasoning process
        learned_from: ID of previous decision this learned from
        
    Returns:
        int: Decision ID
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO agent_decisions (workspace_id, decision_type, input_context, 
                                       reasoning, decision, learned_from)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (workspace_id, decision_type, input_context, reasoning, decision, learned_from)
        )
        return cursor.lastrowid


def update_decision_outcome(decision_id: int, outcome: str, success: bool) -> None:
    """Update a decision with its outcome.
    
    Args:
        decision_id: ID of the decision
        outcome: What happened as a result
        success: Whether the decision was successful
    """
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE agent_decisions
            SET outcome = ?, success = ?
            WHERE id = ?
            """,
            (outcome, 1 if success else 0, decision_id)
        )


def recall_similar_decisions(workspace_id: Optional[int], decision_type: Optional[str] = None,
                             input_context: Optional[str] = None) -> List[Dict[str, Any]]:
    """Recall similar past decisions to learn from.
    
    Args:
        workspace_id: Workspace ID (None for global decisions)
        decision_type: Optional type of decision (use 'any' for all types)
        input_context: Context to match against
        
    Returns:
        list: Similar past decisions
    """
    with get_connection() as conn:
        if decision_type and decision_type != 'any':
            if workspace_id is not None:
                cursor = conn.execute(
                    """
                    SELECT * FROM agent_decisions
                    WHERE workspace_id = ? AND decision_type = ?
                    ORDER BY success DESC, created_at DESC
                    LIMIT 10
                    """,
                    (workspace_id, decision_type)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM agent_decisions
                    WHERE workspace_id IS NULL AND decision_type = ?
                    ORDER BY success DESC, created_at DESC
                    LIMIT 10
                    """,
                    (decision_type,)
                )
        else:
            if workspace_id is not None:
                cursor = conn.execute(
                    """
                    SELECT * FROM agent_decisions
                    WHERE workspace_id = ?
                    ORDER BY success DESC, created_at DESC
                    LIMIT 10
                    """,
                    (workspace_id,)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM agent_decisions
                    WHERE workspace_id IS NULL
                    ORDER BY success DESC, created_at DESC
                    LIMIT 10
                    """,
                )
        return [dict(row) for row in cursor.fetchall()]


# Pattern Learning
def record_pattern(workspace_id: Optional[int], pattern_name: str, pattern_type: str,
                  trigger_conditions: str, action_taken: str) -> int:
    """Record a learned pattern.
    
    Args:
        workspace_id: Workspace ID
        pattern_name: Name of the pattern
        pattern_type: Type (success, failure, optimization, warning)
        trigger_conditions: What conditions trigger this pattern
        action_taken: What action was taken
        
    Returns:
        int: Pattern ID
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO agent_patterns (workspace_id, pattern_name, pattern_type,
                                       trigger_conditions, action_taken)
            VALUES (?, ?, ?, ?, ?)
            """,
            (workspace_id, pattern_name, pattern_type, trigger_conditions, action_taken)
        )
        return cursor.lastrowid


def update_pattern_success(pattern_id: int, success: bool) -> None:
    """Update pattern success rate based on outcome.
    
    Args:
        pattern_id: ID of the pattern
        success: Whether using this pattern was successful
    """
    with get_connection() as conn:
        # Get current stats
        cursor = conn.execute(
            "SELECT success_rate, usage_count FROM agent_patterns WHERE id = ?",
            (pattern_id,)
        )
        row = cursor.fetchone()
        if row:
            current_rate = row['success_rate']
            count = row['usage_count']
            # Update success rate (moving average)
            new_rate = ((current_rate * count) + (1.0 if success else 0.0)) / (count + 1)
            conn.execute(
                """
                UPDATE agent_patterns
                SET success_rate = ?,
                    usage_count = usage_count + 1,
                    last_used = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (new_rate, pattern_id)
            )


def recall_patterns(workspace_id: Optional[int], pattern_type: Optional[str] = None,
                    min_success_rate: float = 0.0) -> List[Dict[str, Any]]:
    """Recall learned patterns.
    
    Args:
        workspace_id: Workspace ID (None for global patterns)
        pattern_type: Optional type filter
        min_success_rate: Minimum success rate
        
    Returns:
        list: Matching patterns
    """
    with get_connection() as conn:
        if pattern_type:
            if workspace_id is not None:
                cursor = conn.execute(
                    """
                    SELECT * FROM agent_patterns
                    WHERE workspace_id = ? AND pattern_type = ? AND success_rate >= ?
                    ORDER BY success_rate DESC, usage_count DESC
                    """,
                    (workspace_id, pattern_type, min_success_rate)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM agent_patterns
                    WHERE workspace_id IS NULL AND pattern_type = ? AND success_rate >= ?
                    ORDER BY success_rate DESC, usage_count DESC
                    """,
                    (pattern_type, min_success_rate)
                )
        else:
            if workspace_id is not None:
                cursor = conn.execute(
                    """
                    SELECT * FROM agent_patterns
                    WHERE workspace_id = ? AND success_rate >= ?
                    ORDER BY success_rate DESC, usage_count DESC
                    """,
                    (workspace_id, min_success_rate)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM agent_patterns
                    WHERE workspace_id IS NULL AND success_rate >= ?
                    ORDER BY success_rate DESC, usage_count DESC
                    """,
                    (min_success_rate,)
                )
        return [dict(row) for row in cursor.fetchall()]


# Agent State Management
def set_agent_state(workspace_id: Optional[int], state_key: str, state_value: str,
                   state_type: str = 'preference', expires_at: Optional[str] = None) -> None:
    """Set agent state/memory.
    
    Args:
        workspace_id: Workspace ID
        state_key: State key
        state_value: State value
        state_type: Type (preference, memory, goal, constraint)
        expires_at: Optional expiration timestamp
    """
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO agent_state (workspace_id, state_key, state_value, state_type, expires_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(workspace_id, state_key) DO UPDATE SET
                state_value = excluded.state_value,
                state_type = excluded.state_type,
                expires_at = excluded.expires_at,
                updated_at = CURRENT_TIMESTAMP
            """,
            (workspace_id, state_key, state_value, state_type, expires_at)
        )


def get_agent_state(workspace_id: Optional[int], state_key: str) -> Optional[str]:
    """Get agent state.
    
    Args:
        workspace_id: Workspace ID (None for global state)
        state_key: State key
        
    Returns:
        str: State value, or None if not found or expired
    """
    with get_connection() as conn:
        if workspace_id is not None:
            cursor = conn.execute(
                """
                SELECT state_value FROM agent_state
                WHERE workspace_id = ? AND state_key = ?
                AND (expires_at IS NULL OR expires_at > datetime('now'))
                """,
                (workspace_id, state_key)
            )
        else:
            cursor = conn.execute(
                """
                SELECT state_value FROM agent_state
                WHERE workspace_id IS NULL AND state_key = ?
                AND (expires_at IS NULL OR expires_at > datetime('now'))
                """,
                (state_key,)
            )
        row = cursor.fetchone()
        return row['state_value'] if row else None


def get_all_agent_state(workspace_id: Optional[int]) -> Dict[str, str]:
    """Get all agent state for a workspace.
    
    Args:
        workspace_id: Workspace ID (None for global state)
        
    Returns:
        dict: All state key-value pairs
    """
    with get_connection() as conn:
        if workspace_id is not None:
            cursor = conn.execute(
                """
                SELECT state_key, state_value FROM agent_state
                WHERE workspace_id = ?
                AND (expires_at IS NULL OR expires_at > datetime('now'))
                """,
                (workspace_id,)
            )
        else:
            cursor = conn.execute(
                """
                SELECT state_key, state_value FROM agent_state
                WHERE workspace_id IS NULL
                AND (expires_at IS NULL OR expires_at > datetime('now'))
                """
            )
        return {row['state_key']: row['state_value'] for row in cursor.fetchall()}


# Learning and Reasoning
def learn_from_decision(decision_id: int) -> None:
    """Learn from a decision outcome and update patterns/knowledge.
    
    Args:
        decision_id: ID of the decision to learn from
    """
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM agent_decisions WHERE id = ?",
            (decision_id,)
        )
        decision = cursor.fetchone()
        if not decision:
            return
        
        if decision['success']:
            # Extract successful patterns
            if decision['reasoning']:
                # Store as knowledge if reasoning was good
                store_knowledge(
                    workspace_id=decision['workspace_id'],
                    topic=decision['decision_type'],
                    fact=f"Successful approach: {decision['reasoning']}",
                    source=f"decision_{decision_id}",
                    confidence=0.8
                )
        else:
            # Learn from failures
            if decision['reasoning']:
                store_knowledge(
                    workspace_id=decision['workspace_id'],
                    topic=decision['decision_type'],
                    fact=f"Avoid: {decision['reasoning']} - led to failure",
                    source=f"decision_{decision_id}",
                    confidence=0.6
                )


def get_agent_intelligence(workspace_id: Optional[int]) -> Dict[str, Any]:
    """Get comprehensive agent intelligence summary.
    
    Args:
        workspace_id: Workspace ID
        
    Returns:
        dict: Intelligence summary
    """
    return {
        'knowledge_count': len(recall_knowledge(workspace_id)),
        'decision_count': len(recall_similar_decisions(workspace_id, 'any')),
        'pattern_count': len(recall_patterns(workspace_id)),
        'state_count': len(get_all_agent_state(workspace_id)),
        'top_patterns': recall_patterns(workspace_id, min_success_rate=0.7)[:5],
        'recent_decisions': recall_similar_decisions(workspace_id, 'any')[:5]
    }
