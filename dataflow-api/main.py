from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import audit, bts_configs, connectors, connections, pipeline_configs
from app.schemas.common import success_response
from database.init_db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="DataFlow API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(connectors.router, prefix="/api/v1")
app.include_router(connections.router, prefix="/api/v1")
app.include_router(pipeline_configs.router, prefix="/api/v1")
app.include_router(bts_configs.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")


@app.get("/health")
def health():
    return success_response({"healthy": True})
