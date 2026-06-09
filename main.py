"""Entry point — starts the FastAPI / Uvicorn server."""

import uvicorn
from loguru import logger

from app.config import config

if __name__ == "__main__":
    logger.info(
        f"start server, docs: http://127.0.0.1:{config.app.listen_port}/docs"
    )
    uvicorn.run(
        app="app.asgi:app",
        host=config.app.listen_host,
        port=config.app.listen_port,
        reload=False,
        log_level="warning",
    )
