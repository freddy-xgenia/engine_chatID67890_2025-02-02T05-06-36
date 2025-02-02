import logging

class StateManager:
    state: dict = {}

    def __init__(self, initial_state=None):
        self.state = initial_state if initial_state is not None else {}
        self.state['pending_actions'] = {}
        self.state['action_results'] = {}
        # Initialize critical keys if known
        self.state.setdefault('spin_winnings', 0)
        self.state.setdefault('bonus_multiplier', 1)
        self.state.setdefault('seed', 0)  # For Isaac RNG

    # Enable subscript-like access
    def __getitem__(self, key):
        value = self.state.get(key)
        if value is None:
            # Assign default values based on key
            default_values = {
                'spin_winnings': 0,
                'bonus_multiplier': 1,
                # Add other known keys and defaults
            }
            value = default_values.get(key, 0)
            logging.warning(f"Key '{key}' not found in state. Initializing to default value '{value}'.")
            self.state[key] = value
        return value

    def __setitem__(self, key, value):
        self.state[key] = value

    def __delitem__(self, key):
        if key in self.state:
            del self.state[key] 

    def add_pending_action(self, action):
        self.state['pending_actions'][action['id']] = action

    def complete_action(self, action_id, result):
        if action_id in self.state['pending_actions']:
            del self.state['pending_actions'][action_id]
            self.state['action_results'][action_id] = result

    def is_action_pending(self, action_id):
        return action_id in self.state['pending_actions']

    def get_pending_actions(self):
        return self.state['pending_actions']

    def has_pending_actions(self):
        return len(self.state['pending_actions']) > 0

    def get(self, key, default=None):
        """Retrieve a value from the state."""
        value = self.state.get(key, default)
        if value is None:
            return default
        return value

    def set(self, key, value):
        """Set a value in the state."""
        self.state[key] = value

    def update(self, updates):
        """Update multiple state values at once."""
        if not isinstance(updates, dict):
            raise ValueError("Updates must be provided as a dictionary.")
        self.state.update(updates)

    def reset(self):
        """Reset the state to an empty dictionary, including clearing actions."""
        self.state = {'pending_actions': {}, 'action_results': {}}

    def validate_state(self):
        """Perform any necessary validation on the state."""
        # Implement validation logic here, raise exceptions if the state is invalid
        pass

    def get_full_state(self):
        """Get the entire state dictionary."""
        return self.state

    def merge_state(self, external_state):
        """Merge an external state into the current state."""
        for key, value in external_state.items():
            if key in self.state and isinstance(self.state[key], dict):
                self.state[key].update(value)
            else:
                self.state[key] = value

    def all_actions_completed(self):
        """Check if all pending actions are completed."""
        return len(self.state['pending_actions']) == 0

    def set_expected_interactions(self, count):
        """Set the expected number of user interactions for this session."""
        self.state['expected_interactions'] = count
        self.state['current_interactions'] = 0

    def increment_interactions(self):
        """Increment the count of current interactions and check completion."""
        if 'current_interactions' in self.state:
            self.state['current_interactions'] += 1

    def interactions_completed(self):
        """Check if the number of current interactions matches the expected count."""
        return self.state.get('current_interactions', 0) >= self.state.get('expected_interactions', 0)
