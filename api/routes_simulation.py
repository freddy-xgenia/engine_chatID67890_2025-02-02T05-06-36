# routes_simulation.py
# DO NOT DELETE THIS!!!
import logging
import requests
import traceback

from typing import Dict, List, Optional, Tuple, Union, Any
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, PlainTextResponse
from pydantic import BaseModel, Field, validator
from maths_engine.configuration import Configuration
from maths_engine.simulation import Simulation, run_simulation_async
from maths_engine.state_manager import StateManager
from maths_engine.plugin_manager import PluginManager  # Import PluginManager
from api.routes_calculations import CalculationResponse, CalculationRequest, calculate_paytable_and_weights
import concurrent.futures
import asyncio
import requests
import matplotlib.pyplot as plt
import numpy as np
import io
import math
from api.routes_calculations import CalculationRequest, calculate_paytable_and_weights, CalculationResponse
from api.routes_spin import SpinRequest, spin

# from icecream import ic
simulation_router = APIRouter()
logger = logging.getLogger(__name__)


class RunSimulationRequest(BaseModel):
    batch: Optional[int] = 10
    # Plugins code
    # plugin_url: str = Field(
    #     ...,
    #     description="URL to fetch the plugin code dynamically.",
    #     examples=["https://firebase.url/to/plugin.py"],
    # )
    plugin_url: Optional[str] = ""
    plugin_name: str = Field(
        None,
        description="Name of the plugin to load.",
        examples=["my_custom_plugin"],
    )
    plugins: Dict[str, Dict] = Field(
        ...,
        description="Plugins to load with parameters.",
        examples=[{
            "free_spins": {
                "icon": 10,
                "multiplier": 1,
                "blocked_reels": [0, 4]
            },
        }],
    )
    demo_params: Optional[dict] = Field(
        description="Demo parameters for the simulation.",
        default=None,
        examples=[{
            "custom_reels": [[1, 2, 3], [4, 5, 6], [7, 8, 9], [1, 2, 3],
                             [4, 5, 6]],
        }],
    )
    # End Plugins code

    bet_amount: int = Field(
        ...,
        description="The amount of the bet for each spin.",
        examples=[100])
    num_spins: int = Field(...,
                           description="The number of spins to simulate.",
                           examples=[10000], le=1_200_000)
    starting_capital: float = Field(
        ...,
        description="The initial capital before starting the simulation.",
        examples=[1_000_000_000],
    )
    rows: int = Field(3, description="Number of rows in the slot machine.")
    columns: int = Field(5,
                         description="Number of columns in the slot machine.")
    symbols: int = Field(
        10, description="Number of different symbols in the slot machine.")
    wild_symbol: int = Field(9,
                             description="The symbol that acts as the wild.")
    # free_spins_icon: int = Field(10, description="The symbol that triggers free spins.")
    # free_spins_trigger: int = Field(3, description="The number of free spins icons needed to trigger free spins.")
    sticky_duration: int = Field(1, description="Duration for sticky symbols.")
    expand_stickies: bool = Field(False,
                                  description="Whether sticky symbols expand.")
    sticky_multiplier: int = Field(
        1, description="Multiplier for sticky symbols.")
    until_bonus: bool = Field(
        False,
        description="Whether stickies last until a bonus round is triggered.")
    bonus_symbol: Optional[int] = Field(
        None, description="The symbol that triggers the bonus round.")
    cascading_reels: bool = Field(
        False, description="Whether the slot machine has cascading reels.")
    # free_spins_count: int = Field(10, description="Number of free spins awarded.")
    weight_formula: Optional[str] = Field(
        "math.exp(-x / 15)",
        description="Formula for symbol weight distribution.")
    payout_formula: Optional[str] = Field(
        "1.5 * x", description="Formula for payout calculation.")
    detail_level: str = Field(
        "basic",
        description="Level of detail for the simulation results.",
        examples=["basic", "detailed"],
    )
    custom_symbol_payouts: Optional[Dict[int, float]] = Field(
        {},
        description="Custom payouts for each symbol in the slot machine.",
        examples=[{
            1: 2.0,
            2: 2.5,
            3: 3.0,
            4: 3.5,
            5: 4.0,
            6: 4.5,
            7: 5.0,
            8: 5.5,
            9: 6.0,
            10: 6.5,
        }],
    )
    custom_paylines: Optional[Dict[str, List[Tuple[int, int]]]] = Field(
        None,
        description="Custom paylines for the slot machine.",
        examples=[{
            "line_1": [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)],
            "line_2": [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1)],
            "line_3": [(0, 2), (1, 2), (2, 2), (3, 2), (4, 2)],
            "line_4": [(0, 3), (1, 3), (2, 3), (3, 3), (4, 3)],
            "line_5": [(0, 4), (1, 4), (2, 4), (3, 4), (4, 4)],
            "line_6": [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)],
            "line_7": [(0, 4), (1, 3), (2, 2), (3, 1), (4, 0)],
            "line_8": [(0, 0), (1, 0), (2, 1), (3, 2), (4, 3)],
            "line_9": [(0, 4), (1, 4), (2, 3), (3, 2), (4, 1)],
            "line_10": [(0, 2), (1, 1), (2, 0), (3, 1), (4, 2)],
        }],
    )


class RunSimulationResponse(BaseModel):
    total_bets: float = Field(..., examples=[17.0])
    total_winnings: float = Field(..., examples=[9.0])
    rtp: float = Field(..., examples=[52.94117647058824])
    hit_frequency: float = Field(..., examples=[11.76470588235294])
    additional_results: Dict[str,
    Union[int, float, str, bool, list,
    dict]] = Field(default_factory=dict,
                   examples=[{
                       "total_free_spins_won":
                           5
                   }])
    errors: List[str] = Field(default_factory=list, examples=[[]])
    calculations: Optional[CalculationResponse]


class RunSimulationReportResponse(BaseModel):
    result_across_all_batches: List[RunSimulationResponse]
    profile_range: List


class AggregatedSimulationResult(BaseModel):
    total_spins: int
    total_batches: int
    spins_per_batches: int
    total_bets: int
    total_winnings: float
    # total_winnings: int
    avg_rtp_across_all_batches: str
    total_free_spins_won: int
    current_free_spins: int
    calculations: Optional[CalculationResponse]
    all_additional_results: Optional[Any]

    @validator("total_bets", pre=True, allow_reuse=True)
    def convert_float_to_int(cls, value):
        if isinstance(value, float):
            return int(value)  # Casts to integer if it's a float
        return value


class RunSimulationReportFinalResponse(BaseModel):
    result_across_all_batches: List[AggregatedSimulationResult]
    profile_range: List
    errors: List[str] = Field(default_factory=list, examples=[[]])


# class RunSimulationDepletionRequest(BaseModel):
#     initial_capital: int
#     bet_amount: int
#     max_rounds: Optional[int] = 1000  # Optional max rounds to prevent infinite loops


def fetch_plugin_code(url: str) -> str:
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
        return response.text  # Return the fetched plugin code
    except requests.RequestException as e:
        logger.error(f"Failed to fetch plugin from URL: {url}, Error: {e}")
        raise HTTPException(status_code=500,
                            detail=f"Error fetching plugin: {e}")


@simulation_router.post(
    "/run_simulation",
    summary="Run a slot machine simulation",
    description=
    "Simulates a series of slot machine spins and returns the results.",
    response_model=RunSimulationResponse,
)
async def run_simulation(request: RunSimulationRequest):
    # Fetch and execute the plugin code if a URL is provided
    if request.plugin_url:
        plugin_code = fetch_plugin_code(request.plugin_url)

        # Execute the plugin code in a controlled environment
        try:
            exec(plugin_code,
                 globals())  # Executes the plugin code, adding it to globals()
        except Exception as e:
            logger.error(f"Error executing plugin code from URL: {e}")
            raise HTTPException(status_code=500,
                                detail=f"Error executing plugin: {e}")

    weight_formula = request.weight_formula
    if weight_formula is None:
        weight_formula = ""

    payout_formula = request.payout_formula
    if payout_formula is None:
        payout_formula = ""

    config = Configuration(
        rows=request.rows,
        columns=request.columns,
        symbols=request.symbols,
        wild_symbol=request.wild_symbol,
        weight_formula=weight_formula,
        payout_formula=payout_formula,
        symbol_payouts=request.custom_symbol_payouts
        if request.custom_symbol_payouts else {},
        custom_paylines=request.custom_paylines,
    )
    config.sticky_options = {
        "duration": request.sticky_duration,
        "expand": request.expand_stickies,
        "multiplier": request.sticky_multiplier,
        "until_bonus": request.until_bonus,
        "bonus_symbol": request.bonus_symbol,
    }
    config.cascading_reels = request.cascading_reels

    state_manager = StateManager(initial_state={"config": config})

    # Initialize plugin manager and load plugins
    plugin_manager = PluginManager(config=config, state_manager=state_manager)
    plugin_manager.load_plugins(request.plugins)

    bet_amount = request.bet_amount

    simulation = Simulation(
        config=config,
        bet_amount=bet_amount,
        num_spins=request.num_spins,
        capital=request.starting_capital,
        plugins_with_params=request.plugins,
        state_manager=state_manager,
        demo_params=request.demo_params,
    )

    await run_simulation_async(simulation)

    # Fetch results from the simulation with the given detail level
    raw_results = simulation.get_results(detail_level=request.detail_level)

    known_keys = [
        "total_bets", "total_winnings", "rtp", "hit_frequency", "errors"
    ]
    additional_results = {
        key: raw_results.get(key, None)
        for key in raw_results
        if key not in known_keys and raw_results.get(key) is not None
    }

    body_calculate = CalculationRequest(symbols=request.symbols,
                                        columns=request.columns,
                                        weight_formula=request.weight_formula,
                                        payout_formula=request.payout_formula,
                                        free_spins_icon=10,
                                        free_spins_trigger=3)

    calculate_payout = await calculate_paytable_and_weights(body_calculate)

    converted_rtp = raw_results.get("rtp", 0.0)
    formatted_rtp = float(f"{converted_rtp:.1f}")

    return RunSimulationResponse(
        total_bets=raw_results.get("total_bets", 0.0),
        total_winnings=raw_results.get("total_winnings", 0.0),
        rtp=formatted_rtp,
        hit_frequency=raw_results.get("hit_frequency", 0.0),
        additional_results=additional_results,
        errors=raw_results.get("errors", []),
        calculations=calculate_payout
    )


# @simulation_router.post("/handle_action")
# async def handle_action(action: dict):
#     if not simulation_instance.plugin_manager.has_pending_actions():
#         return {"error": "No pending actions to handle."}
#
#     results = {}
#     for plugin_name, plugin in simulation_instance.plugin_manager.plugins.items(
#     ):
#         plugin_results = plugin.handle_action(action)
#         if plugin_results:
#             results[plugin_name] = plugin_results
#
#     return results


async def call_run_simulation(request):
    # Fetch and execute the plugin code if a URL is provided
    if request.plugin_url:
        plugin_code = fetch_plugin_code(request.plugin_url)

        # Execute the plugin code in a controlled environment
        try:
            exec(plugin_code,
                 globals())  # Executes the plugin code, adding it to globals()
        except Exception as e:
            logger.error(f"Error executing plugin code from URL: {e}")
            raise HTTPException(status_code=500,
                                detail=f"Error executing plugin: {e}")

    weight_formula = request.weight_formula
    if weight_formula is None:
        weight_formula = ""

    payout_formula = request.payout_formula
    if payout_formula is None:
        payout_formula = ""

    config = Configuration(

        rows=request.rows,
        columns=request.columns,
        symbols=request.symbols,
        wild_symbol=request.wild_symbol,
        weight_formula=weight_formula,
        payout_formula=payout_formula,
        symbol_payouts=request.custom_symbol_payouts
        if request.custom_symbol_payouts else {},
        custom_paylines=request.custom_paylines,
    )
    config.sticky_options = {
        "duration": request.sticky_duration,
        "expand": request.expand_stickies,
        "multiplier": request.sticky_multiplier,
        "until_bonus": request.until_bonus,
        "bonus_symbol": request.bonus_symbol,
    }
    config.cascading_reels = request.cascading_reels

    state_manager = StateManager(initial_state={"config": config})

    # Initialize plugin manager and load plugins
    plugin_manager = PluginManager(config=config, state_manager=state_manager)
    plugin_manager.load_plugins(request.plugins)

    bet_amount = request.bet_amount

    simulation = Simulation(
        config=config,
        bet_amount=bet_amount,
        num_spins=request.num_spins,
        capital=request.starting_capital,
        plugins_with_params=request.plugins,
        state_manager=state_manager,
        demo_params=request.demo_params,
    )
    # TODO: WIP
    await run_simulation_async(simulation)

    # Fetch results from the simulation with the given detail level
    raw_results = simulation.get_results(detail_level=request.detail_level)
    known_keys = [
        "total_bets", "total_winnings", "rtp", "hit_frequency", "errors"
    ]
    additional_results = {
        key: raw_results.get(key, None)
        for key in raw_results
        if key not in known_keys and raw_results.get(key) is not None
    }

    body_calculate = CalculationRequest(
        symbols=request.symbols,
        columns=request.columns,
        weight_formula=request.weight_formula,
        payout_formula=request.payout_formula,
        free_spins_icon=10,
        free_spins_trigger=3
    )
    calculate_payout = await calculate_paytable_and_weights(body_calculate)

    run_simulation_response = RunSimulationResponse(
        total_bets=raw_results.get("total_bets", 0.0),
        total_winnings=raw_results.get("total_winnings", 0.0),
        rtp=raw_results.get("rtp", 0.0),
        hit_frequency=raw_results.get("hit_frequency", 0.0),
        additional_results=additional_results,
        errors=raw_results.get("errors", []),
        calculations=calculate_payout,
    )

    return run_simulation_response


def run_multi_simulation_async(request):
    return asyncio.run(call_run_simulation(request))


def merge_results(results: List[RunSimulationResponse]) -> RunSimulationResponse:
    total_bets = sum(result.total_bets for result in results)
    total_winnings = sum(result.total_winnings for result in results)

    total_rtp = sum(result.rtp for result in results)
    average_rtp = total_rtp / len(results) if results else 0.0

    total_hit_frequency = sum(result.hit_frequency for result in results)
    average_hit_frequency = total_hit_frequency / len(results) if results else 0.0

    # Aggregate additional results
    total_free_spins_won = sum(result.additional_results.get("total_free_spins_won", 0) for result in results)
    total_bonus_rounds_triggered = sum(result.additional_results.get("bonus_rounds_triggered", 0) for result in results)

    # Aggregate paytable
    merged_paytable = {}
    for result in results:
        for symbol, payouts in result.calculations.paytable.items():
            if symbol not in merged_paytable:
                merged_paytable[symbol] = {occurrence: 0.0 for occurrence in payouts}
            for occurrence, payout in payouts.items():
                merged_paytable[symbol][occurrence] += payout

    # Aggregate symbol weights by averaging them
    if results:
        num_results = len(results)
        symbol_weights_length = len(results[0].calculations.symbol_weights)
        merged_symbol_weights = [0.0] * symbol_weights_length
        for result in results:
            for i, weight in enumerate(result.calculations.symbol_weights):
                merged_symbol_weights[i] += weight
        merged_symbol_weights = [weight / num_results for weight in merged_symbol_weights]
    else:
        merged_symbol_weights = []

    # Create the merged result
    merged_result = RunSimulationResponse(
        total_bets=total_bets,
        total_winnings=total_winnings,
        rtp=average_rtp,
        hit_frequency=average_hit_frequency,
        additional_results={
            "pending_actions": {},
            "multiplier_used": 3,
            "multiplier_effect_applied": 0.0,
            "total_free_spins_won": total_free_spins_won,
            "current_free_spins": 0,
            "bonus_rounds_triggered": total_bonus_rounds_triggered
        },
        errors=[],
        calculations=CalculationResponse(paytable=merged_paytable, symbol_weights=merged_symbol_weights),
    )

    return merged_result


@simulation_router.post("/run-multi-simulation")
async def run_multi_simulation(request: RunSimulationRequest):
    num_spins = request.num_spins
    logging.info(f"Received request to run multi simulation with num_spins: {num_spins}")

    if num_spins < 16:
        raise HTTPException(status_code=400, detail="num_spins should be at least 16")

    spins_per_worker = num_spins // 16
    remainder = num_spins % 16

    spins_list = [spins_per_worker] * 16
    for i in range(remainder):
        spins_list[i] += 1

    logging.info(f"Divided spins: {spins_list}")

    all_results = []

    # FIXME: Fix starting_capital
    with concurrent.futures.ProcessPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(run_multi_simulation_async, request.model_copy(
            update={"num_spins": spins, "starting_capital": spins, "bet_amount": request.bet_amount})) for spins in
                   spins_list]
        for future in concurrent.futures.as_completed(futures):
            print('result in multiprocessing : ', future.result().rtp)
            all_results.append(future.result())

    return merge_results(all_results)


rtp_values = []


# @simulation_router.post("/run-batch-simulation-old")
# async def run_batch_simulation_old(request: RunSimulationRequest, app_request: Request):
#     global rtp_values
#     batch = request.batch
#     capital = request.starting_capital
#     capital_per_batch = capital / batch
#     if not batch:
#         raise HTTPException(status_code=422,
#                                 detail=f"batch field is empty")
#     num_spins = request.num_spins
#     logging.info(f"Received request to run multi simulation with num_spins: {num_spins}")
#
#     if num_spins < batch:
#         raise HTTPException(status_code=400, detail=f"num_spins should be at least {batch}")
#
#     spins_per_worker = num_spins // batch
#     remainder = num_spins % batch
#
#     spins_list = [spins_per_worker] * batch
#     for i in range(remainder):
#         spins_list[i] += 1
#
#     logging.info(f"Divided spins: {spins_list}")
#
#     all_results = []
#     rtp_profile_range_results = []
#     min_rtp = 90.0
#     max_rtp = 98.0
#
#     executor = app_request.app.state.executor
#     rtp_values = []  # Clear previous values
#     futures = [executor.submit(run_multi_simulation_async, request.model_copy(update={"num_spins": spins, "starting_capital": capital_per_batch})) for spins in spins_list]
#     for future in concurrent.futures.as_completed(futures):
#         result = future.result()  # Fetch result only once
#         all_results.append(result)
#
#         # Process RTP logic
#         rtp = result.rtp
#         converted_rtp = rtp
#         rtp_values.append(converted_rtp)
#         formatted_rtp = float(f"{converted_rtp:.1f}")
#         if formatted_rtp > max_rtp:
#             rtp_profile_range_results.append(dict(expected_rtp=f"RTP {formatted_rtp} is above maximum expected {max_rtp}"))
#         elif formatted_rtp < min_rtp:
#             rtp_profile_range_results.append(dict(expected_rtp=f"RTP {formatted_rtp} is below minimum expected {min_rtp}"))
#         else:
#             rtp_profile_range_results.append(dict(expected_rtp=f"RTP {formatted_rtp} is in range"))
#
#     simulation_report = RunSimulationReportResponse(
#         result_across_all_batches=all_results,
#         profile_range=rtp_profile_range_results
#     )
#
#     return simulation_report

@simulation_router.post("/run-batch-simulation")
async def run_batch_simulation(request: RunSimulationRequest, app_request: Request):
    from icecream import ic
    try:
        global rtp_values
        batch = request.batch

        if not batch:
            raise HTTPException(status_code=422, detail="batch field is empty")
        num_spins = request.num_spins
        logging.info(f"Received request to run multi simulation with num_spins: {num_spins}")

        if num_spins < batch:
            raise HTTPException(status_code=400, detail="num_spins should be at least {batch}")

        spins_per_worker = num_spins // batch
        remainder = num_spins % batch
        capital = request.starting_capital
        capital_per_batch = capital / batch  # FIXME: Do it more accurate.
        spins_list = [spins_per_worker] * batch
        for i in range(remainder):
            spins_list[i] += 1
        logging.info(f"Divided spins: {spins_list}")

        all_results = []
        rtp_profile_range_results = []
        min_rtp = 90.0
        max_rtp = 98.0

        total_bets = 0
        total_winnings = 0
        total_free_spins_won = 0
        sum_rtp = 0.0
        current_free_spins = 0
        calculations = {}
        errors = any
        aggregated_additional_results = []  # Collect dynamic additional results

        executor = concurrent.futures.ThreadPoolExecutor()
        rtp_values = []  # Clear previous values

        futures = [executor.submit(run_multi_simulation_async, request.model_copy(
            update={"num_spins": spins, "starting_capital": capital_per_batch})) for spins in spins_list]
        for future in concurrent.futures.as_completed(futures):

            result = future.result()  # RunSimulationResponse without total_free_spins_won info
            all_results.append(result)
            calculations = result.calculations

            errors = result.errors

            # Aggregate data
            total_bets += result.total_bets
            total_winnings += result.total_winnings
            total_free_spins_won += result.additional_results.get('total_free_spins_won', 0)
            sum_rtp += result.rtp
            current_free_spins += result.additional_results.get('current_free_spins', 0)

            # Aggregate all additional_results dynamically
            aggregated_additional_results.append(result.additional_results)

            # Process RTP logic
            converted_rtp = result.rtp
            rtp_values.append(converted_rtp)
            formatted_rtp = float(f"{converted_rtp:.1f}")
            if formatted_rtp > max_rtp:
                rtp_profile_range_results.append(
                    dict(expected_rtp=f"RTP {formatted_rtp} is above maximum expected {max_rtp}"))
            elif formatted_rtp < min_rtp:
                rtp_profile_range_results.append(
                    dict(expected_rtp=f"RTP {formatted_rtp} is below minimum expected {min_rtp}"))
            else:
                rtp_profile_range_results.append(dict(expected_rtp=f"RTP {formatted_rtp} is in range"))

        # Calculate average RTP across all batches
        avg_rtp_across_all_batches = sum_rtp / batch

        # Prepare final response, including symbol weights summary
        aggregated_result = AggregatedSimulationResult(
            total_spins=request.num_spins,
            total_batches=batch,
            spins_per_batches=spins_list[0],
            total_bets=total_bets,
            total_winnings=total_winnings,
            current_free_spins=current_free_spins,
            avg_rtp_across_all_batches=f"{avg_rtp_across_all_batches:.1f}%",
            total_free_spins_won=total_free_spins_won,
            calculations=calculations,
            all_additional_results=aggregated_additional_results
        )

        simulation_report = RunSimulationReportFinalResponse(
            result_across_all_batches=[aggregated_result],
            profile_range=rtp_profile_range_results,
            errors=errors
        )
        for aggregated_result in simulation_report.result_across_all_batches:
            for additional_result in aggregated_result.all_additional_results:
                if 'free_spins_detail' in additional_result:
                    del additional_result['free_spins_detail']
        return simulation_report
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return PlainTextResponse(
            status_code=500,
            content=traceback.format_exc(),
        )


# Separate endpoint for downloading the profile range image
@simulation_router.get("/download-profile-range-image")
async def download_profile_range_image():
    global rtp_values  # Access the global rtp_values

    if not rtp_values:
        raise HTTPException(status_code=404, detail="No RTP values found. Please run the simulation first.")

    # Simulate the RTP statuses based on values (you can customize this further)
    statuses = ['below' if rtp < 90 else 'in range' for rtp in rtp_values]

    # Create the bar chart
    fig, ax = plt.subplots(figsize=(12, 12))

    x_pos = np.arange(len(rtp_values))
    bars = ax.bar(x_pos, rtp_values, color=['red' if 'below' in status else 'green' for status in statuses])

    ax.set_xlabel('RTP Values')
    ax.set_ylabel('RTP')
    ax.set_title('Profile Range Report')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([f"RTP {rtp:.1f}" for rtp in rtp_values])
    ax.axhline(y=90, color='blue', linestyle='--', label='Minimum Expected RTP')
    ax.legend()

    # Save the figure to a BytesIO object instead of a file
    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png')
    plt.close()  # Close the figure after saving

    img_bytes.seek(0)  # Rewind the BytesIO object to the beginning

    # Return the image as a downloadable file
    return StreamingResponse(img_bytes, media_type="image/png",
                             headers={"Content-Disposition": "attachment; filename=profile_range_report.png"})


# Define a new endpoint for Profile Point Report
@simulation_router.post("/run-profile-point-report")
async def run_profile_point_report(request: RunSimulationRequest, app_request: Request):
    # Validation logic
    if not request.batch:
        raise HTTPException(status_code=422, detail=f"batch field is empty")

    num_spins = request.num_spins
    batch = request.batch
    if num_spins < batch:
        message = f"num_spins should be at least {batch}"
        raise HTTPException(status_code=400, detail=message)

    # Distribute spins among workers
    spins_per_worker = num_spins // batch
    remainder = num_spins % batch
    spins_list = [spins_per_worker] * batch
    for i in range(remainder):
        spins_list[i] += 1

    # Collect results from simulation
    all_results = []
    rtp_profile_point_results = []
    important_points = []
    executor = app_request.app.state.executor
    futures = [executor.submit(run_multi_simulation_async, request.model_copy(update={"num_spins": spins})) for spins in
               spins_list]

    rtp_values = []  # Reset RTP values for this run
    for future in concurrent.futures.as_completed(futures):
        result = future.result()
        all_results.append(result)

        # Collect RTP values for each result
        rtp = result.rtp / 1000  # Assuming result.rtp is large, scaling it down
        rtp_values.append(rtp)

        # Identify specific profile points of interest (e.g., very high or low RTP values)
        if rtp > 95.0:
            important_points.append({"rtp": rtp, "comment": "RTP is significantly above normal"})
        elif rtp < 92.0:
            important_points.append({"rtp": rtp, "comment": "RTP is significantly below normal"})
        else:
            important_points.append({"rtp": rtp, "comment": "RTP is in the normal range"})

        # Append results
        rtp_profile_point_results.append(dict(rtp=f"RTP {rtp:.1f}"))

    # Generate and return a simulation report with the collected results and points of interest
    simulation_report = RunSimulationReportResponse(
        result_across_all_batches=all_results,
        profile_range=important_points  # Return the identified profile points
    )

    return simulation_report


# Optional: Generate a graph for the Profile Point Report
@simulation_router.get("/download-profile-point-image")
async def download_profile_point_image():
    global rtp_values  # Assuming you store RTP values globally

    if not rtp_values:
        raise HTTPException(status_code=404, detail="No RTP values found. Please run the simulation first.")

    # Simulate the Profile Points logic
    statuses = ['low' if rtp < 92 else 'high' if rtp > 95 else 'normal' for rtp in rtp_values]

    # Create the graph
    fig, ax = plt.subplots(figsize=(12, 12))
    x_pos = np.arange(len(rtp_values))
    bars = ax.bar(x_pos, rtp_values,
                  color=['red' if 'low' in status else 'green' if 'high' in status else 'blue' for status in statuses])

    ax.set_xlabel('RTP Values')
    ax.set_ylabel('RTP')
    ax.set_title('Profile Point Report')
    ax.set_xticks(x_pos)
    ax.set_xticklabels([f"RTP {rtp:.1f}" for rtp in rtp_values])
    ax.axhline(y=92, color='red', linestyle='--', label='Low Threshold (92)')
    ax.axhline(y=95, color='green', linestyle='--', label='High Threshold (95)')
    ax.legend()

    # Save image to BytesIO
    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png')
    plt.close()
    img_bytes.seek(0)

    return StreamingResponse(img_bytes, media_type="image/png",
                             headers={"Content-Disposition": "attachment; filename=profile_point_report.png"})


# Define a new endpoint for Confidence Level Report
@simulation_router.post("/run-confidence-level-report")
async def run_confidence_level_report(request: RunSimulationRequest, app_request: Request):
    if not request.batch:
        raise HTTPException(status_code=422, detail=f"batch field is empty")

    num_spins = request.num_spins
    batch = request.batch
    if num_spins < batch:
        raise HTTPException(status_code=400, detail=f"num_spins should be at least {batch}")

    # Distribute spins among workers
    spins_per_worker = num_spins // batch
    remainder = num_spins % batch
    spins_list = [spins_per_worker] * batch
    for i in range(remainder):
        spins_list[i] += 1

    # Collect results from simulation
    all_results = []
    executor = app_request.app.state.executor
    futures = [executor.submit(run_multi_simulation_async, request.model_copy(update={"num_spins": spins})) for spins in
               spins_list]

    rtp_values = []  # Reset RTP values for this run
    for future in concurrent.futures.as_completed(futures):
        result = future.result()
        all_results.append(result)

        # Collect RTP values for each result
        rtp = result.rtp / 1000  # Assuming result.rtp is large, scaling it down
        rtp_values.append(rtp)

    # Calculate confidence interval
    mean_rtp = np.mean(rtp_values)
    std_dev = np.std(rtp_values)
    sample_size = len(rtp_values)

    # Z-score for 95% confidence level
    z_value = 1.96
    margin_of_error = z_value * (std_dev / math.sqrt(sample_size))

    lower_bound = mean_rtp - margin_of_error
    upper_bound = mean_rtp + margin_of_error

    confidence_interval = {
        "mean_rtp": mean_rtp,
        "std_dev": std_dev,
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "confidence_level": "95%"
    }

    return {
        "confidence_interval": confidence_interval,
        "simulation_results": all_results
    }


# Optional: Generate a graph for the Confidence Level Report
@simulation_router.get("/download-confidence-level-image")
async def download_confidence_level_image():
    global rtp_values  # Assuming you store RTP values globally

    if not rtp_values:
        raise HTTPException(status_code=404, detail="No RTP values found. Please run the simulation first.")

    # Calculate confidence interval for the graph
    mean_rtp = np.mean(rtp_values)
    std_dev = np.std(rtp_values)
    sample_size = len(rtp_values)
    z_value = 1.96
    margin_of_error = z_value * (std_dev / math.sqrt(sample_size))

    lower_bound = mean_rtp - margin_of_error
    upper_bound = mean_rtp + margin_of_error

    # Create the graph
    fig, ax = plt.subplots(figsize=(12, 8))
    x_pos = np.arange(len(rtp_values))

    # Plot RTP values as bars
    ax.bar(x_pos, rtp_values, color='gray')

    # Plot the confidence interval as horizontal lines
    ax.axhline(y=lower_bound, color='red', linestyle='--', label=f'Lower Bound: {lower_bound:.2f}')
    ax.axhline(y=upper_bound, color='green', linestyle='--', label=f'Upper Bound: {upper_bound:.2f}')
    ax.axhline(y=mean_rtp, color='blue', linestyle='-', label=f'Mean RTP: {mean_rtp:.2f}')

    ax.set_xlabel('Simulation Index')
    ax.set_ylabel('RTP Value')
    ax.set_title('Confidence Interval Report')
    ax.legend()

    # Save image to BytesIO
    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png')
    plt.close()
    img_bytes.seek(0)

    return StreamingResponse(img_bytes, media_type="image/png",
                             headers={"Content-Disposition": "attachment; filename=confidence_level_report.png"})


@simulation_router.post("/depletion-test")
async def depletion_test(request: RunSimulationRequest, max_rounds: Optional[int] = 1000):
    initial_capital = request.starting_capital
    rounds_to_depletion = 0
    capital = initial_capital
    bet_amount = request.bet_amount

    # Set up parameters for each round and continue until capital is depleted or max rounds reached
    while capital > bet_amount and rounds_to_depletion < max_rounds:
        plugins = {"free_spins": {"blocked_reels": [0, 4], "icon": 1, "multiplier": 1}}
        spin_request = SpinRequest(
            session_id='xxx',
            bet_amount=int(bet_amount * 100),  # Convert back to cents for SpinRequest
            plugins=plugins,
            is_free_spin=False
        )

        try:
            # Use the spin endpoint to execute a single spin
            response = await spin(spin_request)

            # Extract winnings and update capital
            total_bets = bet_amount  # Each spin costs the bet amount
            total_winnings = response.spin_results["total_payout"] / 100  # Assuming payout is in cents

            # Adjust capital based on bet and winnings
            capital += total_winnings - total_bets
            rounds_to_depletion += 1

            # Prevent capital from going negative
            if capital < 0:
                capital = 0
                break

        except HTTPException as e:
            raise HTTPException(status_code=500, detail=f"Error during depletion test: {e.detail}")

    # Create the depletion report
    return {
        "test_name": "Quick Depletion Test",
        "rounds_to_depletion": rounds_to_depletion,
        "initial_capital": initial_capital,
        "remaining_capital": capital
    }


if __name__ == '__main__':
    request_data = RunSimulationRequest(batch=1, plugin_url='', plugin_name='my_custom_plugin',
                                        plugins={'free_spins': {'blocked_reels': [0, 4], 'icon': 10, 'multiplier': 1
                                                                }}, demo_params=None, bet_amount=100, num_spins=100,
                                        starting_capital=100000000.0, rows=3, columns=5, symbols=10, wild_symbol=9,
                                        sticky_duration=0,
                                        expand_stickies=False, sticky_multiplier=2, until_bonus=False, bonus_symbol=0,
                                        cascading_reels=False, weight_formula='math.exp(-x / 12)',
                                        payout_formula='1.5 * x', detail_level='basic', custom_symbol_payouts={},
                                        custom_paylines={})
