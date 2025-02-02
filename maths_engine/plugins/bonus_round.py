import logging
from typing import List
from maths_engine.configuration import Configuration
from maths_engine.state_manager import StateManager
from .base_plugin import BasePlugin

class BonusRoundPlugin(BasePlugin):
    def __init__(self, config, state_manager):
        super().__init__(config, state_manager)
        self.selections = []  # Stores user selections for the bonus round
        self.bonus_trigger_symbol = getattr(config, 'bonus_symbol', 10)
        self.bonus_rounds_triggered = 0  # Counter for how many times the bonus round was triggered

    def before_spin(self):
        # Reset selections before each spin
        self.selections = []

    def after_spin(self):
        # Access the reels' symbols to check for bonus triggering
        reels = self.state_manager.get("engine_reels", [])
        if self._is_bonus_triggered(reels):
            self.state_manager.add_pending_action({
                "id": "bonus_round",
                "plugin_name": "bonus_round",
                "type": "selection",
                "count": 2,  # Number of selections required
                "options": ["item1", "item2", "item3", "item4"]
            })
            self.bonus_rounds_triggered += 1
            # logging.info("Bonus round triggered! Waiting for user input...")


    def _is_bonus_triggered(self, reels):
        # Check if the bonus symbol is present in any reel
        for reel in reels:
            if self.bonus_trigger_symbol in reel:
                return True
        return False

    def get_pending_actions(self):
        # Return pending actions if any
        if self.state_manager.is_action_pending("bonus_round"):
            return {
                "bonus_round": {
                    "id": "bonus_round",
                    "plugin_name": "bonus_round",
                    "type": "selection",
                    "count": 2,  # Number of selections required
                    "options": ["item1", "item2", "item3", "item4"]
                }
            }
        return {}

    
    def handle_action(self, action):
        # Handle the user's selections during the bonus round
        if not self.state_manager.is_action_pending("bonus_round"):
            return {"error": "No bonus round pending"}

        # Process the selection
        self.selections.append(action['selected_item'])

        # Check if the bonus round is complete
        if len(self.selections) == 2:
            self.state_manager.complete_action("bonus_round", {"selections": self.selections})
            bonus_payout = self.calculate_bonus()
            current_spin_winnings = self.state_manager.get("spin_winnings") or 0
            self.state_manager.set("spin_winnings", current_spin_winnings + bonus_payout)
            # logging.info(f"Bonus round completed. Bonus payout: {bonus_payout}")
            return {"message": "Bonus round completed", "bonus_payout": bonus_payout}

        return {"message": "Selection received, waiting for next input"}

    def calculate_bonus(self):
        # Simple bonus calculation
        return 50  # Fixed bonus payout for demonstration

    def get_results(self):
        return {
            "bonus_rounds_triggered": self.bonus_rounds_triggered
        }
        

def init_plugin(config, state_manager, **params):
    return BonusRoundPlugin(config, state_manager)
