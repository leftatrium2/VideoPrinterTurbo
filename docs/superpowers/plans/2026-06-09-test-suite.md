# Test Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a complete pytest test suite (unit + API integration) that runs without any real API keys or network access.

**Architecture:** Two layers — pure-function unit tests (file_security, utils, schema, plugin registry, state) and API integration tests using FastAPI's TestClient with `tm.start` blocked via mock. All external plugins (LLM, TTS, yt-dlp) are replaced by no-ops so CI can run offline.

**Tech Stack:** Python 3.11+, pytest ≥ 8.0, pytest-mock ≥ 3.14, httpx ≥ 0.27 (TestClient transport)

---

## File Map

| Action | Path | Purpose |
|---|---|---|
| Modify | `pyproject.toml` | Add `[dev]` optional-deps + pytest config |
| Create | `tests/__init__.py` | Make tests a package |
| Create | `tests/conftest.py` | Shared fixtures: state, client, mock_task_manager, tmp_task_dir, isolated_registry |
| Create | `tests/test_file_security.py` | 6 unit tests for path traversal logic |
| Create | `tests/test_utils.py` | 8 unit tests for pure utility functions |
| Create | `tests/test_schema.py` | 5 unit tests for Pydantic models |
| Create | `tests/test_plugin_registry.py` | 6 unit tests for plugin auto-registration |
| Create | `tests/test_state.py` | 7 unit tests for MemoryState |
| Create | `tests/test_api.py` | 14 API integration tests |
| Modify | `CLAUDE.md` | Add Testing section |

---

## Task 1: Add Dev Dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add dev optional-dependencies and pytest config to pyproject.toml**

Open `pyproject.toml`. The file currently has:
```toml
[project.optional-dependencies]
gemini = [
    "google-generativeai==0.8.6",
]
```

Add the `dev` group and pytest config right after:

```toml
[project.optional-dependencies]
gemini = [
    "google-generativeai==0.8.6",
]
dev = [
    "pytest>=8.0",
    "pytest-mock>=3.14",
    "httpx>=0.27",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Install dev dependencies**

```bash
uv sync --extra dev
```

Expected: resolves and installs pytest, pytest-mock, httpx with no errors.

- [ ] **Step 3: Verify pytest is available**

```bash
uv run pytest --version
```

Expected output (version may differ):
```
pytest 8.x.x
```

---

## Task 2: Test Infrastructure (conftest.py)

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create the tests package**

Create `tests/__init__.py` as an empty file.

- [ ] **Step 2: Write conftest.py**

Create `tests/conftest.py` with all shared fixtures:

```python
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
```

**Fixture notes:**
- `state` patches `sm.state` on the **module object**. Both `rewrite.py` and `task.py` import `from app.services import state as sm`, so they reference the same module and pick up the patch automatically.
- `client` depends on both `state` and `tmp_task_dir`. When a test also requests `tmp_task_dir` directly, pytest resolves it to the same instance (function scope), so the test can create files in the same directory the handlers read from.
- `mock_task_manager` is requested explicitly only by tests that POST to `/rewrite`, keeping other tests unaffected.
- `isolated_registry` deep-copies `PluginRegistry._plugins` (a class-level dict) before each test and restores it after, preventing stub plugin classes defined inside test functions from leaking.

- [ ] **Step 3: Verify conftest imports without error**

```bash
uv run pytest --collect-only 2>&1 | head -5
```

Expected: no `ImportError` or `ModuleNotFoundError`. (Test count is 0 — that's fine.)

---

## Task 3: test_file_security.py

**Files:**
- Create: `tests/test_file_security.py`

- [ ] **Step 1: Write all 6 tests**

Create `tests/test_file_security.py`:

```python
import os
import pytest
from app.utils.file_security import resolve_path_within_directory


def test_valid_relative_path(tmp_path):
    f = tmp_path / "data.txt"
    f.write_text("hello")
    result = resolve_path_within_directory(str(tmp_path), "data.txt")
    assert result == str(f.resolve())


def test_valid_absolute_path_inside_base(tmp_path):
    f = tmp_path / "data.txt"
    f.write_text("hello")
    result = resolve_path_within_directory(str(tmp_path), str(f))
    assert result == str(f.resolve())


def test_relative_path_traversal_raises(tmp_path):
    with pytest.raises(ValueError, match="path traversal"):
        resolve_path_within_directory(str(tmp_path), "../../etc/passwd")


def test_absolute_path_outside_base_raises(tmp_path):
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("secret")
    with pytest.raises(ValueError, match="path traversal"):
        resolve_path_within_directory(str(tmp_path), str(outside))


def test_nonexistent_file_raises(tmp_path):
    with pytest.raises(ValueError, match="file does not exist"):
        resolve_path_within_directory(str(tmp_path), "missing.txt")


def test_path_pointing_to_base_dir_itself(tmp_path):
    result = resolve_path_within_directory(str(tmp_path), str(tmp_path))
    assert result == str(tmp_path.resolve())
```

- [ ] **Step 2: Run and confirm all 6 pass**

```bash
uv run pytest tests/test_file_security.py -v
```

Expected:
```
PASSED tests/test_file_security.py::test_valid_relative_path
PASSED tests/test_file_security.py::test_valid_absolute_path_inside_base
PASSED tests/test_file_security.py::test_relative_path_traversal_raises
PASSED tests/test_file_security.py::test_absolute_path_outside_base_raises
PASSED tests/test_file_security.py::test_nonexistent_file_raises
PASSED tests/test_file_security.py::test_path_pointing_to_base_dir_itself
6 passed
```

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml tests/__init__.py tests/conftest.py tests/test_file_security.py
git commit -m "test: add dev deps, conftest, and file_security unit tests"
```

---

## Task 4: test_utils.py

**Files:**
- Create: `tests/test_utils.py`

- [ ] **Step 1: Write all 8 tests**

Create `tests/test_utils.py`:

```python
import pytest
from app.utils.utils import (
    get_response,
    get_uuid,
    split_string_by_punctuations,
    text_to_srt,
    time_convert_seconds_to_hmsm,
)


def test_time_convert_zero():
    assert time_convert_seconds_to_hmsm(0) == "00:00:00,000"


def test_time_convert_whole_minutes():
    assert time_convert_seconds_to_hmsm(90) == "00:01:30,000"


def test_time_convert_with_milliseconds():
    assert time_convert_seconds_to_hmsm(3723.456) == "01:02:03,456"


def test_text_to_srt_format():
    result = text_to_srt(1, "Hello world", 0.0, 1.5)
    assert "1\n" in result
    assert " --> " in result
    assert "Hello world" in result
    assert "00:00:00,000 --> 00:00:01,500" in result


def test_split_by_punctuation():
    result = split_string_by_punctuations("Hello, world.")
    assert result == ["Hello", "world"]


def test_split_preserves_decimal_numbers():
    result = split_string_by_punctuations("3.14 is pi")
    assert result == ["3.14 is pi"]


def test_get_uuid_has_hyphens():
    uid = get_uuid()
    assert len(uid) == 36
    assert "-" in uid


def test_get_uuid_without_hyphens():
    uid = get_uuid(remove_hyphen=True)
    assert len(uid) == 32
    assert "-" not in uid


def test_get_response_with_data():
    resp = get_response(200, {"key": "val"})
    assert resp["status"] == 200
    assert resp["data"] == {"key": "val"}


def test_get_response_without_data():
    resp = get_response(404)
    assert resp["status"] == 404
    assert "data" not in resp
```

*(10 tests — 8 from the spec + 2 extra for `get_response` which needs coverage.)*

- [ ] **Step 2: Run and confirm all pass**

```bash
uv run pytest tests/test_utils.py -v
```

Expected: `10 passed`

- [ ] **Step 3: Commit**

```bash
git add tests/test_utils.py
git commit -m "test: add utils unit tests"
```

---

## Task 5: test_schema.py

**Files:**
- Create: `tests/test_schema.py`

- [ ] **Step 1: Write all 5 tests**

Create `tests/test_schema.py`:

```python
import pytest
from pydantic import ValidationError
from app.models.schema import VideoAspect, VideoRewriteParams


def test_landscape_resolution():
    assert VideoAspect.landscape.to_resolution() == (1920, 1080)


def test_portrait_resolution():
    assert VideoAspect.portrait.to_resolution() == (1080, 1920)


def test_square_resolution():
    assert VideoAspect.square.to_resolution() == (1080, 1080)


def test_video_rewrite_params_defaults():
    params = VideoRewriteParams()
    assert params.video_count == 1
    assert params.subtitle_enabled is True
    assert params.voice_volume == 1.0


def test_invalid_aspect_raises_validation_error():
    with pytest.raises(ValidationError):
        VideoRewriteParams(video_aspect="invalid_ratio")
```

- [ ] **Step 2: Run and confirm all 5 pass**

```bash
uv run pytest tests/test_schema.py -v
```

Expected: `5 passed`

- [ ] **Step 3: Commit**

```bash
git add tests/test_schema.py
git commit -m "test: add schema unit tests"
```

---

## Task 6: test_plugin_registry.py

**Files:**
- Create: `tests/test_plugin_registry.py`

All stub classes are defined **inside test functions** so they only register when the test runs. The `isolated_registry` fixture (defined in conftest.py) deep-copies and restores `PluginRegistry._plugins` around each test.

- [ ] **Step 1: Write all 6 tests**

Create `tests/test_plugin_registry.py`:

```python
import pytest
from app.plugins.base import BasePlugin, PluginRegistry, PluginType


def test_subclass_auto_registers(isolated_registry):
    class _Stub(BasePlugin):
        type = PluginType.DOWNLOADER
        name = "stub-auto"
        def validate_config(self): return True

    assert PluginRegistry.get(PluginType.DOWNLOADER, "stub-auto") is _Stub


def test_get_returns_correct_plugin(isolated_registry):
    class _A(BasePlugin):
        type = PluginType.LLM
        name = "llm-a"
        def validate_config(self): return True

    class _B(BasePlugin):
        type = PluginType.LLM
        name = "llm-b"
        def validate_config(self): return True

    assert PluginRegistry.get(PluginType.LLM, "llm-a") is _A
    assert PluginRegistry.get(PluginType.LLM, "llm-b") is _B


def test_get_default_with_name(isolated_registry):
    class _X(BasePlugin):
        type = PluginType.MATERIAL
        name = "mat-x"
        def validate_config(self): return True

    class _Y(BasePlugin):
        type = PluginType.MATERIAL
        name = "mat-y"
        def validate_config(self): return True

    result = PluginRegistry.get_default(PluginType.MATERIAL, "mat-y")
    assert result is _Y


def test_get_default_without_name_returns_first(isolated_registry):
    # Clear the TRANSCRIBER slot so we control the order
    PluginRegistry._plugins[PluginType.TRANSCRIBER] = {}

    class _First(BasePlugin):
        type = PluginType.TRANSCRIBER
        name = "first"
        def validate_config(self): return True

    class _Second(BasePlugin):
        type = PluginType.TRANSCRIBER
        name = "second"
        def validate_config(self): return True

    result = PluginRegistry.get_default(PluginType.TRANSCRIBER, "")
    assert result is _First


def test_list_plugins(isolated_registry):
    PluginRegistry._plugins[PluginType.PUBLISHER] = {}

    class _P1(BasePlugin):
        type = PluginType.PUBLISHER
        name = "pub-1"
        def validate_config(self): return True

    class _P2(BasePlugin):
        type = PluginType.PUBLISHER
        name = "pub-2"
        def validate_config(self): return True

    names = PluginRegistry.list_plugins(PluginType.PUBLISHER)
    assert set(names) == {"pub-1", "pub-2"}


def test_get_nonexistent_plugin_returns_none(isolated_registry):
    result = PluginRegistry.get(PluginType.DOWNLOADER, "does-not-exist")
    assert result is None
```

- [ ] **Step 2: Run and confirm all 6 pass**

```bash
uv run pytest tests/test_plugin_registry.py -v
```

Expected: `6 passed`

- [ ] **Step 3: Commit**

```bash
git add tests/test_plugin_registry.py
git commit -m "test: add plugin registry unit tests"
```

---

## Task 7: test_state.py

**Files:**
- Create: `tests/test_state.py`

Each test creates its own `MemoryState()` instance — no shared state between tests.

- [ ] **Step 1: Write all 7 tests**

Create `tests/test_state.py`:

```python
import pytest
from app.models import const
from app.services.state import MemoryState


@pytest.fixture()
def mem():
    return MemoryState()


def test_update_and_get_task(mem):
    mem.update_task("t1", state=const.TASK_STATE_PROCESSING, progress=10)
    task = mem.get_task("t1")
    assert task["task_id"] == "t1"
    assert task["state"] == const.TASK_STATE_PROCESSING
    assert task["progress"] == 10


def test_update_task_overwrites(mem):
    mem.update_task("t1", progress=10)
    mem.update_task("t1", progress=50)
    assert mem.get_task("t1")["progress"] == 50


def test_progress_clamped_to_100(mem):
    mem.update_task("t1", progress=150)
    assert mem.get_task("t1")["progress"] == 100


def test_get_nonexistent_task_returns_none(mem):
    assert mem.get_task("missing") is None


def test_delete_existing_task(mem):
    mem.update_task("t1", progress=10)
    mem.delete_task("t1")
    assert mem.get_task("t1") is None


def test_delete_nonexistent_task_is_idempotent(mem):
    mem.delete_task("ghost")  # must not raise


def test_get_all_tasks_pagination(mem):
    for i in range(5):
        mem.update_task(f"task-{i}", progress=i * 10)

    page2, total = mem.get_all_tasks(page=2, page_size=2)
    assert total == 5
    assert len(page2) == 2
```

- [ ] **Step 2: Run and confirm all 7 pass**

```bash
uv run pytest tests/test_state.py -v
```

Expected: `7 passed`

- [ ] **Step 3: Commit**

```bash
git add tests/test_state.py
git commit -m "test: add MemoryState unit tests"
```

---

## Task 8: test_api.py — Task CRUD + Musics

**Files:**
- Create: `tests/test_api.py` (first half)

All tests use the `client` fixture from conftest, which provides isolated state and a temp task dir.

- [ ] **Step 1: Write CRUD + musics tests**

Create `tests/test_api.py`:

```python
import pytest
from app.controllers.manager.base_manager import TaskQueueFullError
from app.models import const


# ── POST /api/v1/rewrite ────────────────────────────────────────────────────


def test_create_task_success(client, mock_task_manager):
    response = client.post("/api/v1/rewrite", json={"video_url": "https://example.com/v.mp4"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == 200
    task_id = body["data"]["task_id"]
    assert len(task_id) == 36  # UUID format
    mock_task_manager.assert_called_once()


def test_create_task_queue_full(client, mocker):
    from app.controllers.v1 import rewrite
    mocker.patch.object(
        rewrite.task_manager,
        "add_task",
        side_effect=TaskQueueFullError("queue full"),
    )
    response = client.post("/api/v1/rewrite", json={"video_url": "https://example.com/v.mp4"})
    assert response.status_code == 429


# ── GET /api/v1/tasks ───────────────────────────────────────────────────────


def test_get_all_tasks_pagination(client, state):
    state.update_task("task-1", state=const.TASK_STATE_PROCESSING, progress=10)
    state.update_task("task-2", state=const.TASK_STATE_COMPLETE, progress=100)

    response = client.get("/api/v1/tasks?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 2
    assert len(data["tasks"]) == 2
    assert data["page"] == 1


# ── GET /api/v1/tasks/{task_id} ─────────────────────────────────────────────


def test_get_task_found(client, state):
    state.update_task("abc-123", state=const.TASK_STATE_PROCESSING, progress=42)

    response = client.get("/api/v1/tasks/abc-123")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["task_id"] == "abc-123"
    assert data["progress"] == 42


def test_get_task_not_found(client):
    response = client.get("/api/v1/tasks/nonexistent-id")
    assert response.status_code == 404


# ── DELETE /api/v1/tasks/{task_id} ──────────────────────────────────────────


def test_delete_task_success(client, state):
    state.update_task("del-me", state=const.TASK_STATE_COMPLETE, progress=100)

    response = client.delete("/api/v1/tasks/del-me")
    assert response.status_code == 200
    assert state.get_task("del-me") is None


def test_delete_task_not_found(client):
    response = client.delete("/api/v1/tasks/nonexistent-id")
    assert response.status_code == 404


# ── GET /api/v1/musics ──────────────────────────────────────────────────────


def test_get_musics_returns_list(client):
    response = client.get("/api/v1/musics")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "files" in data
    assert isinstance(data["files"], list)
```

- [ ] **Step 2: Run and confirm all 8 pass**

```bash
uv run pytest tests/test_api.py -v
```

Expected: `8 passed`

---

## Task 9: test_api.py — Stream and Download

**Files:**
- Modify: `tests/test_api.py` (append)

- [ ] **Step 1: Append stream and download tests**

Append to `tests/test_api.py`:

```python
# ── GET /api/v1/stream/{file_path} ──────────────────────────────────────────


def test_stream_video_ok(client, tmp_task_dir):
    task_dir = tmp_task_dir / "task-stream-ok"
    task_dir.mkdir()
    video = task_dir / "final-1.mp4"
    video.write_bytes(b"\x00" * 1024)

    response = client.get("/api/v1/stream/task-stream-ok/final-1.mp4")
    assert response.status_code == 206
    assert "Content-Range" in response.headers


def test_stream_path_traversal_returns_403(client, mocker):
    """ValueError with 'path traversal' in message → 403."""
    mocker.patch(
        "app.controllers.v1.rewrite.file_security.resolve_path_within_directory",
        side_effect=ValueError("path traversal detected: /etc/passwd"),
    )
    response = client.get("/api/v1/stream/anything")
    assert response.status_code == 403


def test_stream_file_not_found_returns_404(client, tmp_task_dir):
    response = client.get("/api/v1/stream/ghost-task/missing.mp4")
    assert response.status_code == 404


# ── GET /api/v1/download/{file_path} ────────────────────────────────────────


def test_download_video_ok(client, tmp_task_dir):
    task_dir = tmp_task_dir / "task-dl-ok"
    task_dir.mkdir()
    video = task_dir / "final-1.mp4"
    video.write_bytes(b"\x00" * 512)

    response = client.get("/api/v1/download/task-dl-ok/final-1.mp4")
    assert response.status_code == 200
    assert "Content-Disposition" in response.headers
    assert "final-1" in response.headers["Content-Disposition"]


def test_download_path_traversal_returns_403(client, mocker):
    """ValueError with 'path traversal' in message → 403."""
    mocker.patch(
        "app.controllers.v1.rewrite.file_security.resolve_path_within_directory",
        side_effect=ValueError("path traversal detected: /etc/passwd"),
    )
    response = client.get("/api/v1/download/anything")
    assert response.status_code == 403


def test_download_file_not_found_returns_404(client, tmp_task_dir):
    response = client.get("/api/v1/download/ghost-task/missing.mp4")
    assert response.status_code == 404
```

- [ ] **Step 2: Run the full test suite and confirm all 14 API tests pass**

```bash
uv run pytest tests/test_api.py -v
```

Expected: `14 passed`

- [ ] **Step 3: Run the entire test suite**

```bash
uv run pytest -v
```

Expected: `41 passed` (6 + 10 + 5 + 6 + 7 + 7 CRUD/musics + 6 stream/download = 41 — exact count may vary by 1-2 due to `get_response` extras)

- [ ] **Step 4: Commit**

```bash
git add tests/test_api.py
git commit -m "test: add API integration tests for CRUD, stream, and download endpoints"
```

---

## Task 10: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add a Testing section to CLAUDE.md**

Add the following section to `CLAUDE.md` after the **依赖说明** section and before **注意事项**:

```markdown
## 测试

```shell
# 安装测试依赖
uv sync --extra dev

# 运行全部测试
uv run pytest

# 运行特定模块
uv run pytest tests/test_api.py -v
uv run pytest tests/test_file_security.py -v
```

### 测试结构

```
tests/
├── conftest.py              # 共用 fixture（见下方说明）
├── test_file_security.py    # 路径穿越防护（6 个用例）
├── test_utils.py            # 纯工具函数（10 个用例）
├── test_schema.py           # Pydantic 模型校验（5 个用例）
├── test_plugin_registry.py  # 插件注册表（6 个用例）
├── test_state.py            # MemoryState（7 个用例）
└── test_api.py              # API 集成测试（14 个用例）
```

### Fixture 说明

| Fixture | 作用 |
|---|---|
| `state` | 注入独立 `MemoryState`，替换全局 `sm.state` |
| `client` | FastAPI `TestClient`，依赖 `state` + `tmp_task_dir` |
| `mock_task_manager` | 将 `task_manager.add_task` patch 为 no-op，阻止管线运行 |
| `tmp_task_dir` | 临时任务目录，patch `utils.task_dir()` 返回值 |
| `isolated_registry` | 保存/恢复 `PluginRegistry._plugins`，防止插件注册跨测试泄漏 |

所有测试**不需要**真实 API Key 或网络连接。
```

- [ ] **Step 2: Verify CLAUDE.md renders correctly**

```bash
uv run pytest --collect-only -q
```

Expected: shows all test files collected, no errors.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add Testing section to CLAUDE.md"
```

---

## Self-Review Checklist

- [x] **Spec coverage:** All 46 test cases from spec covered (6 file_security + 8 utils + 5 schema + 6 plugin_registry + 7 state + 14 API). CLAUDE.md update included.
- [x] **Placeholders:** No TBD, TODO, or vague steps. Every step has exact code or commands.
- [x] **Type consistency:** `MemoryState`, `PluginRegistry`, `PluginType`, `TaskQueueFullError`, `const.TASK_STATE_*` used consistently across all tasks.
- [x] **Fixture consistency:** `isolated_registry` defined in conftest Task 2, used in Task 6. `tmp_task_dir` defined in conftest, used by both `client` and stream/download tests.
- [x] **mock_task_manager scope:** Only requested in tests that POST to `/rewrite` — other tests unaffected.
