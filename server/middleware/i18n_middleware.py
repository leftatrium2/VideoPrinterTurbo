from contextvars import ContextVar

from fastapi import FastAPI
from starlette.types import ASGIApp, Receive, Scope, Send

i18n_ctx: ContextVar[str] = ContextVar("i18n_ctx", default="cn")


class I18nMiddleware:
    def __init__(self, app: ASGIApp, header_name: str = "X-I18n"):
        self.app = app
        self.header_name = header_name

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        header_key = self.header_name.lower().encode()
        lang = headers.get(header_key, b"cn").decode()
        token = i18n_ctx.set(lang)
        try:
            await self.app(scope, receive, send)
        finally:
            i18n_ctx.reset(token)


def get_current_lang() -> str:
    return i18n_ctx.get()


def register_i18n_middleware(app: FastAPI):
    app.add_middleware(I18nMiddleware)
