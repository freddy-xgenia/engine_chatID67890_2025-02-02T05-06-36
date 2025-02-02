import logging
import traceback

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from maths_engine.buy_free_spin import Constant

buy_free_spin_router = APIRouter()
logger = logging.getLogger(__name__)


class BuyFreeSpinRequest(BaseModel):
    """Request body for buying free spins."""

    bet_amount: int = Field(..., description="The bet amount for the spin.")


class BuyFreeSpinResponse(BaseModel):
    """Response body for buying free spins."""

    cost: float = Field(..., description="The cost of buying free spins.")
    quantity: int = Field(..., description="The quantity of free spins bought.")


@buy_free_spin_router.get("/buy_free_spins", response_model=BuyFreeSpinResponse)
async def buy_free_spins(
    bet_amount: int = Query(..., description="The bet amount for the spin."),
):
    """Endpoint for buying free spins."""
    try:
        # Get the cost of buying free spins
        cost = bet_amount * Constant.DEFAULT_RATE
        quantity = Constant.DEFAULT_QUANTITY

        return BuyFreeSpinResponse(cost=cost, quantity=quantity)

    except Exception as e:
        logger.error(f"Error buying free spins: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail="Error buying free spins."
        ) from None
