import time

from fastapi import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

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
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests by method, status code, and handler.",
    ["handler", "method", "status"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "Latency of HTTP requests in seconds by handler and method.",
    ["handler", "method"],
)


def setup_metrics(app) -> None:
    APP_UPTIME_SECONDS.set_function(lambda: time.time() - APP_STARTED_AT)

    @app.get("/metrics", include_in_schema=False, tags=["observability"])
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def observe_request(handler: str, method: str, status_code: int, duration: float) -> None:
    status_label = f"{status_code // 100}xx"
    HTTP_REQUESTS_TOTAL.labels(
        handler=handler,
        method=method,
        status=status_label,
    ).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(
        handler=handler,
        method=method,
    ).observe(duration)
