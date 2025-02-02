class BasePlugin:
    def __init__(self, config, state_manager):
        self.config = config
        self.state_manager = state_manager
        self.pending_action = False

    def before_spin(self):
        pass

    def after_spin(self):
        pass

    def get_actions(self):
        """Return a list of actions this plugin can trigger."""
        return []

    def handle_action(self, action):
        """Handle the given action."""
        pass

    def is_action_pending(self):
        """Return whether there is a pending action."""
        return self.pending_action

    def set_action_pending(self, pending=True):
        """Set the pending action state."""
        self.pending_action = pending

    def get_plugin_info(self):
        return {
            "name": "Base Plugin",
            "description": "A base class for all plugins.",
            "parameters": {}
        }