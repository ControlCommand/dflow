# State machine rules for DFlow
# RFC-0003: State Transitions

VALID_STATES = [
    "INGRESS",
    "ACTIVE",
    "SCRATCH",
    "CURATED",
    "ARCHIVE"
]

# Valid state transitions
TRANSITIONS = {
    "INGRESS": ["ACTIVE", "SCRATCH"],
    "ACTIVE": ["CURATED", "ARCHIVE"],
    "SCRATCH": ["ACTIVE", "ARCHIVE"],
    "CURATED": ["ARCHIVE", "ACTIVE"],
    "ARCHIVE": []  # Terminal state
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