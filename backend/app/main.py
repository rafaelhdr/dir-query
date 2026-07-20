import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import ask, files, health, uploads, workspaces
from app.rag import index_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(index_service.sync_pending_files())
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Understand Your Stuffs API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(health.router)
    app.include_router(uploads.router)
    app.include_router(files.router)
    app.include_router(ask.router)
    app.include_router(workspaces.router)
    return app


app = create_app()
