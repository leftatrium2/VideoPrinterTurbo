from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

import config.config as _config
from config.config import init_config
from middleware.cors_middleware import register_cors_middleware
from middleware.i18n_middleware import register_i18n_middleware
from models.model import Base
from pipeline.pipeline import init_downloader
from routers.asr_config import router as asr_config_router
from routers.index import router as index_router
from routers.llm_config import router as llm_config_router
from routers.material_config import router as material_config_router
from routers.proxy_config import router as proxy_config_router
from routers.publish_config import router as publish_config_router
from routers.tasks import router as tasks_router
from routers.tts_config import router as tts_config_router
from server.service.task_manager import task_manager
from utils.database import database
from utils.gen_config import gen_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ========== Executed on application startup (run once only) ==========
    database.start()
    # Database creation
    async with database.get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Sync config
    # Start task manager
    async_session_factory = sessionmaker(database.get_engine(), class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        await gen_config(db=session)
        await task_manager.start()
    yield  # Server officially started, accepting requests
    # ========== Executed on application shutdown (before server stops) ==========
    database.stop()
    await task_manager.stop()


init_config()
init_downloader()
app = FastAPI(
    title=_config.config['app']['name'],
    debug=_config.config['app']['debug'],
    version=_config.config['app']['version'],
    lifespan=lifespan,
)
# Register middleware
register_cors_middleware(app)
# register_exception_middleware(app)
# register i18n middleware
register_i18n_middleware(app)

# Register routers
app.include_router(index_router)
app.include_router(tasks_router)
app.include_router(tts_config_router)
app.include_router(asr_config_router)
app.include_router(llm_config_router)
app.include_router(material_config_router)
app.include_router(publish_config_router)
app.include_router(proxy_config_router)
