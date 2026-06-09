# Test Suite Design — VideoPrinterTurbo

**Date:** 2026-06-09
**Scope:** 分层测试套件（单元测试 + API 集成测试）
**Framework:** pytest + pytest-mock + httpx

---

## 目标

在不依赖任何真实 API Key 或外部网络的前提下，验证：

1. 纯逻辑函数的正确性（utils、file_security、schema、plugin registry、state）
2. 所有 API 端点的行为（状态码、响应结构、路径安全、错误处理）

管线插件（yt-dlp、LLM、TTS、素材搜索）通过 mock 替换，不执行真实调用。

---

## 依赖变更

`pyproject.toml` 新增 dev 可选依赖组：

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-mock>=3.14",
    "httpx>=0.27",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

安装命令：`uv sync --extra dev` 或 `pip install -e ".[dev]"`

---

## 目录结构

```
tests/
├── conftest.py              # 共用 fixture
├── test_utils.py            # app/utils/utils.py
├── test_file_security.py    # app/utils/file_security.py
├── test_schema.py           # app/models/schema.py
├── test_plugin_registry.py  # app/plugins/base.py
├── test_state.py            # app/services/state.py MemoryState
└── test_api.py              # API 集成测试
```

---

## conftest.py

提供三个共用 fixture：

| Fixture | 作用 |
|---|---|
| `client` | FastAPI `TestClient`，替换全局 `sm.state` 为独立 `MemoryState` 实例 |
| `mock_task_manager` | 将 `task_manager.add_task` patch 为 no-op，阻止真实管线运行 |
| `tmp_task_dir` | `tmp_path` 下创建 tasks 目录，测后由 pytest 自动清理 |

`tm.start` 不在此 mock，而是通过 `mock_task_manager` 使 `add_task` 成为 no-op 来阻止调度。

---

## 单元测试规格

### test_file_security.py（6 个用例）

| 用例 | 输入 | 期望结果 |
|---|---|---|
| 正常相对路径 | `base=/tmp/foo`，`path=bar/file.txt`（文件存在） | 返回绝对路径 |
| 绝对路径在白名单内 | `base=/tmp/foo`，`path=/tmp/foo/bar.txt`（存在） | 返回该绝对路径 |
| `../` 路径穿越 | `base=/tmp/foo`，`path=../../etc/passwd` | `ValueError`（含 "path traversal"） |
| 绝对路径逃逸白名单 | `base=/tmp/foo`，`path=/tmp/evil.txt`（存在） | `ValueError`（含 "path traversal"） |
| 文件不存在 | `base=/tmp/foo`，`path=missing.txt` | `ValueError`（含 "file does not exist"） |
| 路径指向白名单根目录 | `base=/tmp/foo`，`path=/tmp/foo`（目录存在） | 返回根目录路径 |

### test_utils.py（8 个用例）

| 用例 | 函数 | 输入 | 期望 |
|---|---|---|---|
| 零秒 | `time_convert_seconds_to_hmsm` | `0` | `"00:00:00,000"` |
| 整分钟 | `time_convert_seconds_to_hmsm` | `90` | `"00:01:30,000"` |
| 带毫秒 | `time_convert_seconds_to_hmsm` | `3723.456` | `"01:02:03,456"` |
| SRT 格式 | `text_to_srt` | `idx=1, msg="Hello", start=0.0, end=1.5` | 含 `"1\n"`, `" --> "`, `"Hello"` |
| 标点切割 | `split_string_by_punctuations` | `"Hello, world."` | `["Hello", "world"]` |
| 数字小数点不切割 | `split_string_by_punctuations` | `"3.14 is pi"` | `["3.14 is pi"]` |
| UUID 带连字符 | `get_uuid()` | — | 长度 36，含 `-` |
| UUID 无连字符 | `get_uuid(remove_hyphen=True)` | — | 长度 32，不含 `-` |

### test_schema.py（5 个用例）

| 用例 | 目标 | 期望 |
|---|---|---|
| landscape 分辨率 | `VideoAspect.landscape.to_resolution()` | `(1920, 1080)` |
| portrait 分辨率 | `VideoAspect.portrait.to_resolution()` | `(1080, 1920)` |
| square 分辨率 | `VideoAspect.square.to_resolution()` | `(1080, 1080)` |
| 默认参数 | `VideoRewriteParams()` | `video_count=1`, `subtitle_enabled=True` |
| 无效枚举 | `VideoRewriteParams(video_aspect="invalid")` | `ValidationError` |

### test_plugin_registry.py（6 个用例）

`PluginRegistry._plugins` 是类变量，stub 类定义时通过 `__init_subclass__` 立即写入。为避免测试间状态泄漏，`conftest.py` 提供 `isolated_registry` fixture（autouse=False），在每个测试前深拷贝 `PluginRegistry._plugins`，测后恢复原值。所有 `test_plugin_registry.py` 用例显式使用此 fixture。

| 用例 | 目标 | 期望 |
|---|---|---|
| 子类自动注册 | 定义继承 `BaseDownloader` 的类 | `PluginRegistry.get(DOWNLOADER, name)` 返回该类 |
| `get()` 精确查找 | 注册两个同类型插件 | 按 name 返回正确的类 |
| `get_default()` 有名称 | `default_name` 匹配已注册插件 | 返回对应类 |
| `get_default()` 无名称 | `default_name=""` | 返回第一个注册的类 |
| `list_plugins()` | 注册多个插件 | 返回所有 name 列表 |
| 查找不存在的插件 | `get(type, "nonexistent")` | 返回 `None` |

### test_state.py（7 个用例）

每个测试用独立的 `MemoryState()` 实例，不共享状态。

| 用例 | 操作 | 期望 |
|---|---|---|
| 创建任务 | `update_task("t1", state=4, progress=10)` | `get_task("t1")["progress"] == 10` |
| 覆盖任务 | 两次 `update_task` 同一 ID | 第二次覆盖，progress 更新 |
| progress 上限 | `update_task(..., progress=150)` | `get_task(...)["progress"] == 100` |
| 不存在的任务 | `get_task("missing")` | 返回 `None` |
| 删除存在的任务 | `delete_task("t1")` | `get_task("t1") is None` |
| 删除不存在的任务 | `delete_task("missing")` | 不抛异常（幂等） |
| 分页 | 创建 5 个任务，`get_all_tasks(2, 2)` | 返回第 3-4 条，total=5 |

---

## API 集成测试规格（test_api.py，14 个用例）

所有用例通过 `client` fixture 发起请求，`task_manager.add_task` 被 mock 为 no-op。

### 任务 CRUD

| 用例 | 请求 | mock/前置 | 期望 |
|---|---|---|---|
| 提交任务成功 | `POST /api/v1/rewrite` + 合法 body | `add_task` no-op | 200，`data.task_id` 为 UUID |
| 队列满 | `POST /api/v1/rewrite` | `add_task` 抛 `TaskQueueFullError` | 429 |
| 分页查询所有任务 | `GET /api/v1/tasks?page=1&page_size=10` | state 中预置 2 个任务 | 200，`total=2` |
| 查询存在的任务 | `GET /api/v1/tasks/{id}` | state 中有该任务 | 200，含 `state`/`progress` |
| 查询不存在的任务 | `GET /api/v1/tasks/nonexistent` | — | 404 |
| 删除存在的任务 | `DELETE /api/v1/tasks/{id}` | state 中有该任务 | 200 |
| 删除不存在的任务 | `DELETE /api/v1/tasks/nonexistent` | — | 404 |

### 背景音乐

| 用例 | 请求 | 前置 | 期望 |
|---|---|---|---|
| 获取音乐列表 | `GET /api/v1/musics` | songs 目录为空或含 mp3 | 200，`data.files` 为列表 |

### 视频流 / 下载（路径安全）

使用 `tmp_task_dir` fixture 创建真实临时文件。

| 用例 | 请求 | 前置 | 期望 |
|---|---|---|---|
| 流式播放正常 | `GET /api/v1/stream/{task_id}/final-1.mp4` | 文件存在 | 206，`Content-Range` header |
| 流式播放路径穿越 | `GET /api/v1/stream/../../etc/passwd` | — | 403 |
| 流式播放文件不存在 | `GET /api/v1/stream/{task_id}/missing.mp4` | — | 404 |
| 下载正常 | `GET /api/v1/download/{task_id}/final-1.mp4` | 文件存在 | 200，`Content-Disposition` 含文件名 |
| 下载路径穿越 | `GET /api/v1/download/../../etc/passwd` | — | 403 |
| 下载文件不存在 | `GET /api/v1/download/{task_id}/missing.mp4` | — | 404 |

---

## 不在此 spec 范围内

- Redis 后端（`RedisState`、`RedisTaskManager`）— 需要真实 Redis，留给后续集成环境
- 插件实现（`YtDlpDownloader`、`WhisperTranscriber` 等）— 依赖外部服务，留给 E2E
- WebUI（Streamlit）— 独立前端，不适合 pytest 测试
