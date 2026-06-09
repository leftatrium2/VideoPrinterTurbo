import copy
import pytest
from fastapi.testclient import TestClient

from app.asgi import app
from app.plugins.base import PluginRegistry
from app.services import state as sm
from app.services.state import MemoryState
from app.utils import utils as _utils


@pytest.fixture()
def state(monkeypatch):
    """Fresh MemoryState injected as the global sm.state."""
    s = MemoryState()
    monkeypatch.setattr(sm, "state", s)
    return s


@pytest.fixture()
def tmp_task_dir(tmp_path, monkeypatch):
    """Temp tasks directory; patches utils.task_dir() so handlers use it."""
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    monkeypatch.setattr(_utils, "task_dir", lambda sub_dir="": str(tasks))
    return tasks


@pytest.fixture()
def client(state, tmp_task_dir):
    """TestClient with isolated in-memory state and a temp task directory."""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def mock_task_manager(mocker):
    """Patch task_manager.add_task to a no-op so the pipeline never runs."""
    from app.controllers.v1 import rewrite
    return mocker.patch.object(rewrite.task_manager, "add_task")


@pytest.fixture()
def isolated_registry():
    """Save and restore PluginRegistry._plugins around each test."""
    original = copy.deepcopy(PluginRegistry._plugins)
    yield
    PluginRegistry._plugins = original
