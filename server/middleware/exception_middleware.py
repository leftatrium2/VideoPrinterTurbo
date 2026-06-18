from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from utils import const
from utils.exception import VPTException
from utils.result import result_failure
from starlette.exceptions import HTTPException as StarletteHTTPException


class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            return JSONResponse(status_code=500, content=result_failure(code=const.GLOBAL_ERR_UNKNOWN, message=str(e)))


async def vpt_exception_handler(request: Request, exc: VPTException):
    return JSONResponse(status_code=500, content=result_failure(code=exc.code, message=exc.message))


async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=404, content=result_failure(code=const.GLOBAL_ERR_UNKNOWN, message=str(exc)))


def register_exception_middleware(app: FastAPI):
    app.add_middleware(ExceptionMiddleware)
    app.add_exception_handler(VPTException, vpt_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
