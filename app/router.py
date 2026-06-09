"""Application routing — aggregates all API routers."""

from fastapi import APIRouter

from app.controllers.v1 import rewrite

root_api_router = APIRouter()
root_api_router.include_router(rewrite.router)
