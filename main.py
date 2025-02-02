from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.routes_calculations import calculations_router
from api.routes_codesandbox import sandbox_router
from api.routes_mathsengine import maths_router
from api.routes_simulation import simulation_router
from api.routes_spin import spin_router
from api.routes_test import test_router

# Create FastAPI app
app = FastAPI(debug=True)

# Include routers for various endpoints
app.include_router(simulation_router, prefix="/api/v1", tags=["Simulation"])
app.include_router(sandbox_router, prefix="/api/v1", tags=["CodeSandBox"])
app.include_router(spin_router, prefix="/api/v1", tags=["Spin"])
app.include_router(maths_router, prefix="/api/v1", tags=["Maths Engine"])
app.include_router(test_router, prefix="/api/v1", tags=["Test"])
app.include_router(calculations_router, prefix="/api/v1", tags=["Calculations"])

# Thread pool for background processing
executor = ThreadPoolExecutor(max_workers=10)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def read_root():
    """Home page endpoint"""
    return {"message": "Hello World"}


@app.on_event("startup")
async def startup_event():
    # Initialize the ThreadPoolExecutor on app startup
    app.state.executor = executor
    print("ThreadPoolExecutor started")


@app.on_event("shutdown")
async def shutdown_event():
    # Shutdown the ThreadPoolExecutor on app shutdown
    app.state.executor.shutdown()
    print("ThreadPoolExecutor shut down")


from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address)


# Add rate-limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except RateLimitExceeded as exc:
        # Customize the response for rate-limiting errors
        return JSONResponse(
            {"detail": "Rate limit exceeded. Try again later."}, status_code=429
        )


# Add limiter to an endpoint
@app.get("/health-woke-up")
@limiter.limit("2/minute")  # Limit to 5 requests per minute
async def health_check(request: Request):
    return {"status": "ok"}


# Handle RateLimitExceeded globally
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        {"detail": "Rate limit exceeded. Try again later."}, status_code=429
    )


if __name__ == "__main__":
    import uvicorn

    # Run the app locally with Uvicorn (useful for local testing and debugging)
    uvicorn.run(
        "main:app", host="0.0.0.0", port=8000, timeout_keep_alive=3600, reload=True
    )
