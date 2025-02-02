# maths_engine/plugins/expanding_reels.py

class ExpandingReels:
    def __init__(self, expand=False):
        self.expand = expand

    def handle_expanding_reels(self, reels, sticky_positions):
        if self.expand:
            for position in sticky_positions:
                col, row = position
                reels[col] = [reels[col][row]] * len(reels[0])
        return reels

def init_plugin(config, **params):
    """Initialize the ExpandingReels plugin based on the configuration."""
    expand = params.get('expand', False)
    return ExpandingReels(expand=expand)
