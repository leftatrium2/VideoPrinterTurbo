from config.config import config
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from utils.logger import logger


class DataBase(object):
    engine = None

    def start(self):
        logger.info(f"DataBase {config['database']['url']} started")
        self.engine = create_async_engine(
            config["database"]["url"],
            echo=True
        )

    def stop(self):
        logger.info(f"DataBase stopped")
        if self.engine:
            self.engine.dispose()

    async def get_db(self):
        async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            yield session


database = DataBase()
