import logging
from maths_engine.configuration import Configuration
from maths_engine.state_manager import StateManager
from maths_engine.plugins.base_plugin import BasePlugin


class MultiplierPlugin(BasePlugin):

    def __init__(self, config: Configuration, state_manager: StateManager,
                 multiplier: int):
        super().__init__(config, state_manager)
        # Initialize the logger
        self.logger = logging.getLogger(__name__)
        self.multiplier = multiplier  # Set the multiplier value
        self.state_manager.set("multiplier_effect_applied",
                               False)  # Keep track of multiplier application

    def before_spin(self):
        # Reset multiplier effect application state before each spin
        self.state_manager.set("multiplier_effect_applied", False)

    def after_spin(self):
        # Check if the spin had winnings
        spin_winnings = self.state_manager.get("spin_winnings", 0)
        if spin_winnings > 0:
            # Apply the multiplier effect
            self.state_manager.set("spin_winnings",
                                   spin_winnings * self.multiplier)
            self.state_manager.set("multiplier_effect_applied", True)
            # self.logger.info(
            #     f"Applied multiplier: {self.multiplier}x to winnings.")

    def get_results(self):
        # Return the results related to this plugin
        return {
            "multiplier_used":
            self.multiplier,
            "multiplier_effect_applied":
            self.state_manager.get("multiplier_effect_applied", False),
        }


def init_plugin(config: Configuration,
                state_manager: StateManager,
                multiplier: int = 2):
    """Initialize the MultiplierPlugin."""
    return MultiplierPlugin(config, state_manager, multiplier)


def get_plugin_info():
    return {
        "name": "Multiplier Plugin",
        "description": "Applies a multiplier to the winnings of each spin.",
        "parameters": {
            "multiplier": {
                "type": "int",
                "default": 2,
                "description": "The multiplier to apply to each winning spin.",
            }
        },
    }
