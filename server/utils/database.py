from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import config.config as _config
from utils.logger import logger


class DataBase(object):
    engine = None

    def start(self):
        logger.info(f"DataBase {_config.config['database']['url']} started")
        self.engine = create_async_engine(
            _config.config["database"]["url"],
            echo=True
        )

    def stop(self):
        logger.info(f"DataBase stopped")
        if self.engine:
            self.engine.dispose()

    def get_engine(self):
        return self.engine

    async def get_db(self):
        async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            yield session


database = DataBase()
