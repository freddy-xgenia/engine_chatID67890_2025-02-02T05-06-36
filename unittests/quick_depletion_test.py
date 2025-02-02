from unittests.base_test import BaseTest


class QuickDepletionTest(BaseTest):

    def run_test(self, simulation):
        initial_capital = simulation.starting_capital
        rounds_to_depletion = 0

        for i in range(simulation.num_spins):
            if simulation.starting_capital <= 0:
                break
            simulation.engine.spin(simulation.bet_amount)
            simulation.starting_capital -= simulation.bet_amount
            rounds_to_depletion += 1

        return {
            "test_name": "Quick Depletion Test",
            "rounds_to_depletion": rounds_to_depletion,
            "initial_capital": initial_capital
        }
