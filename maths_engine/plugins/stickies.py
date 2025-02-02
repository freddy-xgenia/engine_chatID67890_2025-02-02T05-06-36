# maths_engine/plugins/stickies.py

class Stickies:
    def __init__(self, options):
        self.duration = options.get('duration', 1)
        self.expand = options.get('expand', False)
        self.multiplier = options.get('multiplier', 1)
        self.until_bonus = options.get('until_bonus', False)
        self.bonus_symbol = options.get('bonus_symbol', None)
        self.sticky_positions = {}  # {(col, row): remaining_duration}

    def is_sticky(self, position):
        return position in self.sticky_positions

    def get_sticky_positions(self):
        return self.sticky_positions

    def set_sticky_positions(self, sticky_positions):
        self.sticky_positions = sticky_positions

    def update_stickies(self, reels):
        new_sticky_positions = {}
        for position, remaining_duration in self.sticky_positions.items():
            col, row = position
            if remaining_duration > 1:
                new_sticky_positions[position] = remaining_duration - 1
            elif remaining_duration == 1:
                # Sticky duration ends after this spin
                continue
            if self.expand:
                # Implement expanding logic if needed
                pass
        self.sticky_positions = new_sticky_positions

    def add_sticky(self, position):
        self.sticky_positions[position] = self.duration

def init_plugin(config):
    options = {
        'duration': config.sticky_options.get('duration', 1),
        'expand': config.sticky_options.get('expand', False),
        'multiplier': config.sticky_options.get('multiplier', 1),
        'until_bonus': config.sticky_options.get('until_bonus', False),
        'bonus_symbol': config.sticky_options.get('bonus_symbol', None),
    }
    return Stickies(options)

def get_plugin_info():
    return {
        "name": "Stickies",
        "description": "Adds sticky symbols to the reels with configurable options.",
        "parameters": {
            "duration": {
                "type": "int",
                "default": 1,
                "description": "Duration in spins for symbols to remain sticky."
            },
            "expand": {
                "type": "bool",
                "default": False,
                "description": "Whether sticky symbols expand to adjacent positions."
            },
            "multiplier": {
                "type": "int",
                "default": 1,
                "description": "Multiplier applied to wins involving sticky symbols."
            },
            "until_bonus": {
                "type": "bool",
                "default": False,
                "description": "Whether sticky symbols remain until a bonus round is triggered."
            },
            "bonus_symbol": {
                "type": "int",
                "default": None,
                "description": "Symbol ID that triggers the bonus round."
            }
        }
    }