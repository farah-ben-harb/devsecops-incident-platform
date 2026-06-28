from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.api.routes.health import router as health_router
from app.api.routes.incidents import router as incidents_router
from app.core.config import get_settings
from app.db.session import create_db_and_tables
from app.telemetry.metrics import API_ERROR_TOTAL, setup_metrics

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
    try:
        response = await call_next(request)
    except Exception:
        API_ERROR_TOTAL.labels(
            path=request.url.path,
            method=request.method,
            status_code="500",
        ).inc()
        raise

    if response.status_code >= 400:
        API_ERROR_TOTAL.labels(
            path=request.url.path,
            method=request.method,
            status_code=str(response.status_code),
        ).inc()

    return response


app.include_router(health_router)
app.include_router(incidents_router)
setup_metrics(app)

