"""Base router factory for v1 API endpoints."""

from fastapi import APIRouter


def new_router(dependencies=None):
    router = APIRouter()
    router.tags = ["V1"]
    router.prefix = "/api/v1"
    if dependencies:
        router.dependencies = dependencies
    return router
