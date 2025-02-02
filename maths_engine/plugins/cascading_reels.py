# maths_engine/plugins/cascading_reels.py

import random

class CascadingReels:
    def __init__(self, rows, columns, symbol_weights, stickies, scatter_symbols, paylines):
        self.rows = rows
        self.columns = columns
        self.symbol_weights = symbol_weights
        self.stickies = stickies
        self.scatter_symbols = scatter_symbols
        self.paylines = paylines

    def cascade_reels(self, reels):
        print("Cascading reels...")  # Debug statement
        new_reels = []
        cascaded = False

        for col in range(self.columns):
            filtered_col = [
                symbol for row, symbol in enumerate(reels[col])
                if not self.stickies.is_sticky((col, row)) and symbol != 0
            ]
            if len(filtered_col) < self.rows:
                cascaded = True
                filtered_col = [
                    self.random_symbol()
                    for _ in range(self.rows - len(filtered_col))
                ] + filtered_col
            new_reels.append(filtered_col)

        self.update_stickies(reels, new_reels)
        return cascaded

    def random_symbol(self):
        return random.choices(range(1, len(self.symbol_weights) + 1), weights=self.symbol_weights)[0]

    def update_stickies(self, old_reels, new_reels):
        new_sticky_positions = {}
        for position, duration in self.stickies.get_sticky_positions().items():
            col, row = position
            if duration > 1:
                new_sticky_positions[position] = duration - 1
                new_reels[col][row] = old_reels[col][row]
        self.stickies.set_sticky_positions(new_sticky_positions)

def init_plugin(config, scatter_symbols=[11, 12], stickies=None):
    """Initialize the CascadingReels plugin based on the configuration."""
    rows = config.rows
    columns = config.columns
    symbol_weights = config.get_symbol_weights()
    paylines = config.get_paylines()

    return CascadingReels(rows, columns, symbol_weights, stickies, scatter_symbols, paylines)
