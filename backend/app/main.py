"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.app.api.v1.endpoints.predict import load_model
from backend.app.api.v1.router import api_router
from backend.app.core.config import settings

import sys
from pathlib import Path



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the inference artifact once when the application starts."""
    app.state.model = load_model()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: object, exc: RequestValidationError
) -> JSONResponse:
    """Expose invalid prediction payloads as client errors rather than model errors."""
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid laptop data: " + "; ".join(
            error["msg"] for error in exc.errors()
        )},
    )


app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    return {
        "message": settings.PROJECT_NAME,
        "docs": "/docs",
        "api": settings.API_V1_STR,
    }
