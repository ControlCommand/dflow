# State machine rules for DFlow
# RFC-0003: State Transitions

VALID_STATES = [
    "INGRESS",
    "VALIDATED",
    "ACTIVE",
    "SCRATCH",
    "CURATED",
    "ARCHIVED",
    "REJECTED"
]

# Valid state transitions (strictly enforced)
TRANSITIONS = {
    "INGRESS": ["VALIDATED"],
    "VALIDATED": ["ACTIVE", "REJECTED"],
    "ACTIVE": ["CURATED", "SCRATCH"],
    "SCRATCH": ["ACTIVE", "REJECTED"],
    "CURATED": ["ARCHIVED", "ACTIVE"],
    "ARCHIVED": [],  # Terminal state
    "REJECTED": []   # Terminal state
}

def transition(action):
    """
    Given an action, return the resulting state.
    For now, actions map directly to states.
    """
    if action in VALID_STATES:
        return action
    return None

def is_valid_transition(from_state, to_state):
    """
    Check if a transition from from_state to to_state is valid.
    """
    if from_state not in TRANSITIONS:
        return False
    return to_state in TRANSITIONS[from_state]

def get_allowed_transitions(state):
    """Get list of allowed next states for a given state."""
    return TRANSITIONS.get(state, [])