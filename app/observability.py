import time
from collections.abc import Callable

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.requests import Request
from starlette.responses import Response


REQUEST_COUNT = Counter(
    "telco_rule_engine_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "telco_rule_engine_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
)
RISK_PREDICTIONS = Counter(
    "telco_rule_engine_predictions_total",
    "Total churn risk predictions",
    ["risk"],
)


async def metrics_endpoint() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


async def metrics_middleware(request: Request, call_next: Callable):
    started = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - started

    REQUEST_COUNT.labels(
        method=request.method, path=request.url.path, status=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(method=request.method, path=request.url.path).observe(elapsed)
    return response

