from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


# 跨域
def register_cors_middleware(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        # 允许跨域的源地址
        allow_origins=[
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            # "*" 表示允许所有域名(开发临时用，生产不推荐)
            # "*"
        ],
        allow_credentials=True,  # 允许携带 Cookie
        allow_methods=["*"],  # 允许所有请求方法: GET/POST/PUT/DELETE...
        allow_headers=["*"],  # 允许所有请求头
    )
