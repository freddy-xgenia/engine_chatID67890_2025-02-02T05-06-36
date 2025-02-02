# maths_engine/plugins/multiplier_wilds.py

from .base_plugin import BasePlugin


class MultiplierWildsPlugin(BasePlugin):
    def __init__(self, config, state_manager):
        super().__init__(config, state_manager)
        self.wild_symbol = config.get_plugin_param("wild_symbol", 7)  # Default wild symbol
        self.multiplier_value = config.get_plugin_param("multiplier_value", 2)  # Default multiplier value

    def apply_multiplier(self, line_win_info):
        """Apply the multiplier to the line win if a wild symbol is part of the winning combination."""
        if self.wild_symbol in line_win_info['symbols']:
            original_payout = line_win_info['payout']
            multiplied_payout = original_payout * self.multiplier_value
            print(f"Multiplier applied: Original payout {original_payout}, Multiplied payout {multiplied_payout}")
            line_win_info['payout'] = multiplied_payout
            line_win_info['multiplier_applied'] = True
            line_win_info['multiplier_value'] = self.multiplier_value
        else:
            line_win_info['multiplier_applied'] = False

    def before_spin(self, engine):
        """Reset or prepare the multiplier logic before a new spin."""
        pass  # No state reset needed for this plugin before a spin

    def after_spin(self, engine, spin_result):
        """Handle post-spin logic to apply multiplier to winning lines."""
        for line_win_info in spin_result.get('winning_lines', []):
            self.apply_multiplier(line_win_info)

        total_payout = sum(line['payout'] for line in spin_result.get('winning_lines', []))
        spin_result["total_payout"] = total_payout
        return spin_result


def init_plugin(config, state_manager):
    """Initialize the MultiplierWildsPlugin plugin."""
    return MultiplierWildsPlugin(config, state_manager)


def get_plugin_info():
    return {
        "name": "Multiplier Wilds",
        "description": "Applies a multiplier to line wins if a wild symbol is part of the combination.",
        "parameters": {
            "wild_symbol": {
                "type": "int",
                "default": 7,
                "description": "The symbol ID of the wild symbol."
            },
            "multiplier_value": {
                "type": "int",
                "default": 2,
                "description": "The value by which the line win is multiplied."
            }
        }
    }
