class StickyOptions:

    def __init__(self,
                 duration=1,
                 expand=True,
                 multiplier=2,
                 until_bonus=False,
                 bonus_symbol=None):
        self.duration = duration
        self.expand = expand
        self.multiplier = multiplier
        self.until_bonus = until_bonus
        self.bonus_symbol = bonus_symbol

    def get_options(self):
        return {
            "duration": self.duration,
            "expand": self.expand,
            "multiplier": self.multiplier,
            "until_bonus": self.until_bonus,
            "bonus_symbol": self.bonus_symbol
        }