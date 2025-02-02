import asyncio

from icecream import ic
import random
from maths_engine.configuration import Configuration
from maths_engine.slot_machine_engine import SlotMachineEngine


class SlotMachineWrapper:
    def __init__(self, config: Configuration):
        self.engine = SlotMachineEngine(config)

    async def spin_once(self, bet_amount: float):
        return await self.engine.spin_once(bet_amount)


# In another part of your application
async def place_bet(bet_amount: float):
    configuration = Configuration()
    slot_machine = SlotMachineWrapper(config=configuration)
    return await slot_machine.spin_once(bet_amount)


spin_result = asyncio.run(place_bet(bet_amount=5))
ic(spin_result)
