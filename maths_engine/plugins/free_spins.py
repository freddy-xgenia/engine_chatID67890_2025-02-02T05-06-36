import logging
from typing import List
from maths_engine.configuration import Configuration
from maths_engine.state_manager import StateManager
from .base_plugin import BasePlugin


class FreeSpinsPlugin(BasePlugin):

    def __init__(
        self,
        config: Configuration,
        state_manager: StateManager,
        multiplier: int,
        icon: int,
        blocked_reels: List[int] = [0, 4]
    ):
        super().__init__(config, state_manager)
        # Initialize the logger
        self.logger = logging.getLogger(__name__)

        self.free_spins_symbol = icon
        self.free_spins_multiplier = multiplier
        self.blocked_reels = blocked_reels
        self.state_manager.set("current_free_spins", 0)
        self.state_manager.set("free_spins_lines", [])
        self.state_manager.set("free_spins_multiplier", multiplier)
        self.state_manager.set("total_free_spins_won",
                               0)  # Initialize total_free_spins_won
        # Store original reel weights to reset after free spins
        self.original_reel_weights = {
            reel_idx: config.get_reel_weights(reel_idx)
            for reel_idx in range(config.columns)
        }

    def before_spin(self):
        # Set the free spin mode based on the number of remaining free spins
        if self.state_manager.get("current_free_spins") > 0:
            self.state_manager.set("is_free_spin", True)
            # Adjust the weights of the reels for free spins
            self._adjust_reel_weights_for_free_spins()
        else:
            self.state_manager.set("is_free_spin", False)
            # Reset the weights to original state for normal spins
            self._reset_reel_weights()

    def after_spin(self):
        # Handle the detection of free spin symbols and awarding free spins
        self._increment_state_free_spins()
        is_free_spin = self.state_manager.get("is_free_spin")

        if is_free_spin:
            bet_amount = self.state_manager.get("bet_amount")
            capital = self.state_manager.get("capital") + bet_amount  # Refund the bet amount
            self.state_manager.set("capital", capital)

            total_bets = self.state_manager.get("total_bets") - bet_amount  # Remove bet amount from total bets
            self.state_manager.set("total_bets", total_bets)

            # Decrement the free spins if in free spin mode
            current_free_spins = self.state_manager.get("current_free_spins")
            if current_free_spins > 0:
                self.state_manager.set("current_free_spins",
                                       current_free_spins - 1)

    def _increment_state_free_spins(self):
        icon = self.free_spins_symbol
        reels = self.state_manager.get("engine_reels", [])

        free_spins_count = 0
        curr_free_spins_lines = []

        # Iterate over each row and symbol in the reels
        for reel_idx, reel in enumerate(reels):
            if reel_idx in self.blocked_reels:
                continue

            for line_idx, symbol in enumerate(reel):
                if symbol == icon:
                    free_spins_count += 1
                    curr_free_spins_lines.append({
                        "symbols": [symbol],
                        "positions": [(line_idx, reel_idx)]
                    })
                    """
                    Next line was incorrect.
                    Only one free spins symbol should appear within the same reel (game rules ClickUp) and not count 
                    only one for reel.
                    """
                    # break  # Only count one free spins symbol per reel

        self.state_manager.set("free_spins_count", free_spins_count)

        # Calculate the number of free spins to award
        won = 0
        is_free_spin = self.state_manager.get("is_free_spin")
        # Check if the spin is already a free spin to prevent re-triggering
        if is_free_spin:
            if free_spins_count >= 3:
                won = 10
            if free_spins_count == 1:
                won = 2
            if free_spins_count == 2:
                won = 4
        elif not is_free_spin:
            if free_spins_count >= 3:  # Assuming 3 symbols trigger free spins
                won = 10  # Example: Award 10 free spins

        # Update total and current free spins count
        self.state_manager.set("total_free_spins_won", self.state_manager.get("total_free_spins_won", 0) + won)  # FIXME: reespin number counter
        self.state_manager.set("current_free_spins", self.state_manager.get("current_free_spins", 0) + won)

        # Store the lines that triggered free spins
        free_spins_lines = self.state_manager.get("free_spins_lines")
        free_spins_lines.append(curr_free_spins_lines)
        self.state_manager.set("free_spins_lines", free_spins_lines)

    def _adjust_reel_weights_for_free_spins(self):
        """Adjust the weights of symbols on the reels to modify the chances of the free spins symbol appearing."""
        # Retrieve the slot machine engine from the state manager
        slot_machine_engine = self.state_manager.get("slot_machine_engine")
        if not slot_machine_engine:
            self.logger.error("SlotMachineEngine not found in state manager.")
            return

        for reel_idx in range(self.state_manager.get("config").columns):
            # Get the original weights to modify
            weights = self.original_reel_weights[reel_idx].copy()

            # If the reel is blocked, set the weight of the free spins symbol to 0
            if reel_idx in self.blocked_reels:
                weights[self.free_spins_symbol - 1] = 0  # Adjusting 1-based symbol to 0-based index
            # else:
            #     # Modify weights (e.g., increase the free spins symbol's weight)
            #     weights[self.free_spins_symbol -
            #             1] *= 2  # Double the weight of the free spins symbol

            # Use the slot machine engine to set the modified reel weights
            slot_machine_engine.set_reel_weights(reel_idx, weights)

    def _reset_reel_weights(self):
        """Reset the reel weights to their original state using the stored original weights."""
        # Retrieve the slot machine engine from the state manager
        slot_machine_engine = self.state_manager.get("slot_machine_engine")
        if not slot_machine_engine:
            self.logger.error("SlotMachineEngine not found in state manager.")
            return

        for reel_idx in range(self.state_manager.get("config").columns):
            # Reset weights to the original state
            original_weights = self.original_reel_weights[reel_idx]
            slot_machine_engine.set_reel_weights(reel_idx, original_weights)

    def nullify_payout_for_symbol(self, payout_override, symbol):
        """Set payout for a specific symbol to zero."""
        if payout_override is None:
            payout_override = {}

        payout_override[symbol] = 0
        return payout_override

    def get_results(self):
        return {
            "total_free_spins_won": self.state_manager.get("total_free_spins_won", 0),
            "current_free_spins": self.state_manager.get("current_free_spins", 0),
            "free_spins_detail": self.state_manager.get("free_spins_lines", 0)
        }


def init_plugin(config,
                state_manager: StateManager,
                multiplier: int,
                icon: int,
                blocked_reels: List[int] = [0, 4]):
    """Initialize the FreeSpinsPlugin plugin."""
    return FreeSpinsPlugin(config, state_manager, multiplier, icon,
                           blocked_reels)


def get_plugin_info():
    return {
        "name": "Free Spins",
        "description": "Adds free spins to the game.",
        "parameters": {
            "multiplier": {
                "type": "int",
                "default": 1,
                "description": "The multiplier for free spins winnings.",
            },
            "icon": {
                "type": "int",
                "default": None,
                "description": "The symbol that triggers free spins.",
            },
            "blocked_reels": {
                "type":
                "list",
                "default": [0, 4],
                "description":
                "Reels that are blocked from triggering free spins.",
            },
        },
    }
