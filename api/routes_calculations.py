

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel, Field

from maths_engine.configuration import Configuration

app = FastAPI()

calculations_router = APIRouter()

class CalculationRequest(BaseModel):
    symbols: int = Field(..., description="Number of different symbols in the slot machine.")
    columns: int = Field(..., description="Number of columns in the slot machine.")
    weight_formula: str = Field("math.exp(-x / 3.2)", description="Formula for symbol weight distribution.")
    payout_formula: str = Field("1.5 * x", description="Formula for payout calculation.")
    free_spins_icon: int = Field(10, description="Symbol that triggers free spins.")
    free_spins_trigger: int = Field(3, description="Number of symbols required to trigger free spins.")

class CalculationResponse(BaseModel):
    paytable: dict = Field(..., description="Generated paytable based on the formula.")
    symbol_weights: list = Field(..., description="Normalized symbol weights based on the formula.")

@calculations_router.post("/calculate_paytable_and_weights", response_model=CalculationResponse)
async def calculate_paytable_and_weights(request: CalculationRequest):
    try:
        # Create a Configuration instance
        config = Configuration(
            symbols=request.symbols,
            columns=request.columns,
            weight_formula=request.weight_formula,
            payout_formula=request.payout_formula,
            free_spins_icon=request.free_spins_icon,
            free_spins_trigger=request.free_spins_trigger
        )

        # Calculate the paytable and symbol weights
        paytable = config.get_paytable()
        symbol_weights = config.get_symbol_weights()

        # Return the results
        return CalculationResponse(
            paytable=paytable,
            symbol_weights=symbol_weights
        )
    except Exception as e:
        raise Exception(str(e)) from None

app.include_router(calculations_router, prefix="/api/v1")


