from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.config import config
from routers.asr_tts_config import router as asr_tts_config_router
from routers.index import router as index_router
from routers.llm_config import router as llm_config_router
from routers.material_config import router as material_config_router
from routers.publish_config import router as publish_config_router
from routers.tasks import router as tasks_router
from server.service.task_manager import task_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ========== 应用启动时执行（只运行一次） ==========
    task_manager.start()
    yield  # 服务正式开始运行，接收请求
    # ========== 应用关闭时执行（服务停止前） ==========
    task_manager.stop()


app = FastAPI(
    title=config['app']['name'],
    debug=config['app']['debug'],
    version=config['app']['version'],
    lifespan=lifespan,
)
# 跨域
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
app.include_router(index_router)
app.include_router(tasks_router)
app.include_router(asr_tts_config_router)
app.include_router(llm_config_router)
app.include_router(material_config_router)
app.include_router(publish_config_router)
