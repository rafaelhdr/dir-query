import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ask, auth, conversations, files, health, workspaces
from app.rag import index_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(index_service.sync_pending_files())
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Dir Query API",
        version="0.1.0",
        lifespan=lifespan,
    )
    # Workspace lookup and question-answering are already public and
    # unauthenticated, and the embeddable widget (see the website-widget
    # capability) needs to call them from arbitrary third-party origins —
    # so this is open to any origin. allow_credentials stays False since
    # auth here is a bearer token from localStorage, never a cookie, so
    # wildcard CORS can't be used to forge an authenticated request.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(files.router)
    app.include_router(ask.router)
    app.include_router(conversations.router)
    app.include_router(workspaces.router)
    return app


app = create_app()
