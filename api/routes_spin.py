#routes_spin.py
# DO NOT DELETE THIS!!!

import logging
from typing import Optional, Union

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel, Field

from maths_engine.configuration import Configuration
from maths_engine.simulation import Simulation
from maths_engine.state_manager import StateManager
from unittests.numbers import check_results

app = FastAPI()
spin_router = APIRouter()

logger = logging.getLogger(__name__)


class SpinRequest(BaseModel):
    session_id: str = Field(
        ..., description="The session ID for the spin.", examples=["xxx"]
    )
    bet_amount: int = Field(
        ..., description="The amount of the bet for each spin.", examples=[69]
    )
    is_free_spin: bool = Field(
        ..., description="Whether the spin is a free spin.", examples=[False]
    )
    plugins: dict = Field(
        ...,
        description="Plugins to load with parameters.",
        examples=[{
            "free_spins": {
                "multiplier": 1,
                "icon": 10,
                "blocked_reels": [0, 4],
            },
        }],
    )
    demo_params: Optional[dict] = Field(
        description="Demo parameters for the simulation.",
        default=None,
        examples=[{
            "custom_reels": [[1, 2, 3], [4, 5, 6], [7, 8, 9], [1, 2, 3], [4, 5, 6]],
        }],
    )
    # demo_params: Optional[None] = None


class SpinResponse(BaseModel):
    session_id: str = Field(
        ..., description="The session ID for the spin.", examples=["xxx"]
    )
    big_win: bool = Field(
        ..., description="Whether the spin resulted in a big win.", examples=[False]
    )
    spin_results: dict = Field(
        ...,
        description="Results of the spin.",
        examples=[{
            "total_payout": 0,
            "payline_results": [[6, 1, 7, 4, 2], [3, 8, 6, 9, 6], [9, 2, 9, 0, 4]],
            "winning_lines": [],
        }],
    )


@spin_router.post("/spin", summary="do the spin", response_model=SpinResponse)
async def spin(
    request: SpinRequest,
):
    config = Configuration(
        free_spins_icon=request.plugins.get("free_spins", {}).get("icon"),
        free_spins_trigger=request.plugins.get("free_spins", {}).get(
            "trigger_count", 0
        ),
        plugins=request.plugins,
    )

    free_spin_blocked_reel = request.plugins.get("free_spins", {}).get(
        "blocked_reels", []
    )

    blocked_reel_icon = {}
    for reel_idx in free_spin_blocked_reel:
        blocked_reel_icon[reel_idx] = request.plugins.get("free_spins", {}).get("icon")

    state_manager = StateManager(
        initial_state={
            "config": config,
            "blocked_icons": blocked_reel_icon,
        }
    )
    bet_amount = request.bet_amount
    simulation = Simulation(
        config=config,
        bet_amount=bet_amount,
        num_spins=1,
        capital=float("inf"),
        plugins_with_params=request.plugins,
        state_manager=state_manager,
        demo_params=request.demo_params,
    )

    simulation.state_manager.set("is_free_spin", request.is_free_spin)
    simulation.state_manager.set("icon", request.plugins.get("free_spins", {}).get("icon"))
    simulation.state_manager.set("blocked_reels", request.plugins.get("free_spins", {}).get("blocked_reels"))
    if request.is_free_spin:
        simulation.state_manager.set("current_free_spins", 1)  # Add 1 free spin in case it is free spin.
    try:
        # Assuming simulation.single_spin() generates a dictionary similar to the provided result.
        result = simulation.single_spin()

        # Process and validate results
        checked_results = check_results(result)
        # print(f"Checked results: {checked_results}")
    except Exception as e:
        import traceback
        logger.error("an error occurred: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e)) from e

    return SpinResponse(
        session_id=request.session_id,
        big_win=checked_results["big_win"],
        spin_results=checked_results["spin_results"],
    )


app.include_router(spin_router, prefix="/api/v1")
