"""
Integration example: Using agent brain with reliability decorators.
Shows how the agent uses database as its brain for decision-making.
"""

from helpers.reliability import require_verification
from helpers.agent_brain import record_decision, recall_similar_decisions
from helpers.agent_brain import (
    store_knowledge, recall_knowledge,
    record_pattern, recall_patterns,
    set_agent_state, get_agent_state
)


@require_verification
def agent_decision_with_brain(workspace_id: int, task: str):
    """Example: Agent making decision using its brain (database).
    
    The agent:
    1. Recalls similar past decisions
    2. Uses learned patterns
    3. Stores new knowledge
    4. Records the decision for future learning
    """
    # 1. Recall past similar decisions
    past_decisions = recall_similar_decisions(workspace_id, 'code_review')
    
    # 2. Recall relevant knowledge
    knowledge = recall_knowledge(workspace_id, topic='python')
    
    # 3. Recall successful patterns
    patterns = recall_patterns(workspace_id, pattern_type='success', min_success_rate=0.7)
    
    # 4. Make decision based on brain knowledge
    if patterns:
        # Use learned pattern
        decision = f"Following pattern: {patterns[0]['action_taken']}"
    elif knowledge:
        # Use stored knowledge
        decision = f"Applying knowledge: {knowledge[0]['fact']}"
    else:
        # Default decision
        decision = "Using default approach"
    
    # 5. Record decision for learning
    decision_id = record_decision(
        workspace_id=workspace_id,
        decision_type='code_review',
        decision=decision,
        input_context=task,
        reasoning=f"Based on {len(past_decisions)} past decisions and {len(knowledge)} facts"
    )
    
    # 6. Store new knowledge if successful
    store_knowledge(
        workspace_id=workspace_id,
        topic='decision_making',
        fact=f"Task '{task}' handled with: {decision}",
        source='agent_reasoning',
        confidence=0.8
    )
    
    return decision_id


# Example: Agent learning from outcomes
def agent_learns_from_outcome(decision_id: int, success: bool, outcome: str):
    """Agent learns from decision outcomes."""
    from helpers.agent_brain import update_decision_outcome, learn_from_decision
    
    # Update decision with outcome
    update_decision_outcome(decision_id, outcome, success)
    
    # Learn from the decision
    learn_from_decision(decision_id)
    
    # If successful, record as pattern
    if success:
        from helpers.agent_brain import record_pattern
        record_pattern(
            workspace_id=None,  # Global pattern
            pattern_name=f'successful_decision_{decision_id}',
            pattern_type='success',
            trigger_conditions=outcome,
            action_taken='Decision was successful'
        )
