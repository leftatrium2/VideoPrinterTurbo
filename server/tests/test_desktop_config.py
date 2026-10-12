import asyncio
import sqlite3
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from models.model import Base
from service.whisper_model_manager import WhisperModelManager


def test_old_sqlite_database_is_migrated_idempotently(tmp_path, monkeypatch):
    import app as application
    target = tmp_path / 'legacy.db'
    engine = create_engine(f'sqlite:///{target.as_posix()}')
    Base.metadata.create_all(engine)
    engine.dispose()
    with sqlite3.connect(target) as db:
        db.execute('ALTER TABLE vpt_asr_config DROP COLUMN local_whisper_model')
        db.execute('INSERT INTO vpt_asr_config DEFAULT VALUES')
    monkeypatch.setitem(application._config.config['database'], 'url', f'sqlite+aiosqlite:///{target.as_posix()}')
    monkeypatch.setattr(application, 'gen_config', AsyncMock())
    monkeypatch.setattr(application.task_manager, 'start', AsyncMock())
    monkeypatch.setattr(application.task_manager, 'stop', AsyncMock())

    async def boot_twice():
        for _ in range(2):
            async with application.lifespan(application.app):
                pass

    asyncio.run(boot_twice())
    with sqlite3.connect(target) as db:
        assert db.execute('SELECT local_whisper_model FROM vpt_asr_config').fetchone() == ('small',)


def test_model_api_validates_input_and_returns_status(tmp_path, monkeypatch):
    import routers.asr_config as routes
    monkeypatch.setattr(routes, 'model_manager', WhisperModelManager(tmp_path))
    app = FastAPI()
    app.include_router(routes.router)
    with TestClient(app) as client:
        listing = client.get('/asr_config/local_model_list').json()
        assert listing['code'] == 0
        assert len(listing['data']) == 5
        assert client.get('/asr_config/local_model_status', params={'model': '../bad'}).status_code == 400
        assert client.post('/asr_config/local_model_download', json={'model': '../bad'}).status_code == 400
