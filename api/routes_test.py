# routes_mathsengine.py


from fastapi import APIRouter, FastAPI
from pydantic import BaseModel, Field

from unittests.test_manager import TestManager

app = FastAPI()

test_router = APIRouter()


class ListTestsResponse(BaseModel):
    tests: list = Field(
        ...,
        description="List of available tests.",
        examples=[["test 1", "test 2", "...", "test N"]],
    )


class RunTestsResponse(BaseModel):
    results: dict = Field(
        ...,
        description="Results of the tests.",
        examples=[{
            "test 1": {
                "success": True,
            },
            "test 2": {
                "success": True,
            },
            "test N": {
                "success": True,
            },
        }],
    )


@test_router.get(
    "/test", summary="List available tests", response_model=ListTestsResponse
)
async def list_tests():
    test_manager = TestManager()
    test_manager.load_tests()
    tests = test_manager.list_tests()
    return ListTestsResponse(tests=tests)


@test_router.post("/test", summary="run all test", response_model=RunTestsResponse)
async def run_tests():
    test_manager = TestManager()
    test_manager.load_tests()
    res = test_manager.run_tests()
    return {"results": res}


app.include_router(test_router, prefix="/api/v1")
