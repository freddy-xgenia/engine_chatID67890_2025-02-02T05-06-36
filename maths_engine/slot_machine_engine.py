import logging
import os
import sys
import inspect
import numpy as np

from maths_engine.isaac_rng_v2 import Isaac
from maths_engine.plugin_manager import PluginManager

from maths_engine.state_manager import StateManager
from typing import Optional

logger = logging.getLogger(__name__)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class SlotMachineEngine:

    def __init__(
        self,
        config,
        state_manager: StateManager,
        plugin_manager=None,
        plugins_with_params=None,
    ):  # Accept `plugins_with_params` as an argument
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.plugin_manager = plugin_manager or PluginManager(config)
        self.state_manager = state_manager
        self.state_manager.set("engine_lines", [])
        self.paytable = config.get_paytable(exclude=[self.config.wild_symbol])
        self.paylines = config.get_paylines()
        self.errors = []
        self.free_spins = 0
        self.current_free_spin_winnings = 0
        self.free_spin_round_end = False
        self.free_spin_total_winnings = 0
        self.total_free_spins_won = 0
        self.current_total_winnings = 0
        self.current_reels = []
        self.winning_lines = []
        self.rng = Isaac(self.state_manager)

        self.reel_weights = {
            i: config.get_symbol_weights()
            for i in range(config.columns)
        }  # Store reel weights for modification

        if plugins_with_params is not None:
            self.plugin_manager.load_plugins(
                plugins_with_params)  # Pass `plugins_with_params`

        # logger.info({
        #     "message": "SlotMachineEngine initialized.",
        #     "config": self.config.__dict__,
        #     "paytable": self.paytable,
        # })

    def pre_spin(self, icon = Optional, blocked_reels = Optional):
        self.rng = Isaac(self.state_manager)
        reels_from_rng = self.get_weighted_reels(self.rng, icon, blocked_reels)
        # reels_from_rng = [[2, 3, 4], [5, 9, 6], [8, 10, 2], [2, 10, 6], [3, 1, 7]]



        self.state_manager.set("engine_reels", reels_from_rng)
        self.lines = self.convert_reels_to_lines(
            reels=self.state_manager.get("engine_reels"))

    def spin(self, bet_amount) -> None:
        """
        spin - Simulate a spin of the slot machine.

        Args:
            bet_amount (float): The amount to bet on the spin.
        Returns:
            None
        """

        # bet_amount = bet_amount/100

        self.bet_amount = bet_amount
        self.state_manager.set("bet_amount", bet_amount)

        if self.state_manager.get("demo_params") is not None:
            self.state_manager.set(
                "engine_reels",
                self.state_manager.get("demo_params").get("custom_reels"),
            )
            self.lines = self.convert_reels_to_lines(
                reels=self.state_manager.get("engine_reels"))
            self._update_state()
            self.state_manager.set("spin_winnings", self.calculate_winnings())
            return

        self.lines = self.convert_reels_to_lines(
            reels=self.state_manager.get("engine_reels"))
        self._update_state()
        self.state_manager.set("spin_winnings", self.calculate_winnings())

    @staticmethod
    def convert_reels_to_lines(reels: list) -> list[list]:
        reels_arr = np.array(reels)
        reels_transformed = reels_arr.T
        lines = reels_transformed.tolist()
        return lines

    def set_reel_weights(self, reel_idx, weights):
        """Set custom weights for a specific reel."""
        if reel_idx < 0 or reel_idx >= self.config.columns:
            raise ValueError(f"Invalid reel index: {reel_idx}")
        if len(weights) != self.config.symbols:
            raise ValueError(
                f"Weight length must match the number of symbols: {self.config.symbols}"
            )
        self.reel_weights[reel_idx] = weights

    # def get_weighted_reels(self, rng, icon = Optional):
    #     """Select symbols for each reel using custom weighted selection with Isaac RNG."""
    #     reels = []
    #     for reel_idx in range(self.config.columns):
    #         reel_symbols = []
    #         # Use the potentially modified weights for the current reel
    #         weights = self.reel_weights[reel_idx]
    #         symbols = list(range(1, self.config.symbols +
    #                              1))  # Assuming symbols are 1 to N
    #         cumulative_weights = self._calculate_cumulative_weights(weights)
    #         for _ in range(self.config.rows):
    #             chosen_symbol = self._select_symbol_with_weights(
    #                 rng, symbols, cumulative_weights, icon)
    #             reel_symbols.append(chosen_symbol)
    #         reels.append(reel_symbols)
    #     print("final reels : ", reels)
    #     return reels

    # def get_weighted_reels(self, rng, icon=Optional, blocked_reels=None):
    #     """Select symbols for each reel using custom weighted selection with Isaac RNG, blocking specific icons on certain reels."""
    #     reels = []
    #
    #     # If blocked_reels is not provided, initialize as an empty list
    #     blocked_reels = blocked_reels if blocked_reels is not None else []
    #     from icecream import ic
    #     for reel_idx in range(self.config.columns):
    #         reel_symbols = []
    #         weights = self.reel_weights[reel_idx].copy()  # Copy to avoid mutating original weights
    #         symbols = list(range(1, self.config.symbols + 1))  # Assuming symbols are 1 to N
    #         ic(symbols)
    #         # Block the wild symbol on the first reel (reel_idx 0)
    #         if reel_idx == 0 and self.config.wild_symbol in symbols:
    #             wild_index = symbols.index(self.config.wild_symbol)
    #             # Set the weight of the wild symbol to zero on the first reel
    #             weights[wild_index] = 0
    #
    #             # Optional: remove the wild symbol from the list entirely on the first reel
    #             symbols.pop(wild_index)
    #             weights.pop(wild_index)
    #
    #         # Check if the current reel index is in blocked_reels and needs to exclude the icon
    #         if reel_idx in blocked_reels and icon in symbols:
    #             icon_index = symbols.index(icon)
    #             # Set the weight of the blocked icon to zero to exclude it entirely on this reel
    #             weights[icon_index] = 0
    #
    #             # If you want to fully remove the symbol instead of zeroing its weight:
    #             symbols.pop(icon_index)
    #             weights.pop(icon_index)
    #
    #         # Calculate cumulative weights based on the updated symbol list and modified weights
    #         cumulative_weights = self._calculate_cumulative_weights(weights)
    #
    #         for _ in range(self.config.rows):
    #             chosen_symbol = self._select_symbol_with_weights(
    #                 rng, symbols, cumulative_weights, icon)
    #             reel_symbols.append(chosen_symbol)
    #
    #         reels.append(reel_symbols)
    #     return reels

    def get_weighted_reels(self, rng, icon=Optional, blocked_reels=None):
        """Select symbols for each reel using custom weighted selection with Isaac RNG, blocking specific icons on certain reels."""
        reels = []

        # If blocked_reels is not provided, initialize as an empty list
        blocked_reels = blocked_reels if blocked_reels is not None else []

        for reel_idx in range(self.config.columns):
            reel_symbols = []
            weights = self.reel_weights[reel_idx].copy()  # Copy to avoid mutating original weights
            symbols = list(range(1, self.config.symbols + 1))  # Assuming symbols are 1 to N

            # Block the wild symbol on the first reel (reel_idx 0)
            if reel_idx == 0 and self.config.wild_symbol in symbols:
                wild_index = symbols.index(self.config.wild_symbol)
                # Set the weight of the wild symbol to zero on the first reel
                weights[wild_index] = 0

                # Optional: remove the wild symbol from the list entirely on the first reel
                symbols.pop(wild_index)
                weights.pop(wild_index)

            # Check if the current reel index is in blocked_reels and needs to exclude the icon
            if reel_idx in blocked_reels and icon in symbols:
                icon_index = symbols.index(icon)
                # Set the weight of the blocked icon to zero to exclude it entirely on this reel
                weights[icon_index] = 0

                # If you want to fully remove the symbol instead of zeroing its weight:
                symbols.pop(icon_index)
                weights.pop(icon_index)

            # Calculate cumulative weights based on the updated symbol list and modified weights
            cumulative_weights = self._calculate_cumulative_weights(weights)

            for _ in range(self.config.rows):
                # Select a symbol, but only allow '10' to appear once per reel
                chosen_symbol = self._select_symbol_with_weights(
                    rng, symbols, cumulative_weights, icon
                )
                reel_symbols.append(chosen_symbol)

                # If '10' is selected, remove it from symbols and weights to prevent further selection
                if chosen_symbol == 10 and 10 in symbols:  # FIXME: With this implementation, the symbol 10 will appear at most once per reel during the selection process. Should be changed to now overwrite 10 symbol.
                    index_10 = symbols.index(10)
                    symbols.pop(index_10)
                    weights.pop(index_10)

                    # Recalculate cumulative weights after modifying the symbol pool
                    cumulative_weights = self._calculate_cumulative_weights(weights)

            reels.append(reel_symbols)

        return reels

    @staticmethod
    def _calculate_cumulative_weights(weights):
        """Calculate cumulative weights for selection."""
        cumulative_weights = []
        total = 0
        for weight in weights:
            total += weight
            cumulative_weights.append(total)
        return cumulative_weights

    @staticmethod
    def _select_symbol_with_weights(rng, symbols, cumulative_weights, icon= Optional):
        """Select a symbol based on weights using Isaac RNG."""
        total_weight = cumulative_weights[-1]
        rand_value = rng.rand(mod=total_weight, icon=icon)

        for i, cumulative_weight in enumerate(cumulative_weights):
            if rand_value <= cumulative_weight:
                return symbols[i]

        return symbols[-1]  # Fallback in case of rounding errors

    def calculate_winnings(self):
        # self.logger.debug("Calculating winnings.")
        from icecream import ic
        self.current_total_winnings = 0
        self.state_manager.set("engine_lines", self.lines)
        confirmed_lines = self.check_wins(
            slot_results=self.state_manager.get("engine_reels"))
        for win_line in confirmed_lines:
            line_payout = self.check_payline(win_line)
            # going back to the cents version
            # if isinstance(line_payout, int):
            #     line_payout = line_payout * 100
            # elif isinstance(line_payout, float) and line_payout.is_integer():
            #     line_payout = int(round(line_payout) * 100)
            # else:
            #     line_payout = int(round(line_payout * 100))

            if line_payout > 0:
                self.current_total_winnings += line_payout
                from icecream import ic
                self.winning_lines.append({
                    "line":
                    win_line[0],
                    "symbols":
                    win_line[1],
                    "positions":
                    self.calculate_symbols_position(win_line),
                    "payout":
                    line_payout,
                })

        return self.current_total_winnings

    async def spin_once(self, bet_amount: float):
        # self.logger.debug("Spin once initiated.")
        self.bet_amount = bet_amount

        total_payout = 0
        all_winning_lines = [[]]

        progressive_jackpot = 0

        self.state_manager.set("engine_reels", self.config.get_reels())
        all_payline_results = self.convert_reels_to_lines(
            reels=self.state_manager.get("engine_reels"))
        confirmed_lines = self.check_wins(slot_results=all_payline_results)

        for win_line in confirmed_lines:
            line_payout = self.check_payline(win_line)
            all_winning_lines[0].append({
                "line": win_line[0],
                "symbols": win_line[1],
                "positions": self.calculate_symbols_position(win_line),
                "payout": line_payout,
            })
            total_payout += line_payout

        return all_payline_results, progressive_jackpot, all_winning_lines, total_payout

    logging.basicConfig(level=logging.DEBUG)

    def check_wins(self, slot_results: list) -> list:
        all_win_lines = []
        wild_symbol = self.config.wild_symbol  # Define the wild symbol
        scatter_symbol = self.state_manager.get("icon")  # Define the scatter symbol

        # Get the number of rows and columns
        num_rows = len(slot_results[0])  # Assuming at least one column exists
        num_cols = len(slot_results)      # Number of columns is the length of the outer array

        for line_index, line_v in enumerate(self.paylines):
            line = []
            for idx, pos in enumerate(line_v):
                if isinstance(pos, tuple):
                    col, row = pos  # Switch to col, row format
                    if row >= num_rows or col >= num_cols:
                        error_msg = (f"Index out of range: row={row}, col={col}, "
                                    f"slot_results dimensions={num_rows}x{num_cols}")
                        self.errors.append(error_msg)
                        logging.error(error_msg)
                        continue
                    symbol = slot_results[col][row]  # Access using [col][row]
                    line.append(symbol)
                else:
                    logging.error(f"Expected tuple for position at index {idx}, got: {pos}")

            # Refined condition to allow winning lines with wild and scatter if wild contributes to win
            if wild_symbol in line and scatter_symbol in line:
                # Check if scatter symbol interferes with potential win
                scatter_index = line.index(scatter_symbol)
                win_possible = any(
                    line[i] == wild_symbol or (line[i] == line[0] and line[0] != scatter_symbol)
                    for i in range(min(scatter_index, 3))  # Check only the symbols up to the scatter position
                )
                if not win_possible:
                    logging.info(f"Skipping line {line_index} due to scatter symbol interference.")
                    continue

            # Skip lines consisting entirely of wild or scatter symbols
            if all(symbol == wild_symbol for symbol in line):
                logging.info(f"Skipping line {line_index} because it consists entirely of wild symbols.")
                continue

            if all(symbol == scatter_symbol for symbol in line):
                logging.info(f"Skipping line {line_index} because it consists entirely of scatter symbols.")
                continue

            # Process the line for win logic
            first_non_wild_symbol = None
            is_win = True
            longest_win_line = []  # To store the longest matching line

            for i, symbol in enumerate(line):
                if symbol != wild_symbol:
                    if first_non_wild_symbol is None:
                        first_non_wild_symbol = symbol  # Set the first non-wild symbol
                    elif symbol != first_non_wild_symbol:
                        is_win = False
                        break

                # Store the longest win line based on the current symbol index
                if i == 2 and is_win:  # 3-symbol win
                    longest_win_line = line[:3]
                if i == 3 and is_win:  # 4-symbol win
                    longest_win_line = line[:4]
                if i == 4 and is_win:  # 5-symbol win
                    longest_win_line = line

            if longest_win_line:
                all_win_lines.append([line_index + 1, longest_win_line])

        return all_win_lines

    def calculate_symbols_position(self, wl: list) -> list:
        line_index = wl[0]-1
        sequence_length = len(wl[1])
        positions = []
        line_to_check = self.paylines[line_index]

        for i in range(sequence_length):
            # Get the column index from line_to_check
            col = line_to_check[i][1]  # i is the index of the current symbol in the winning line
            row = line_to_check[i][0]  # This represents the position in the original paylines
            positions.append([col, row])  # Append in [col, row] format

        return positions

    # def analyse_line_sequence(self, line: list) -> list | bool:
    #     # self.logger.debug("Analysing line sequence.")
    #     if not line:
    #         return False
    #
    #     primary_symbol = next(
    #         (sym for sym in line if sym != self.config.wild_symbol),
    #         self.config.wild_symbol,
    #     )
    #     matched_symbols = []
    #     count = 0
    #
    #     for symbol in line:
    #         if symbol == primary_symbol:  # Only check for the primary symbol
    #             count += 1
    #             matched_symbols.append(symbol)
    #         else:
    #             break
    #
    #     if count >= 3:
    #         return matched_symbols
    #     else:
    #         return False

    def detailed_spin_result(self, bet_amount):
        # self.logger.debug("Generating detailed spin result.")
        result = {
            "lines": self.lines,
            "total_winnings": 0,
            "free_spins": 0,
            "sticky_positions": {},
            "hits": 0,
            "wins": [],
            "cascades": [],
            "stickies": [],
            "current_free_spin_winnings": 0,
            "free_spin_round_end": False,
            "free_spin_total_winnings": 0,
            "win_amount": 0,
            "error": None,
        }

        try:
            win_amount = self.state_manager.get("total_winnings")
            result["total_winnings"] = win_amount
            result["win_amount"] = win_amount

            result["free_spins"] = self.free_spins
            result[
                "current_free_spin_winnings"] = self.current_free_spin_winnings
            result["free_spin_round_end"] = self.free_spin_round_end
            result["free_spin_total_winnings"] = self.free_spin_total_winnings
            result["total_free_spins_won"] = self.total_free_spins_won
        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"Error in detailed_spin_result: {e}")

        return result

    def exclude_wild_symbol(self, num_list):
        for number in num_list:
            if number != self.state_manager.get("config").wild_symbol:
                return number
        return None

    def check_payline(self, win_line) -> float:
        payout_multiplier = len(win_line[1])
        bet_amount = self.bet_amount

        bet_amount_per_line = bet_amount / 20  #divided by 20 because we have 20 payline (need to build this dynamically)
        payout_symbol = self.exclude_wild_symbol(win_line[1])
        if (payout_symbol in self.paytable
                and payout_multiplier in self.paytable[payout_symbol]):
            line_payout = (bet_amount_per_line *
                           self.paytable[payout_symbol][payout_multiplier])

            return line_payout
        return 0

    def get_state(self):
        # self.logger.debug("Getting slot machine state.")
        state = {
            "reels": self.state_manager.get("engine_reels"),
            "total_winnings": 0,
            "free_spins": 0,
            "sticky_positions": {},
            "hits": 0,
            "wins": [],
            "cascades": [],
            "stickies": [],
            "current_free_spin_winnings": 0,
        }
        state.pop("wins", None)
        return state

    def _update_state(self):
        # self.state_manager.set("engine_reels", self.reels)
        pass
