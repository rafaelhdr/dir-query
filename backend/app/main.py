import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import ask, health, uploads
from app.rag import index_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(asyncio.to_thread(index_service.sync_index))
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Understand Your Stuffs API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(health.router)
    app.include_router(uploads.router)
    app.include_router(ask.router)
    return app


app = create_app()
