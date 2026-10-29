import asyncio
import sqlite3
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from models.model import Base
from service.whisper_model_manager import WhisperModelManager


@pytest.mark.parametrize('legacy', [True, False])
def test_sqlite_database_is_migrated_idempotently(tmp_path, monkeypatch, legacy):
    import app as application
    target = tmp_path / 'legacy.db'
    engine = create_engine(f'sqlite:///{target.as_posix()}')
    Base.metadata.create_all(engine)
    engine.dispose()
    with sqlite3.connect(target) as db:
        if legacy:
            db.execute('ALTER TABLE vpt_asr_config DROP COLUMN local_whisper_model')
            db.execute('ALTER TABLE vpt_tasks DROP COLUMN format_id')
            db.execute('DROP TABLE vpt_lip_sync_config')
        db.execute('INSERT INTO vpt_asr_config DEFAULT VALUES')
        db.execute("INSERT INTO vpt_tasks (task_id, task_url) VALUES ('existing-task', 'https://example.com/video')")
        if not legacy:
            db.execute("INSERT INTO vpt_lip_sync_config (sync_labs_apikey, fal_latent_sync_apikey) "
                       "VALUES ('test-sync-key', 'test-fal-key')")
            db.execute("UPDATE vpt_tasks SET format_id = '270' WHERE task_id = 'existing-task'")
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
        columns = {row[1] for row in db.execute('PRAGMA table_info(vpt_lip_sync_config)')}
        assert {'id', 'sync_labs_apikey', 'fal_latent_sync_apikey', 'hey_gen_apikey'} <= columns
        lip_sync_rows = db.execute(
            'SELECT sync_labs_apikey, fal_latent_sync_apikey FROM vpt_lip_sync_config').fetchall()
        if legacy:
            assert lip_sync_rows == []  # upgrade creates the table without inventing credentials
            db.execute('INSERT INTO vpt_lip_sync_config DEFAULT VALUES')
            assert db.execute('SELECT sync_labs_apikey, fal_latent_sync_apikey '
                              'FROM vpt_lip_sync_config').fetchone() == ('', '')
        else:
            assert lip_sync_rows == [('test-sync-key', 'test-fal-key')]
        assert db.execute('SELECT local_whisper_model FROM vpt_asr_config').fetchone() == ('small',)
        assert db.execute('SELECT task_id, task_url, format_id FROM vpt_tasks').fetchone() == (
            'existing-task', 'https://example.com/video', '' if legacy else '270',
        )
        db.execute("INSERT INTO vpt_tasks (task_id, task_url) VALUES ('new-task', 'https://example.com/new')")
        assert db.execute("SELECT format_id FROM vpt_tasks WHERE task_id = 'new-task'").fetchone() == ('',)


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
