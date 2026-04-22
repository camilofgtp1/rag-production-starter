from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api import eval as eval_api
from app.api import governance, ingest, query
from app.config import settings
from app.retrieval.qdrant_client import ensure_collection


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_collection()
    yield


app = FastAPI(title="rag-production-starter", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "ok"})


app.include_router(ingest.router)
app.include_router(query.router)
app.include_router(governance.router)
app.include_router(eval_api.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)