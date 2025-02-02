import random

from maths_engine.plugins.free_spins import (
    FreeSpinsPlugin,
)

from .base_plugin import BasePlugin


class ScattersPlugin(BasePlugin):
    def __init__(self, config, state_manager):
        super().__init__(config, state_manager)
        self.scatter_symbols = config.get_plugin_param(
            "scatter_symbols", [9, 10]
        )  # Default scatter symbols
        self.scatter_trigger_count = config.get_plugin_param(
            "scatter_trigger_count", 3
        )  # How many scatters to trigger
        self.scatter_payout_multiplier = config.get_plugin_param(
            "scatter_payout_multiplier", 5
        )  # Multiplier for scatter payouts
        self.blocked_reels = config.get_plugin_param(
            "blocked_reels", [0, 1]
        )  # Reels where scatters can't appear (e.g., reel 1 and 2)
        self.scatter_positions = state_manager.get("scatter_positions", [])
        self.triggered = state_manager.get("triggered", False)
        self.scatter_count = state_manager.get("scatter_count", 0)
        self.free_spins_plugin = FreeSpinsPlugin(
            config, state_manager
        )  # Instantiate the FreeSpinsPlugin

    def block_scatters_on_reels(self, reels):
        """Ensure that scatter symbols do not appear on blocked reels."""
        for col in self.blocked_reels:  # Iterate over blocked reels
            for row in range(len(reels[col])):  # Iterate over rows in each blocked reel
                if reels[col][row] in self.scatter_symbols:
                    # Replace scatter with another symbol (example: replace with a random valid symbol)
                    reels[col][row] = self.get_random_non_scatter_symbol()
        return reels

    def get_random_non_scatter_symbol(self):
        """Return a random non-scatter symbol."""
        non_scatter_symbols = [
            sym
            for sym in range(1, self.config.symbols + 1)
            if sym not in self.scatter_symbols
        ]
        return random.choice(non_scatter_symbols)

    def count_scatters(self, reels):
        """Count scatter symbols in the current reels (excluding blocked reels)."""
        count = 0
        positions = []
        for col in range(len(reels)):  # Loop over columns
            if col in self.blocked_reels:
                continue  # Skip blocked reels
            for row in range(len(reels[col])):  # Loop over rows in each column
                if reels[col][row] in self.scatter_symbols:
                    count += 1
                    positions.append((col, row))
        return count, positions

    def handle_scatter_logic(self, engine):
        """Logic to be executed after the reels stop spinning."""
        # Ensure scatters are blocked on certain reels before counting them
        engine.reels = self.block_scatters_on_reels(engine.reels)

        # Count scatters in the current spin
        self.scatter_count, self.scatter_positions = self.count_scatters(engine.reels)

        # Check if scatter trigger condition is met
        if self.scatter_count >= self.scatter_trigger_count:
            self.triggered = True
            self.state_manager.set("triggered", self.triggered)
            self.state_manager.set("scatter_positions", self.scatter_positions)
            self.state_manager.set("scatter_count", self.scatter_count)
            print(
                f"Scatters triggered! Count: {self.scatter_count}, Positions: {self.scatter_positions}"
            )
            scatter_payout = self.scatter_payout(engine)

            # Trigger free spins
            print("Triggering Free Spins Feature...")
            self.free_spins_plugin.trigger_free_spins()

            return scatter_payout
        else:
            self.triggered = False
            self.state_manager.set("triggered", self.triggered)
            return 0

    def scatter_payout(self, engine):
        """Calculate the payout based on the scatter count."""
        payout = engine.bet_amount * self.scatter_payout_multiplier * self.scatter_count
        print(f"Scatter payout: {payout}")
        return payout

    def before_spin(self, engine):
        """Reset or prepare scatter logic before a new spin."""
        self.scatter_count = 0
        self.scatter_positions = []
        self.triggered = False
        self.state_manager.set("scatter_positions", [])
        self.state_manager.set("triggered", False)
        self.state_manager.set("scatter_count", 0)

    def after_spin(self, engine, spin_result):
        """Handle post-spin scatter logic and adjust results."""
        scatter_payout = self.handle_scatter_logic(engine)
        if scatter_payout > 0:
            spin_result["scatter_payout"] = scatter_payout

        # Preserve the line wins as calculated by the engine
        total_payout = scatter_payout + spin_result.get("line_payout", 0)
        spin_result["total_payout"] = total_payout
        return spin_result


def init_plugin(config, state_manager):
    """Initialize the ScattersPlugin plugin."""
    return ScattersPlugin(config, state_manager)


def get_plugin_info():
    return {
        "name": "Scatters",
        "description": "Triggers free spins and provides scatter payouts based on scatter symbols.",
        "parameters": {
            "scatter_symbols": {
                "type": "list",
                "default": [11, 12],
                "description": "List of scatter symbol IDs.",
            },
            "scatter_trigger_count": {
                "type": "int",
                "default": 3,
                "description": "Number of scatter symbols required to trigger the feature.",
            },
            "scatter_payout_multiplier": {
                "type": "int",
                "default": 5,
                "description": "Multiplier for scatter payouts.",
            },
            "blocked_reels": {
                "type": "list",
                "default": [0, 1],
                "description": "Reels where scatter symbols cannot appear.",
            },
        },
    }