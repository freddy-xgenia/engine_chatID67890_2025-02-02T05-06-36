from maths_engine.slot_machine_engine import SlotMachineEngine
from maths_engine.configuration import Configuration
from icecream import ic


def main():
    config = Configuration(
                           )
    config.sticky_options["duration"] = 5
    config.sticky_options["multiplier"] = 3
    config.expand = False
    config.cascading_reels = True  # Set to True for testing cascading reels

    engine = SlotMachineEngine(config)
    bet_amount = 1
    result = engine.detailed_spin_result(bet_amount)

    # print(f"Reels: {result['reels']}")
    # print(f"Total Winnings: {result['total_winnings']}")
    # print(f"Bet Amount: {result['bet_amount']}")
    # print(f"Win Amount: {result['win_amount']}")
    # print(f"Hits: {result['hits']}")
    # print(f"Wins: {result['wins']}")
    # print(f"Free Spins: {result['free_spins']}")
    # ic(result)

if __name__ == "__main__":
    main()
