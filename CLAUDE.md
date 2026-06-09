# VideoPrinterTurbo

视频改写 AI 项目：下载视频 → 转录原文 → LLM 改写 → TTS 配音 → 搜索素材 → 合成新视频 → 发布。

- **Stack:** Python 3.11+, FastAPI + uvicorn, Streamlit, moviepy, yt-dlp, edge-tts, faster-whisper, openai
- **Entry point:** `main.py`（API server），`webui/Main.py`（Streamlit UI）
- **Remote:** `git@github.com:leftatrium2/VideoPrinterTurbo.git`

## 快速命令

```shell
# 依赖安装
uv sync --frozen
pip install -e ".[gemini]"   # 需要 Gemini 支持时

# 启动 API server
uv run python main.py        # http://localhost:8080

# 启动 WebUI（新终端）
uv run streamlit run webui/Main.py --browser.gatherUsageStats=False

# Docker 一键启动
docker-compose up            # api :8080, webui :8501

# 语法检查（无测试套件时用）
python -m py_compile <file>
find app webui -name "*.py" | xargs python -m py_compile
```

## 配置

首次运行需要复制配置文件并填写 API Key：

```shell
cp config.example.toml config.toml
```

关键配置项（`config.toml`）：
- `llm_provider` — `openai` / `deepseek` / `gemini`
- `material_provider` — `pexels` / `pixabay`（需对应 API Key）
- `transcriber_provider` — `whisper` / `subtitle_extractor`
- `subtitle_provider` — `edge` / `whisper`
- `enable_redis = true` — 切换到 Redis 队列和状态（默认内存）
- `[ui] language` — 固定默认语言（留空则自动检测）

## 项目结构

```
VideoPrinterTurbo/
├── main.py                       # uvicorn 入口
├── pyproject.toml                # 依赖管理
├── config.example.toml / config.toml
│
├── app/
│   ├── asgi.py                   # FastAPI 实例 + CORS + 异常处理 + 静态文件
│   ├── router.py                 # APIRouter 聚合
│   ├── config/config.py          # TOML → AppConfig/WhisperConfig/ProxyConfig
│   │
│   ├── controllers/
│   │   ├── base.py               # 公共依赖 (get_task_id, verify_token)
│   │   ├── manager/
│   │   │   ├── base_manager.py   # TaskManager 抽象（并发控制 + 队列）
│   │   │   ├── memory_manager.py # InMemoryTaskManager (queue.Queue)
│   │   │   └── redis_manager.py  # RedisTaskManager (Redis List)
│   │   └── v1/rewrite.py         # API 端点定义
│   │
│   ├── models/
│   │   ├── const.py              # 任务状态常量（-1/1/4）
│   │   ├── exception.py          # HttpException
│   │   └── schema.py             # Pydantic 模型（VideoRewriteParams, TranscriptSegment 等）
│   │
│   ├── plugins/                  # ⭐ 插件体系（6 类扩展点）
│   │   ├── base.py               # BasePlugin + PluginType + PluginRegistry
│   │   ├── downloader/           # BaseDownloader + YtDlpDownloader
│   │   ├── transcriber/          # BaseTranscriber + WhisperTranscriber + SubtitleExtractor
│   │   ├── llm/                  # BaseLLMProvider + OpenAIProvider + GeminiProvider
│   │   ├── material/             # BaseMaterialSearcher + PexelsSearcher + PixabaySearcher
│   │   └── publisher/            # BasePublisher + UploadPostPublisher
│   │
│   ├── services/
│   │   ├── task.py               # 管线编排器（7 步骤）
│   │   ├── video_rewrite.py      # moviepy + ffmpeg 合成
│   │   ├── voice.py              # edge-tts TTS
│   │   ├── subtitle.py           # Whisper 字幕生成
│   │   └── state.py              # 任务状态（MemoryState / RedisState）
│   │
│   └── utils/
│       ├── utils.py              # 路径/UUID/JSON/SRT 工具
│       └── file_security.py      # 白名单路径校验（防目录穿越）
│
├── webui/
│   ├── Main.py                   # Streamlit 前端
│   └── i18n/{zh,en}.json         # 国际化语言文件（60 keys）
│
├── resource/
│   ├── fonts/                    # 字幕字体
│   ├── songs/                    # 背景音乐
│   └── public/index.html         # 静态首页
│
├── storage/tasks/                # 任务输出目录（运行时产物）
├── downloads/                    # yt-dlp 下载临时目录（运行时产物）
├── Dockerfile                    # Python 3.11-slim + ffmpeg
└── docker-compose.yml            # api(:8080) + webui(:8501)
```

## API 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/api/v1/rewrite` | 提交视频改写任务 |
| `GET` | `/api/v1/tasks` | 分页查询所有任务 |
| `GET` | `/api/v1/tasks/{id}` | 查询单个任务状态和结果 |
| `DELETE` | `/api/v1/tasks/{id}` | 删除任务及产物 |
| `GET` | `/api/v1/stream/{path}` | 视频流播放（Range 支持）|
| `GET` | `/api/v1/download/{path}` | 视频文件下载 |
| `GET` | `/api/v1/musics` | 背景音乐列表 |

## 管线流程（`services/task.py:start()`）

7 个步骤顺序执行，每步更新进度，可通过 `stop_at` 参数跳过后续步骤：

```
POST /api/v1/rewrite  { video_url, rewrite_instruction, ... }
  │
  ├─ ① 下载（5~15）   yt-dlp → VideoPackage { video_path, audio_path, subtitle_path, metadata }
  ├─ ② 转录（20~30）  优先内嵌字幕（SRT/VTT/ASS），回退 faster-whisper ASR
  ├─ ③ LLM 改写（35~45）  原文 + 指令 → 新解说词 + search_terms
  ├─ ④ TTS（50~60）   edge-tts → 语音文件 + 时间轴字幕
  ├─ ⑤ 素材搜索（65~75）  Pexels / Pixabay → 本地视频路径列表
  ├─ ⑥ 视频合成（80~95）  moviepy + ffmpeg → final-{n}.mp4
  └─ ⑦ 发布（98，可选）  TikTok / Instagram → PublishResult
```

## 插件体系

6 类扩展点，每类一个抽象基类 + 自动注册：

| 类型 | 基类 | 核心方法 | 已实现 | 可扩展方向 |
|---|---|---|---|---|
| `downloader` | `BaseDownloader` | `download(url) → VideoPackage` | `YtDlpDownloader` | Bilibili、本地文件 |
| `transcriber` | `BaseTranscriber` | `transcribe(audio)` / `extract_subtitles(video)` | `WhisperTranscriber`, `SubtitleExtractor` | 阿里云 ASR、Azure 语音 |
| `llm` | `BaseLLMProvider` | `rewrite()` / `generate_script()` / `generate_terms()` / `translate()` | `OpenAIProvider`, `GeminiProvider` | 文心一言、Claude |
| `material` | `BaseMaterialSearcher` | `search()` / `download()` | `PexelsSearcher`, `PixabaySearcher` | 本地素材、腾讯云 |
| `publisher` | `BasePublisher` | `publish(video) → PublishResult` | `UploadPostPublisher` | 抖音、快手 |

**注册机制：** `BasePlugin.__init_subclass__` 自动调用 `PluginRegistry.register()`，新插件只需继承并设置 `type` / `name` 即可，无需手动注册。

### 新增插件示例

```python
class MyDownloader(BaseDownloader):
    type = PluginType.DOWNLOADER
    name = "my_downloader"

    def validate_config(self): ...
    def download(self, url: str) -> VideoPackage: ...
```

## 设计模式

- **Plugin Registry** — 自动注册 + 通过 `get_default(config_key)` 从配置获取默认实现
- **Strategy** — 每类插件对应一种接口，运行时按配置切换实现
- **Abstract Factory** — `controllers/manager/` 和 `services/state.py` 支持 Memory / Redis 双实现
- **Pipeline** — `services/task.py:start()` 为管线编排器，每步独立、可跳过
- **Template Method** — `TaskManager` 定义骨架，子类实现队列细节

## 开发约定

### 错误处理

- **API 层**：raise `HttpException`（继承 `HTTPException`）
- **插件层**：raise `RuntimeError`
- 不要在插件内部吞掉异常后返回 `None`

### 配置访问

```python
from app.config.config import config
value = config.app.get("key", default)
```

### 文件路径安全

所有涉及用户输入路径的操作必须通过白名单校验：

```python
from app.utils.file_security import resolve_path_within_directory
safe_path = resolve_path_within_directory(user_path, allowed_root)
```

### 状态与队列

- `services/state.py` 的全局 `state` 管理任务状态
- `controllers/manager/` 的 `task_manager` 管理并发队列
- Memory / Redis 切换由 `config.enable_redis` 控制，业务代码无需感知

### WebUI 国际化

所有 Streamlit 组件文本用 `tr()` 包裹：

```python
st.button(tr("Start Rewrite"))
```

语言文件位于 `webui/i18n/*.json`，扁平 key-value 结构，key 为英文标识符，找不到时原样返回 key（英文降级）。

**语言选择优先级（高→低）：**
1. URL 参数 `?lang=xx`（JS 写入）
2. `config.toml [ui] language`
3. 系统区域（`locale.getlocale()`）
4. 默认 `"zh"`

新增文本时同步更新 `zh.json` 和 `en.json`；新增语言只需在 `webui/i18n/` 下添加对应 JSON 文件。

## 依赖说明

- Python `>=3.11,<3.13`（`.python-version` 锁定）
- 使用 `uv` 管理依赖，通过 `pyproject.toml` 修改后运行 `uv sync`
- Gemini 为可选依赖组：`pip install -e ".[gemini]"`
- Whisper `large-v3` 首次运行自动下载（约 3GB）

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

## 注意事项

- `config.toml` 含 API Key，不要提交（已在 `.gitignore`）
- `storage/` 和 `downloads/` 为运行时产物，不要提交
- 修改 `app/plugins/` 下任何文件后需重启 API server（插件在启动时注册）
- 视频合成依赖系统级 `ffmpeg`，Docker 镜像已内置；本地开发需自行安装
- 素材搜索和 LLM 调用需要网络；国内用户建议在 `config.toml` 中配置 `[proxy]`
