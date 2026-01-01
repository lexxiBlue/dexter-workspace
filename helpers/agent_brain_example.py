"""
Example: Using the agent brain as the agent's persistent memory.
"""

from helpers.agent_brain import (
    store_knowledge, recall_knowledge,
    record_decision, update_decision_outcome,
    record_pattern, recall_patterns,
    set_agent_state, get_agent_state,
    get_agent_intelligence
)


def example_agent_thinking():
    """Example of agent using database as brain."""
    workspace_id = 1
    
    # 1. Store learned facts
    store_knowledge(
        workspace_id=workspace_id,
        topic='code_style',
        fact='Always use type hints in Python functions',
        source='user_feedback',
        confidence=0.95
    )
    
    # 2. Recall knowledge when needed
    facts = recall_knowledge(workspace_id, topic='code_style')
    print(f"Agent recalls: {facts[0]['fact']}")
    
    # 3. Record decision-making process
    decision_id = record_decision(
        workspace_id=workspace_id,
        decision_type='refactoring',
        decision='Split large function into smaller ones',
        input_context='Function has 200+ lines',
        reasoning='Large functions are hard to maintain. Split improves readability.'
    )
    
    # 4. Update with outcome
    update_decision_outcome(
        decision_id=decision_id,
        outcome='Successfully refactored. Code is cleaner.',
        success=True
    )
    
    # 5. Learn patterns from success
    record_pattern(
        workspace_id=workspace_id,
        pattern_name='split_large_functions',
        pattern_type='success',
        trigger_conditions='Function > 150 lines',
        action_taken='Split into smaller functions'
    )
    
    # 6. Store agent state/preferences
    set_agent_state(
        workspace_id=workspace_id,
        state_key='preferred_style',
        state_value='minimal, functional',
        state_type='preference'
    )
    
    # 7. Recall agent's "personality"
    style = get_agent_state(workspace_id, 'preferred_style')
    print(f"Agent prefers: {style}")
    
    # 8. Get full intelligence summary
    intel = get_agent_intelligence(workspace_id)
    print(f"Agent knows {intel['knowledge_count']} facts")
    print(f"Agent has made {intel['decision_count']} decisions")
    print(f"Agent learned {intel['pattern_count']} patterns")


if __name__ == "__main__":
    example_agent_thinking()
