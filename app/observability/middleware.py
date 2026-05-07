import re
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.observability.metrics import REQUEST_DURATION, REQUESTS_TOTAL

SKIP_PATHS = {"/metrics", "/health"}


def _normalize_path(path: str) -> str:
    normalized = re.sub(r"/[a-f0-9-]{8,}", "/{id}", path)
    return normalized


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in SKIP_PATHS:
            return await call_next(request)

        start_time = time.perf_counter()
        response: Response = await call_next(request)
        duration = time.perf_counter() - start_time

        endpoint = _normalize_path(request.url.path)
        method = request.method
        status_code = str(response.status_code)

        REQUESTS_TOTAL.labels(
            endpoint=endpoint, method=method, status_code=status_code
        ).inc()
        REQUEST_DURATION.labels(endpoint=endpoint).observe(duration)

        return response
