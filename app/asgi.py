"""Application implementation — ASGI entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

import os
from app.config import config
from app.models.exception import HttpException
from app.router import root_api_router
from app.utils import utils


def exception_handler(request: Request, e: HttpException):
    return JSONResponse(
        status_code=e.status_code,
        content=utils.get_response(e.status_code, e.data, e.message),
    )


def validation_exception_handler(request: Request, e: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content=utils.get_response(400, e.errors(), "field required"),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("VideoPrinterTurbo started")
    yield
    logger.info("VideoPrinterTurbo shut down")


def get_application() -> FastAPI:
    instance = FastAPI(
        title=config.app.project_name,
        description="VideoPrinterTurbo — AI-powered video rewriting platform.",
        version=config.app.project_version,
        debug=False,
        lifespan=lifespan,
    )
    instance.include_router(root_api_router)
    instance.add_exception_handler(HttpException, exception_handler)
    instance.add_exception_handler(RequestValidationError, validation_exception_handler)
    return instance


app = get_application()

# CORS
cors_allowed_origins_str = os.getenv("CORS_ALLOWED_ORIGINS", "")
origins = cors_allowed_origins_str.split(",") if cors_allowed_origins_str else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directories
task_dir = utils.task_dir()
app.mount("/tasks", StaticFiles(directory=task_dir, html=True, follow_symlink=True), name="tasks")

public_dir = utils.public_dir()
app.mount("/", StaticFiles(directory=public_dir, html=True), name="public")
