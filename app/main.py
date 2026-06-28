import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.api.routes.health import router as health_router
from app.api.routes.incidents import router as incidents_router
from app.core.config import get_settings
from app.db.session import create_db_and_tables
from app.telemetry.metrics import API_ERROR_TOTAL, observe_request, setup_metrics

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Incident tracking API for a DevSecOps and GitOps portfolio platform.",
    lifespan=lifespan,
)


@app.middleware("http")
async def record_api_errors(request: Request, call_next):
    request_started = time.perf_counter()
    handler = request.url.path

    try:
        response = await call_next(request)
    except Exception:
        API_ERROR_TOTAL.labels(
            path=handler,
            method=request.method,
            status_code="500",
        ).inc()
        observe_request(
            handler=handler,
            method=request.method,
            status_code=500,
            duration=time.perf_counter() - request_started,
        )
        raise

    if response.status_code >= 400:
        API_ERROR_TOTAL.labels(
            path=handler,
            method=request.method,
            status_code=str(response.status_code),
        ).inc()

    observe_request(
        handler=handler,
        method=request.method,
        status_code=response.status_code,
        duration=time.perf_counter() - request_started,
    )

    return response


app.include_router(health_router)
app.include_router(incidents_router)
setup_metrics(app)
