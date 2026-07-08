from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, scoped_session

import config.config as _config
from utils.logger import logger


class DataBase(object):
    engine = None
    sync_engine = None
    _sync_session_factory = None
    _scoped_session = None

    def start(self):
        logger.info(f"DataBase {_config.config['database']['url']} started")
        self.engine = create_async_engine(
            _config.config["database"]["url"],
            echo=True
        )
        sync_url = _config.config["database"]["url"].replace("+aiosqlite", "")
        self.sync_engine = create_engine(sync_url, echo=True)
        self._sync_session_factory = sessionmaker(bind=self.sync_engine)
        self._scoped_session = scoped_session(self._sync_session_factory)

    def stop(self):
        logger.info(f"DataBase stopped")
        if self._scoped_session:
            self._scoped_session.remove()
        if self.sync_engine:
            self.sync_engine.dispose()
        if self.engine:
            self.engine.dispose()

    def get_engine(self):
        return self.engine

    def get_sync_session(self):
        return self._scoped_session()

    def remove_sync_session(self):
        if self._scoped_session:
            self._scoped_session.remove()

    async def get_db(self):
        async_session = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            yield session


database = DataBase()
