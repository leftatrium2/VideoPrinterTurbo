# CLAUDE.md

本文件为 Claude Code（claude.ai/code）在本仓库中工作时提供指导。

## 项目概览

VideoPrinterTurbo（视频改写 AI 项目）：下载视频 → 转录原文 → LLM 改写 → TTS 配音 → 搜索素材 → 合成新视频 → 发布。后端在 `server/`（FastAPI），前端在 `front/`（Vue 3）。

两者之间没有统一的构建工具串联——`server/` 和 `front/` 视为共用一个 git 仓库的两个独立运行的项目。

## 协作范围

- `front/` — 可自由读写。
- `server/` — **只读，不能修改。** 可以自由阅读以了解后端逻辑/行为，但在任何情况下都不要编辑、新建或删除 `server/` 下的文件。
- 根目录配置文件（`pyproject.toml` 等）— 由用户负责。

## 常用命令

```shell
# 后端 — 安装依赖（uv 管理，见 uv.lock / pyproject.toml）
uv sync

# 后端 — 启动开发服务器（必须以 server/ 为工作目录；app.py 里是裸的 `import config.config` 等写法）
cd server && uvicorn app:app --host 0.0.0.0 --port 8080

# 前端 — 安装依赖 + 启动开发服务器（http://localhost:5173，代理 /api/* -> localhost:8080/*，去除 /api 前缀）
cd front && npm install && npm run dev

# 前端 — 类型检查
cd front && npx vue-tsc --noEmit

# 前端 — 测试（Vitest）
cd front && npx vitest run

# 前端 — 生产构建
cd front && npm run build
```

目前**没有后端测试**（`pyproject.toml` 设置了 `testpaths = ["tests"]`，`dev` extra 中也列了 `pytest`/`pytest-mock`/`httpx`，但仓库中并不存在 `tests/` 目录）。如需添加后端测试，先执行 `uv sync --extra dev`。

## 高层架构

### 后端（`server/`）

- `app.py` — FastAPI 入口。`lifespan()` 负责初始化数据库、调用 `gen_config()` 将配置同步进数据库、调用 `task_manager.start()`；路由也在此注册。
- `config/config.py` — 加载根目录的 `config.yaml`，写入 `_config.config`、`_config.downloader_config`、`_config.i18n_config` 等全局变量。
- `middleware/` — `cors_middleware.py`（已注册）、`i18n_middleware.py`（已注册——把 `X-I18n` 请求头读入 `ContextVar`，供后端代码本地化响应；`cn`/`en`）、`exception_middleware.py`（**存在但未注册**——`app.py` 中 `register_exception_middleware(app)` 被注释掉了）。
- `models/model.py` — SQLAlchemy ORM 模型，包括 `VptTask`（对应 `vpt_tasks` 表）以及 pexels/pixabay 素材配置表。
- `models/schemas.py` — Pydantic 请求/响应 schema。
- `pipeline/` — 核心处理流水线，每个阶段一个子包：
  - `downloader/` — 目前只剩 `yt_dlp/` 一种实现（其余下载器已被移除，详见 git 历史）。`pipeline.py` 中 `get_downloader()` 按关键词匹配已配置的域名选择下载器，其余一律回退到 yt-dlp 下载器。
  - `transcriber/` — 字幕提取、本地 Whisper、腾讯云 ASR、科大讯飞 ASR。
  - `llm/` — OpenAI 兼容的改写 provider。
  - `tts/` — Azure TTS v1/v2、SiliconFlow、Google Gemini、小米 MiMo 的 provider 类。
  - `material/` — Pexels / Pixabay 素材搜索器。
  - `publisher/` — 发布目标；尚未实现。
  - `pipeline.py` — 通过单例 `Pipeline` 类编排上述各步骤。**重要：只有步骤 1–3（下载、转录/字幕、LLM 改写）有真实逻辑。** `text_to_speech`、`text_to_subtitle`、`bgm`、`video_overlay`、`publish` 都是直接返回 `True` 的空实现（`text_to_speech` 里的 `tts_base` 恒为 `None`）。`tts/` 下的 provider 类已经存在，但尚未接入 `Pipeline`。
- `service/task_manager.py` — 设计上用于轮询 `vpt_tasks` 中排队的任务并推入流水线执行。**目前不起作用**：`start()` 里启动工作线程的代码被注释掉了；即便启动，其循环调用的 `pipeline.process(task.task_id)` 这个方法在 `Pipeline` 上根本不存在。不要假设排队的任务会被实际处理；`apscheduler_listener.py` 只是把 APScheduler 的日志级别调低，并没有真正驱动任务执行。
- `routers/` — 每个业务域一个文件（`tasks`、`llm_config`、`asr_config`、`tts_config`、`proxy_config`、`material_config`、`publish_config`、`index`）。大多数配置类路由遵循同一模式：`GET /<area>/` 以 `{code, msg, data}` 返回已保存配置，`POST /<area>/update` 负责持久化。
- `utils/const.py` — ASR 类型、TTS 引擎、代理类型、素材来源/拼接/转场/比例、错误码等所有魔法数字/字符串常量。硬编码状态/类型值之前先查这里。
- `db/VideoPrinterTurbo.db` — SQLite 文件，路径由 `config.yaml` 的 `database.url` 决定。

### 前端（`front/`）

Vue 3 + Vite + TypeScript + Element Plus + Pinia + Vue Router + Vue I18n。

- `src/router/index.ts` — 所有路由都是 `AppLayout` 的子路由，挂载在 `/` 下。**路由 `path` 只能使用字母和下划线（`snake_case`），禁止使用短横线。** `meta.breadcrumb` 存的是 i18n *键名*（不是翻译后的文本）；`AppLayout` 用 `t()` 翻译后再传给 `AppTopbar`。
- `src/services/api.ts` — axios 封装；拦截器根据当前语言环境给每个请求加 `X-I18n: cn|en` 头。大多数配置接口（`llm_config`、`asr_config`、`proxy_config`、`tasks/`）响应格式为 `{code, msg, data}`；但个别接口（如 `GET /tts_config/tts_list`）直接返回裸数组——不要假设所有接口的响应壳都统一，用之前先确认具体接口。
- `src/stores/task.ts` — 任务列表的 Pinia store；每 5 秒轮询一次，但仅当列表中存在 `status === 1`（进行中）的任务时才会轮询。
- `src/i18n/` — `zh.ts` / `en.ts` 翻译表，`index.ts` 做语言检测（`localStorage['vpt_lang']` → 否则按 `navigator.language` 前缀是否为 `zh` → 否则 `en`），并导出 `setLocale()`。
- `src/views/` — 每个设置/任务页面对应一个组件：`AddTask.vue`、`TaskList.vue`、`AsrConfig.vue`、`LlmConfig.vue`、`ProxyConfig.vue`、`TtsConfig.vue`、`MaterialConfig.vue`。`/settings/publish_config` 仍是 `PlaceholderPage.vue`（未实现）；`/settings/material` 现在渲染的是真正的 `MaterialConfig.vue`，不再是占位页。
- 设计 token 位于 `src/styles/variables.css`（`--color-primary #409EFF`、`--sidebar-width 240px`、`--topbar-height 64px`，卡片圆角 8px / 控件圆角 4px，字体 Inter）。各页面的"使用说明"链接必须复用统一的 `.help-link` 样式类（灰色、13px、hover 变蓝），禁止各页面自定义样式。

### 任务生命周期与数据模型

- 任务记录存于 `vpt_tasks`；`task_id` 是 `Text` 类型的类主键标识（**不是**数字型 `id`），由 `utils/task_utils.gen_task_id()` 生成（`YYYYMMDDHHMMSS` + 6 位随机数，失败时回退 `uuid4`）。`status`：`0` 待处理 / `1` 进行中 / `2` 完成 / `-1` 失败。删除为软删除（`is_deleted=1`）。
- **编辑任务实际上是新建一条任务记录**——`AddTask.vue` 挂载在 `/get_task?task_id=...` 时会用 `GET /tasks/get` 回填表单，但提交时始终调用 `POST /tasks/add`，并没有更新接口。
- `GET /tasks/` 返回用于填充"添加任务"表单下拉框的动态配置（asr/tts/subtitle/bgm/material 选项——material 是嵌套结构：`source`/`splicing`/`transition`/`ratio`）。已知 bug：针对 Azure TTS V1 这一项，后端（`routers/tasks.py`）把 `name`/`value` 写反了，导致 `value` 返回的是展示字符串 `"Azure TTS V1"`，而不是常量 `"TTS_LIST_AZURE_TTS_V1"`——这会破坏前端 `TTS_ENGINE_MAP`（`AddTask.vue`）对该服务商的查找。
- 改动 `AddTask.vue` 的 BGM/素材区块前，有几个隐藏细节要注意：BGM 的 `el-upload` 故意不设 `:limit="1"`（设置了会导致二次选择文件时触发 `on-exceed` 而非 `on-change`）；BGM 试听播放器用一个 `ref` 记录"是否正在播放"，而不是靠 `audio.src` 判断，因为 `audio.src = ''` 会被浏览器解析成页面自身的 URL（清空时用的是 `audio.removeAttribute('src')`）。

## 后端 API 参考

Base URL `http://localhost:8080`；前端开发服务器会把 `/api/*` 代理过去（并去除 `/api` 前缀）。

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/` | 健康检查 |
| `GET` | `/tasks/` | 添加任务页动态配置（`asr`、`tts`、`subtitle`、`bgm`、`material.{source,splicing,transition,ratio}`） |
| `POST` | `/tasks/add` | 新建任务；把 `TaskItem` 全部字段写入 `vpt_tasks` |
| `GET` | `/tasks/list` | 分页查询列表（`page`、`page_size` 10–50），只统计 `is_deleted=0` |
| `GET` | `/tasks/get?task_id=` | 查询单个任务详情（编辑模式回填用） |
| `GET` | `/tasks/check?url=` | 真实的下载器校验（并非 stub） |
| `GET` | `/tasks/del?task_id=` | 软删除 |
| `GET` | `/tasks/get_asr_lang` | 字幕语言选项，ASR 方式为"从字幕提取"时使用 |
| `GET` / `POST` | `/llm_config/`、`/llm_config/update` | 单份已保存的 LLM 配置（5 个字段） |
| `GET` | `/tts_config/` | Stub（`{"abc": "bcd"}`） |
| `GET` | `/tts_config/tts_list` | 真实数据；返回 5 个 TTS 服务商的裸数组（没有 `{code,msg,data}` 外壳） |
| `GET` | `/tts_config/tts_config_detail?engine=` | 指定引擎的声音列表 + 已保存配置 |
| `POST` | `/tts_config/update` | 保存 TTS 配置 |
| `GET` / `POST` | `/asr_config/`、`/asr_config/update` | ASR 配置（Whisper/腾讯云/科大讯飞） |
| `GET` | `/asr_config/local_whisper_list` | 3 个本地 Whisper 后端 |
| `GET` | `/material_config/pexels_list`、`/pixabay_list` | 分页查询已保存的 API Key 配置 |
| `POST` | `/material_config/add_pexels_config`、`/add_pixabay_config` | 新增一条 API Key 配置 |
| `GET` | `/material_config/del_pexels_config`、`/del_pixabay_config` | 按 id 删除一条配置 |
| `GET` | `/publish_config/` | Stub，返回 `{"get_publish_config": "get_publish_config"}`（注意：不是 `{code,msg,data}` 外壳） |
| `GET` / `POST` | `/proxy_config/`、`/proxy_config/update` | 代理配置（HTTPS/SOCKS5） |

### `vpt_tasks` 表字段（`server/models/model.py`）

```
id, task_url, create_time, is_deleted, status, task_id, error_code, error_desc,
is_rewrite_to_tts, is_llm, is_publish, is_from_asr_or_subtitle, llm_prompt,
is_rewrite_to_subtitle, is_bgm, is_video_material,
tts_speed, subtitle_size, uploaded_bgm, bgm_volume,
video_material_type, uploaded_video_material, video_material_splicing_mode,
video_material_transition_mode, video_material_Video_ratio,
video_material_max_duration, video_material_generate_count,
subtitle_font, subtitle_font_color, subtitle_border_color,
audio_rewrite_type, tts_server, tts_voice, tts_volume, subtitle_position,
subtitle_lang
```

## 前端测试

`front/src/services/api.test.ts`（9 个用例）和 `front/src/stores/task.test.ts`（3 个用例）。运行方式：`cd front && npx vitest run`。
