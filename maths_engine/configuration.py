# maths_engine/configuration.py
# DO NOT DELETE THIS!!!
import math
from typing import Dict
from maths_engine.isaac_rng_v2 import Isaac


class Configuration:

    def __init__(
            self,
            rows=3,
            columns=5,
            symbols=10,
            wild_symbol=9,
            weight_formula="math.exp(-x / 15)",
            payout_formula="1.5 * x",
            symbol_payouts: Dict[int, float] = {},
            custom_paylines=None,
            plugins=None,
            **additional_params,
    ):
        self.rows = int(rows)
        self.columns = int(columns)
        self.symbols = int(symbols)
        self.wild_symbol = int(wild_symbol)
        self.custom_paylines = custom_paylines or {}
        self.expand = False
        self.cascading_reels = True
        self.weight_formula = weight_formula
        self.payout_formula = payout_formula
        self.plugins = plugins if plugins is not None else []
        self.scatter_weight = 4.102
        # self.scatter_weight = 4.102
        # Store additional parameters for plugin use
        self.additional_params = additional_params

        # Initialize the attributes for simulation results
        self.rtp = None
        self.total_bets = None
        self.total_winnings = None
        self.hit_frequency = None
        # self.reel_weights = {i: [1] * self.symbols for i in range(self.columns)}  # Default equal weights for each reel

        self.symbol_payouts = symbol_payouts
        if not self.symbol_payouts:
            self.symbol_payouts = {
                1: 2.0,
                2: 2.5,
                3: 3.0,
                4: 3.5,
                5: 4.0,
                6: 4.5,
                7: 5.0,
                8: 5.5,
                9: 6.0,
                10: 6.5,
            }
        dynamic_symbol_payout = {}
        for symbol in range(1, self.symbols + 1):
            dynamic_symbol_payout[symbol] = 2.0 + (symbol - 1) * 0.5
        self.symbol_payouts = dynamic_symbol_payout

    def __repr__(self):
        return f"Configuration instance (rows={repr(self.rows)}, columns={repr(self.columns)})"

    def get_plugin_param(self, param_name, default=None):
        """Retrieve a parameter value for a plugin."""
        return self.additional_params.get(param_name, default)

    # MFM - Added Reel Set Weights
    # def set_reel_weights(self, reel_idx, weights):
    #     """Set custom weights for a specific reel."""
    #     if reel_idx < 0 or reel_idx >= self.columns:
    #         raise ValueError(f"Invalid reel index: {reel_idx}")
    #     if len(weights) != self.symbols:
    #         raise ValueError(f"Weight length must match the number of symbols: {self.symbols}")
    #     self.reel_weights[reel_idx] = weights
    # MFM - Added Get_Reel_weights
    def get_reel_weights(self, reel_idx):
        """Get the weight distribution for a specific reel."""
        # Call get_symbol_weights to get the weights list
        return self.get_symbol_weights()

    def get_reels(
            self,
            rng: Isaac,
    ):
        weights = self.get_symbol_weights()

        reels = []
        for reel_idx in range(1, self.columns + 1):
            reel = []
            for _ in range(1, self.rows + 1):
                reel.append(rng.rand(mod=self.symbols,
                                     reel_idx=reel_idx,
                                     ))
            reels.append(reel)
        return reels

    def get_paytable(self, exclude=None):
        exclude = exclude or []

        def calculate_payout(x):
            return eval(self.payout_formula, {"math": math, "x": x})

        paytable = {}
        for i in range(1, self.symbols + 1):
            if i in exclude:
                continue
            payouts = {}
            for combo_length in range(2, self.columns + 1):
                payout_in_dollars = calculate_payout(self.symbol_payouts[i] * combo_length)
                payouts[combo_length] = payout_in_dollars
            paytable[i] = payouts
        return paytable

    def get_paylines(self):
        if self.custom_paylines:
            return [v for k, v in sorted(self.custom_paylines.items())]
        return [
            [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)],  # Winline 1 - Horizontal top row    
            [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1)],  # Winline 2 - Horizontal middle row    
            [(0, 2), (1, 2), (2, 2), (3, 2), (4, 2)],  # Winline 3 - Horizontal bottom row    
            [(0, 0), (1, 1), (2, 2), (3, 1), (4, 0)],  # Winline 4 - V-shape    
            [(0, 2), (1, 1), (2, 0), (3, 1), (4, 2)],  # Winline 5 - Inverted V-shape    
            [(0, 0), (1, 0), (2, 1), (3, 2), (4, 2)],  # Winline 6 - Starts top, descends right    
            [(0, 2), (1, 2), (2, 1), (3, 0), (4, 0)],  # Winline 7 - Starts bottom, ascends right    
            [(0, 0), (1, 1), (2, 0), (3, 1), (4, 0)],  # Winline 8 - Zigzag down    
            [(0, 2), (1, 1), (2, 2), (3, 1), (4, 2)],  # Winline 9 - Zigzag up    
            [(0, 1), (1, 0), (2, 0), (3, 0), (4, 1)],  # Winline 10 - Lower corners horizontal line    
            [(0, 1), (1, 2), (2, 2), (3, 2), (4, 1)],  # Winline 11 - Upper corners horizontal line    
            [(0, 1), (1, 0), (2, 1), (3, 2), (4, 1)],  # Winline 12 - Zigzag down from middle    
            [(0, 1), (1, 2), (2, 1), (3, 0), (4, 1)],  # Winline 13 - Zigzag up from middle    
            [(0, 0), (1, 1), (2, 1), (3, 1), (4, 0)],  # Winline 14 - Top edge middle    
            [(0, 2), (1, 1), (2, 1), (3, 1), (4, 2)],  # Winline 15 - Bottom edge middle    
            [(0, 0), (1, 0), (2, 2), (3, 2), (4, 0)],  # Winline 16 - Steps down    
            [(0, 2), (1, 2), (2, 0), (3, 0), (4, 2)],  # Winline 17 - Steps up    
            [(0, 0), (1, 2), (2, 0), (3, 2), (4, 0)],  # Winline 18 - Alternating top and bottom    
            [(0, 2), (1, 0), (2, 2), (3, 0), (4, 2)],  # Winline 19 - Alternating bottom and top    
            [(0, 1), (1, 2), (2, 0), (3, 2), (4, 1)],  # Winline 20 - X shape
        ]

    def get_sticky_options(self):
        return self.sticky_options

    def get_symbol_weights(self):
        # Calculate the base weights using the weight formula
        base_weights = [
            eval(self.weight_formula, {"math": math, "x": i})
            for i in range(self.symbols)
        ]
        total_base_weight = sum(base_weights)

        # Normalize the base weights to make sure they sum up to 100
        normalized_base_weights = [(weight / total_base_weight) * 100 for weight in base_weights]
        normalized_base_weights[-1] = self.scatter_weight  # Lock scatter weight
        # print(normalized_base_weights)

        return normalized_base_weights

    def set_simulation_results(self, rtp, total_bets, total_winnings, hit_frequency):
        self.rtp = rtp
        self.total_bets = total_bets
        self.total_winnings = total_winnings
        self.hit_frequency = hit_frequency

    def get_simulation_results(self):
        return {
            "rtp": self.rtp,
            "total_bets": self.total_bets,
            "total_winnings": self.total_winnings,
            "hit_frequency": self.hit_frequency
        }


if __name__ == '__main__':
    c = Configuration()

