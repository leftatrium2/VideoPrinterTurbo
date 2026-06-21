from contextlib import asynccontextmanager

from fastapi import FastAPI

import config.config as _config
from config.config import init_config
from middleware.cors_middleware import register_cors_middleware
from middleware.exception_middleware import register_exception_middleware
from pipeline.pipeline import init_downloader
from routers.asr_tts_config import router as asr_tts_config_router
from routers.index import router as index_router
from routers.llm_config import router as llm_config_router
from routers.material_config import router as material_config_router
from routers.publish_config import router as publish_config_router
from routers.tasks import router as tasks_router
from server.service.task_manager import task_manager
from utils.database import database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ========== 应用启动时执行（只运行一次） ==========
    task_manager.start()
    database.start()
    yield  # 服务正式开始运行，接收请求
    # ========== 应用关闭时执行（服务停止前） ==========
    task_manager.stop()
    database.stop()


init_config()
init_downloader()
app = FastAPI(
    title=_config.config['app']['name'],
    debug=_config.config['app']['debug'],
    version=_config.config['app']['version'],
    lifespan=lifespan,
)
# 注册中间件
register_cors_middleware(app)
register_exception_middleware(app)
# 注册路由
app.include_router(index_router)
app.include_router(tasks_router)
app.include_router(asr_tts_config_router)
app.include_router(llm_config_router)
app.include_router(material_config_router)
app.include_router(publish_config_router)
