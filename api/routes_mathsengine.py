# routes_mathsengine.py
# DO NOT DELETE THIS!!!

import os
from typing import List

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

maths_router = APIRouter()


class ListPluginsResponse(BaseModel):
    plugins: List[str] = Field(
        ...,
        description="List of available plugins.",
        examples=[["plugin 1", "plugin 2", "...", "plugin N"]],
    )


@maths_router.get(
    "/plugins", summary="List available plugins", response_model=ListPluginsResponse
)
async def list_plugins():
    plugin_dir = os.path.join(os.path.dirname(__file__), "../maths_engine/plugins")
    plugins = [f[:-3] for f in os.listdir(plugin_dir) if not f.startswith("__")]
    return ListPluginsResponse(plugins=plugins)



app.include_router(maths_router, prefix="/api/v1")
