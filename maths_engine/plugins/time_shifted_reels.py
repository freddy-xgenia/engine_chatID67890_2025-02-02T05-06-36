# maths_engine/plugins/time_shifted_reels.py

import random
from datetime import datetime
from .base_plugin import BasePlugin

class TimeShiftedReels(BasePlugin):
    def __init__(self, config, state_manager):
        super().__init__(config, state_manager)
        self.reel_adjustment_time = config.get_plugin_param("reel_adjustment_time", "night")  # Example parameter
        self.player_behavior_influence = config.get_plugin_param("player_behavior_influence", True)

    def is_night_time(self):
        """Check if the current time is considered 'night'."""
        current_hour = datetime.now().hour
        return current_hour >= 20 or current_hour < 6  # Example: Night time is 8 PM to 6 AM

    def adjust_reels_based_on_time(self, reels):
        """Adjust reels based on the time of day."""
        if self.reel_adjustment_time == "night" and self.is_night_time():
            # Example: Convert certain symbols to wilds at night
            for col in range(self.config.columns):
                for row in range(self.config.rows):
                    if reels[col][row] == 2:  # Assuming symbol '2' changes at night
                        reels[col][row] = self.config.wild_symbol
        return reels

    def adjust_reels_based_on_player_behavior(self, reels):
        """Adjust reels based on player behavior."""
        player_spin_count = self.state_manager.get("player_spin_count", 0)
        if self.player_behavior_influence and player_spin_count > 50:
            # Example: After 50 spins, add an extra wild symbol
            col = random.randint(0, self.config.columns - 1)
            row = random.randint(0, self.config.rows - 1)
            reels[col][row] = self.config.wild_symbol
        return reels

    def before_spin(self, engine):
        """Modify the reels before the spin based on time-shifted dynamics."""
        reels = engine.reels
        reels = self.adjust_reels_based_on_time(reels)
        reels = self.adjust_reels_based_on_player_behavior(reels)
        engine.reels = reels

    def after_spin(self, engine, spin_result):
        """No additional logic needed after spin for this plugin."""
        return spin_result

def init_plugin(config, state_manager):
    """Initialize the TimeShiftedReels plugin."""
    return TimeShiftedReels(config, state_manager)

def get_plugin_info():
    return {
        "name": "Time Shifted Reels",
        "description": "Adjusts the reel outcomes based on time of day and player behavior.",
        "parameters": {
            "reel_adjustment_time": {
                "type": "str",
                "default": "night",
                "description": "Time of day when the reel adjustments take place."
            },
            "player_behavior_influence": {
                "type": "bool",
                "default": True,
                "description": "Whether player behavior influences the reel outcomes."
            }
        }
    }