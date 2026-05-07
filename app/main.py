from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api import eval as eval_api
from app.api import governance, ingest, query
from app.observability.logging import configure_logging
from app.observability.middleware import PrometheusMiddleware
from app.retrieval.qdrant_client import ensure_collection

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("MLflow initialized")
    ensure_collection()
    yield


app = FastAPI(title="rag-production-starter", version="0.1.0", lifespan=lifespan)

app.add_middleware(PrometheusMiddleware)


@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "ok"})


@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(governance.router)
app.include_router(eval_api.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
