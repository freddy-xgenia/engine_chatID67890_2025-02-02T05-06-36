# maths_engine/plugins/random_wild_modifier.py

import logging
import random

from maths_engine.configuration import Configuration
from maths_engine.state_manager import StateManager

from .base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class RandomWildModifierPlugin(BasePlugin):
    def __init__(
        self,
        config: Configuration,
        state_manager: StateManager,
    ):
        super().__init__(config, state_manager)
        self.num_wilds_to_add = config.get_plugin_param(
            "num_wilds_to_add", 3
        )  # Default to adding 3 wilds
        self.wild_symbol = config.get_plugin_param(
            "wild_symbol", config.wild_symbol
        )  # Default to the main wild symbol
        self.apply_multiplier = config.get_plugin_param("apply_multiplier", False)
        self.multiplier_value = config.get_plugin_param(
            "multiplier_value", 2
        )  # Default multiplier is 2x
        self.paytable = config.get_paytable(exclude=[self.config.free_spins_icon])

    def add_random_wilds(self):
        """Add a specified number of wilds to random positions on the reels."""
        reels = self.state_manager.get("engine_reels")
        for _ in range(self.num_wilds_to_add):
            col = random.randint(0, self.config.columns - 1)
            row = random.randint(0, self.config.rows - 1)
            reels[col][row] = self.wild_symbol

        self.state_manager.set("engine_reels", reels)

    def before_spin(self):
        """Modify the reels before the spin by adding random wilds."""
        self.add_random_wilds()

    def after_spin(self):
        """Optionally apply a multiplier to payouts if wilds contributed to the win."""
        self._calculate_winnings(is_applying_multiplier=self.apply_multiplier)

    def _calculate_winnings(self, is_applying_multiplier: bool = False):
        wild_total_winnings = 0
        confirmed_lines = self._check_wins(
            slot_results=self.state_manager.get("engine_reels")
        )
        for win_line in confirmed_lines:
            line_payout = self._check_payline(win_line)
            if line_payout > 0:
                current_line_win = (
                    line_payout * self.multiplier_value
                    if is_applying_multiplier
                    else line_payout
                )
                wild_total_winnings += current_line_win

        self.state_manager.set("spin_winnings", wild_total_winnings)
        return

    def _check_wins(self, slot_results: list) -> list:
        all_win_lines = []
        for line_index, line_v in enumerate(self.config.get_paylines()):
            line = []
            for idx, pos in enumerate(line_v):
                if isinstance(pos, tuple):
                    row, col = pos
                    if row >= len(slot_results) or col >= len(slot_results[0]):
                        continue
                    symbol = slot_results[row][col]
                    line.append(symbol)
                else:
                    logger.error(f"Expected tuple for position, got: {pos}")

            line_sequence = self._analyse_line_sequence(line)
            if line_sequence:
                all_win_lines.append([line_index, line_sequence])

        return all_win_lines

    def _check_payline(self, win_line) -> float:
        payout_multiplier = len(win_line[1])
        payout_symbol = self._exclude_free_spin_symbol(win_line[1])
        if (
            payout_symbol in self.paytable
            and payout_multiplier in self.paytable[payout_symbol]
        ):
            line_payout = (
                self.state_manager.get("bet_amount")
                * self.paytable[payout_symbol][payout_multiplier]
            )
            return line_payout
        return 0

    def _exclude_free_spin_symbol(self, num_list):
        """
        won't be used in the current implementation
        """
        for number in num_list:
            if number != self.state_manager.get("config").free_spins_icon:
                return number
        return None

    def _analyse_line_sequence(self, line: list) -> list | bool:
        if not line:
            return False

        primary_symbol = next(
            (sym for sym in line if sym != self.config.wild_symbol),
            self.config.wild_symbol,
        )
        matched_symbols = []
        count = 0

        for symbol in line:
            if symbol == primary_symbol or symbol == self.config.wild_symbol:
                count += 1
                matched_symbols.append(symbol)
            else:
                break

        if count >= 3:
            return matched_symbols
        else:
            return False


def init_plugin(
    config: Configuration,
    state_manager: StateManager,
) -> RandomWildModifierPlugin:
    """Initializes the RandomWildModifierPlugin plugin."""
    return RandomWildModifierPlugin(config, state_manager)


def get_plugin_info():
    return {
        "name": "Random Wild Modifier",
        "description": "Applies a random modifier to wild symbols, such as multipliers or stickiness.",
        "parameters": {
            "wild_symbol": {
                "type": "int",
                "default": 7,
                "description": "The symbol ID of the wild symbol.",
            },
            "wild_modifier_chance": {
                "type": "float",
                "default": 0.2,
                "description": "The probability of applying a wild modifier.",
            },
            "wild_modifier_type": {
                "type": "str",
                "default": "multiplier",
                "description": "The type of wild modifier to apply (multiplier or sticky).",
            },
            "wild_modifier_value": {
                "type": "int",
                "default": 2,
                "description": "The value of the wild modifier (multiplier value or sticky duration).",
            },
        },
    }
