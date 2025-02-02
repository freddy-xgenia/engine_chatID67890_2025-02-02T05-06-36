# simulation.py
# DO NOT DELETE THIS!!!

import logging
import os
import sys
import traceback
from concurrent.futures import ProcessPoolExecutor

from maths_engine.configuration import Configuration
from maths_engine.plugin_manager import PluginManager
from maths_engine.slot_machine_engine import SlotMachineEngine
from maths_engine.state_manager import StateManager

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logger = logging.getLogger(__name__)


class Simulation:

    def __init__(self,
                 config,
                 bet_amount,
                 num_spins,
                 capital,
                 plugins_with_params,
                 state_manager,
                 demo_params=None):
        self.state_manager = state_manager
        self.state_manager.set("bet_amount", bet_amount)
        self.state_manager.set("num_spins", num_spins)
        self.state_manager.set("pending_actions",
                               {})  # Track actions waiting for user input
        self.state_manager.set("action_complete",
                               False)  # Track when actions are complete
        self.state_manager.set("spin_count", 0)
        self.state_manager.set("capital", capital)
        self.state_manager.set("total_winnings", 0)
        self.state_manager.set("total_bets", 0)
        self.state_manager.set("hits", 0)
        self.state_manager.set("detailed_results", [])
        self.state_manager.set("errors", [])
        self.state_manager.set("multiplier", 1)
        self.state_manager.set("demo_params", demo_params)
        self.plugin_manager = PluginManager(
            config=config,
            state_manager=self.state_manager,
        )
        self.plugin_manager.load_plugins(plugins_with_params)
        self.engine = SlotMachineEngine(
            config=config,
            plugin_manager=self.plugin_manager,
            state_manager=self.state_manager,
        )
        # Store the engine in the state manager
        self.state_manager.set("slot_machine_engine", self.engine)
        self.state_manager.set("icon", 0)
        self.state_manager.set("blocked_reels", [])

    def run(self):
        try:
            num_spins = self.state_manager.get("num_spins")

            for _ in range(num_spins):
                capital = self.state_manager.get("capital")
                bet_amount = self.state_manager.get("bet_amount")

                if capital < bet_amount:
                    break

                spin_success = self._run_spin()
                if not spin_success:
                    # An error occurred during the spin, stop the simulation
                    break

            # Ensure the simulation results are stored
            rtp = self._get_rtp()
            self.state_manager.get("config").set_simulation_results(
                rtp,
                self.state_manager.get("total_bets"),
                self.state_manager.get("total_winnings"),
                self._get_hit_frequency()
            )

        except Exception as e:
            traceback.print_exc()
            logger.error({
                "action": "Simulation.run",
                "error": str(e),
            })
            errors = self.state_manager.get("errors", [])
            errors.append(str(e))
            self.state_manager.set("errors", errors)

        finally:
            user_id = self.state_manager.get("user_id")  # Assuming user_id is stored in state_manager
            self.plugin_manager.unload_plugins(user_id)

    


    
    def _run_spin(self):
        # Prepare for the spin with optional blocked reels or specific icons
        self.engine.pre_spin(icon=self.state_manager.get("icon"), blocked_reels=self.state_manager.get("blocked_reels"))

        # Process pending actions before proceeding with the spin
        if not self._process_pending_actions():
            # An error occurred while processing actions
            return False  # Indicate failure

        # Proceed with the spin once pending actions are handled
        self.plugin_manager.before_spin()
        self.engine.spin(self.state_manager.get("bet_amount"))
        self.plugin_manager.after_spin()

        # Process pending actions after the spin
        if not self._process_pending_actions():
            # An error occurred while processing actions
            return False  # Indicate failure

        # Update the capital and winnings
        bet_amount = self.state_manager.get("bet_amount")
        capital = self.state_manager.get("capital")

        # Deduct bet amount from capital
        capital -= bet_amount
        self.state_manager.set("capital", capital)

        # Increment total bets
        total_bets = self.state_manager.get("total_bets") + bet_amount
        self.state_manager.set("total_bets", total_bets)

        # Add spin winnings to capital
        spin_winning = self.state_manager.get("spin_winnings")
        capital += spin_winning
        self.state_manager.set("capital", capital)

        # Track hits and total winnings
        if spin_winning > 0:
            self.state_manager.set("hits", self.state_manager.get("hits") + 1)
            self.state_manager.set("total_winnings", self.state_manager.get("total_winnings") + spin_winning)

        # Store detailed spin results
        result = self.engine.detailed_spin_result(self.state_manager.get("bet_amount"))
        detailed_results = self.state_manager.get("detailed_results")
        detailed_results.append(result)
        self.state_manager.set("detailed_results", detailed_results)

        # Increment spin count
        self.state_manager.set("spin_count", self.state_manager.get("spin_count") + 1)

        return True  # Indicate success

    def _process_pending_actions(self):
        pending_actions = self.state_manager.get_pending_actions()
        if pending_actions:
            for action_id, action_details in list(pending_actions.items()):
                plugin_name = action_details.get('plugin_name')
                plugin_instance = self.plugin_manager.plugins.get(plugin_name)
                if plugin_instance:
                    action_type = action_details.get('type')
                    if action_type == 'selection':
                        # Simulate user input or implement selection logic
                        options = action_details.get('options', [])
                        selected_item = options[0] if options else None  # Select the first option for simulation

                        try:
                            # Call the plugin's handle_action method with the selected item
                            plugin_instance.handle_action({"selected_item": selected_item})
                            # Mark the action as completed
                            self.state_manager.complete_action(action_id, {})
                        except Exception as e:
                            error_message = f"Error handling action '{action_id}': {str(e)}"
                            logging.error(error_message)
                            self.state_manager.set("errors", self.state_manager.get("errors", []) + [error_message])
                            return False
                    else:
                        # Handle other action types if necessary
                        pass
                else:
                    error_message = f"Plugin '{plugin_name}' not found."
                    logging.error(error_message)
                    self.state_manager.set("errors", self.state_manager.get("errors", []) + [error_message])
                    return False
            # Re-check for new pending actions added during processing
            return self._process_pending_actions()
        return True



    def get_results(
        self,
        detail_level: str = "basic",
    ) -> dict:
        state = self.state_manager.get_full_state()

        results = {
            "total_bets": state["total_bets"],
            "total_winnings": state["total_winnings"],
            "rtp": self._get_rtp(),
            "hit_frequency": self._get_hit_frequency(),
            "errors": state.get("errors") or [],
            "pending_actions": state.get("pending_actions", {}),
            "total_free_spins_won": state.get("total_free_spins_won", 0)
        }

        # Set status based on presence of errors
        if results["errors"]:
            results["status"] = "error"
        else:
            results["status"] = "success"

        # Get results from each plugin
        for plugin_name, plugin_instance in self.plugin_manager.plugins.items():
            plugin_results = plugin_instance.get_results()
            results.update(plugin_results)

        if detail_level == "detailed":
            results["detailed_results"] = state["detailed_results"]
            results["paylines"] = self.state_manager.get("config").get_paylines()
            results["paytable"] = self.state_manager.get("config").get_paytable()

        return results
        
    def _get_rtp(self):
        total_bets = self.state_manager.get("total_bets")
        total_winnings = self.state_manager.get("total_winnings")  # convert from cents to base units
        
        return ((total_winnings / total_bets) * 100 if total_bets > 0 else 0)


    def _get_hit_frequency(self):
        return ((self.state_manager.get("hits") /
                 self.state_manager.get("spin_count")) *
                100 if self.state_manager.get("spin_count") > 0 else 0)

    def single_spin(self):
        # Ensure there are no pending actions before proceeding
        self._run_spin()

        # After the spin, check for any required user actions
        if self.plugin_manager.has_pending_actions():
            self.state_manager.set("pending_actions",
                                   self.plugin_manager.get_pending_actions())
            return {
                "status": "pending_actions",
                "details": self.state_manager.get("pending_actions")
            }

        spin_winning = self.state_manager.get("spin_winnings") * self.state_manager.get("multiplier")

        self.state_manager.set("total_bets", self.state_manager.get("total_bets") + self.state_manager.get("bet_amount"))
        self.state_manager.set("capital", self.state_manager.get("capital") - self.state_manager.get("bet_amount"))
        if spin_winning > 0:
            self.state_manager.set("hits", self.state_manager.get("hits") + 1)
            # self.state_manager.set("total_winnings", self.state_manager.get("total_winnings") + spin_winning)  # will double "total_winnings"
        detailed_results = self.state_manager.get("detailed_results")
        self.state_manager.set("detailed_results", detailed_results)

        out = self.get_results()
        ## hard coded! need to change! DONE!
        awarded = out
        
        symbols = []
        positions = []

        pos_count = 0

        if awarded.get("total_free_spins_won", 0) > 0:
            for spin_symbol in out["free_spins_detail"]:
                for symbol in spin_symbol:
                    pos_count+=1
                    symbols.append(symbol['symbols'][0])
                    positions.append([symbol['positions'][0], pos_count-1])

        out["big_win"] = False
        big_win = self.state_manager.get("bet_amount") * 1000  # Fixme: use correct value
        if spin_winning > big_win:
            out["big_win"] = True
        out["spin_results"] = {
            "total_payout": spin_winning,
            "payline_results": self.engine.lines,
            "winning_lines": self.engine.winning_lines,
            "free_spins": dict(
                awarded=out.get("total_free_spins_won", 0),
                positions=positions,
                symbols=symbols
            )
        }

        return out

    def has_pending_actions(self):
        for plugin in self.plugins.values():
            actions = plugin.get_pending_actions()
            if actions:
                return True
        return False

    def get_pending_actions(self):
        pending = {}
        for plugin_name, plugin in self.plugins.items():
            actions = plugin.get_pending_actions()
            if actions:
                pending[plugin_name] = actions
        return pending


async def run_simulation_async(simulation: Simulation):
    try:

        simulation.run()  # Run the simulation asynchronously
        return simulation.get_results()
    except Exception as e:
        logging.error(f"Simulation error: {traceback.format_exc()}")
        print(e)


if __name__ == '__main__':
    config = Configuration(
        rows=3,
        columns=5,
        symbols=10,
        wild_symbol=9,
        weight_formula='math.exp(-x / 2)',
        payout_formula='1.5 * x',
        symbol_payouts={},
        custom_paylines={},
    )
    state_manager = StateManager(initial_state={"config": config})


    simulation_instance = Simulation(
        config=config,
        bet_amount=69,
        num_spins=1,
        capital=100000000,
        plugins_with_params={
            "free_spins": {
                "blocked_reels": [
                    0,
                    4
                ],
                "icon": 10,
                "multiplier": 1
            }
        },
        state_manager=state_manager,
        demo_params=None)

    time_spend = simulation_instance.run()
    print(time_spend)