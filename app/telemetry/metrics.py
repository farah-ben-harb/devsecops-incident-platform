import time

from prometheus_client import Counter, Gauge
from prometheus_fastapi_instrumentator import Instrumentator

APP_STARTED_AT = time.time()

INCIDENT_CREATED_TOTAL = Counter(
    "incident_created_total",
    "Total number of incidents created.",
    ["service_name", "severity"],
)
API_ERROR_TOTAL = Counter(
    "api_error_total",
    "Total number of API responses with error status codes.",
    ["path", "method", "status_code"],
)
APP_UPTIME_SECONDS = Gauge(
    "app_uptime_seconds",
    "Number of seconds the application has been running.",
)


def setup_metrics(app) -> None:
    APP_UPTIME_SECONDS.set_function(lambda: time.time() - APP_STARTED_AT)
    Instrumentator(excluded_handlers=["/metrics"]).instrument(app).expose(
        app,
        include_in_schema=False,
        tags=["observability"],
    )

