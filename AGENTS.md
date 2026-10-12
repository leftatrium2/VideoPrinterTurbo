# 仓库协作指南

## 项目与职责范围

VideoPrinterTurbo 是视频改写 AI 项目，处理流程为：下载视频、转录原文、
使用 LLM 改写、生成配音、搜索素材、合成新视频、发布。本仓库包含两个独立项目：

- `front/`：Vue 3 前端。可自由阅读和修改。
- `server/`：FastAPI 后端。**只读，禁止编辑、新建或删除该目录下的文件。**
  可以阅读以了解后端逻辑和 API 行为。
- 根目录配置文件（包括 `pyproject.toml`）由用户维护；除非用户明确要求，
  不要修改。

## 常用命令

```sh
# 后端（依赖与启动均以 server/ 为工作目录）
cd server
uv sync
uvicorn app:app --host 0.0.0.0 --port 8080

# 前端
cd front && npm install
cd front && npm run dev
cd front && npx vue-tsc --noEmit
cd front && npx vitest run
cd front && npm run build
```

后端测试位于 `server/tests/`。先在 `server/` 执行 `uv sync --extra dev`，再执行 `python -m pytest -q`。
后端依赖配置实际位于 `server/pyproject.toml`。

## 架构说明

后端入口为 `server/app.py`；其生命周期负责初始化数据库与配置，并启动
`task_manager`。配置从根目录的 `config.yaml` 加载。路由通常返回
`{code, msg, data}`，但部分接口会直接返回数据；使用前应确认具体接口。
`utils/const.py` 是任务及配置常量的唯一来源。

任务工作线程已启用，调用 `PipelineManager.process_now` 顺序执行任务；
视频合成、TTS、BGM 与素材相关代码已存在，具体可用性以实际验证为准。
发布功能继续保持禁用。

存储配置中的相对路径（如 `storage/downloads`）由 `utils/file_utils.py` 统一转换为本机绝对路径；
配置文件继续使用正斜杠。下载成功必须有非空视频文件，失败时保存原始下载错误并停止后续处理。
下载器结果中的 `status` 为可选字段：存在时 `0` 表示成功，其他值表示失败。

Windows 单 EXE 启动入口为 `desktop/launcher.py`，构建脚本为 `desktop/build.ps1`。
桌面版使用 faster-whisper CPU/int8，首次下载模型，默认 small。
`VPT_DATA_DIR` 指定持久数据根目录，`VPT_RESOURCE_DIR` 指定只读内置资源目录，
`VPT_MODEL_DIR` 可覆盖模型缓存目录。普通后端启动保持原目录行为。
模型管理 API 位于 `/asr_config/local_model_list`、`local_model_download`、`local_model_status`；
模型缓存校验完成后才允许离线加载。`local_whisper_model` 保存模型选择，SQLite 启动时补齐旧表字段。
本次用户已临时授权后端及根目录修改；完成该需求后仍遵循原有目录权限约定。

前端使用 Vue 3、Vite、TypeScript、Element Plus、Pinia、Vue Router 与 Vue I18n。
API 处理位于 `front/src/services/api.ts`，任务轮询位于
`front/src/stores/task.ts`，翻译文件位于 `front/src/i18n/`。

## 前端约定

- 路由路径只能使用字母和下划线（`snake_case`），禁止使用短横线。
- `meta.breadcrumb` 存储 i18n 键名，而不是已翻译的文本。
- 页面帮助链接必须复用 `.help-link`，禁止创建页面专用变体。
- 设计 token 位于 `front/src/styles/variables.css`（主色 `#409EFF`、侧边栏
  240px、顶部栏 64px、卡片圆角 8px、控件圆角 4px、字体 Inter）。
- API 返回格式并不统一。例如 `/tts_config/tts_list` 直接返回数组，绝大多数
  配置接口则返回 `{code, msg, data}`。

## 任务数据与已知行为

- `vpt_tasks.task_id` 是文本类型的任务主标识，不是数字型 `id`。状态：`0` 待处理、
  `1` 进行中、`2` 已完成、`-1` 失败。任务删除为软删除（`is_deleted=1`）。
- `AddTask.vue` 编辑任务用 `GET /tasks/get` 回填表单，提交调用 `POST /tasks/update`；
  新建任务调用 `POST /tasks/add`。
- 字幕提取、本地 Whisper、远程 Whisper 分别用 `asr_type=1/2/3` 获取语言列表；
  选项显示 `lang`，将字符串 `value` 原样提交到 `subtitle_lang`。
- 音频转文字中的人声分离选项默认“否”，通过布尔字段 `is_need_audio_separator`
  提交用户选择；编辑时兼容任务详情返回的 `0/1`。
- 任务 store 仅在存在 `status === 1` 的任务时每五秒轮询一次。
- 下载代理字段为 `is_use_proxy`（不要使用旧字段 `is_download_proxy`）。检查链接时将
  复选框状态以查询参数 `use_proxy=true|false` 传给 `/tasks/check`。
- 修改 `AddTask.vue` 的 BGM/素材界面前，BGM 上传不要设置 `:limit="1"`；清空音频时
  使用 `removeAttribute('src')`，不要使用 `audio.src = ''`。
- 视频覆盖比例字段为 `video_material_video_ratio`。
- 视频覆盖的 `video_material_keyword` 可留空；非空时最多 5 个以空白分隔的词，只允许
  英文字母、数字、连字符和撇号。该规则仅由前端校验。
- 添加任务页的“发布”区块因法律风险暂不展示，提交任务时固定传递 `is_publish=false`；
  不要重新启用或实现发布功能，除非用户明确要求。
- ASR 配置包含本地 Whisper 和“Whisper（远程 ASR）”。远程部署类型值为
  `TASK_CONFIG_REMOTE_VLLM_WHISPER=1`（默认，使用 `remote_vllm_url`、
  `remote_vllm_model`）或 `TASK_CONFIG_REMOTE_WHISPER_CPP=2`（使用
  `remote_whisper_cpp_url`）；任务表单配置会在远程类型非 0 时提供远程 Whisper。
- 已知 Azure TTS V1 从 `GET /tasks/` 返回展示名作为 `value`，会破坏前端引擎映射；
  涉及此区域时请核实该行为。其试听接口还要求 `vpt_tts_config` 中存在
  `tts_server=1` 的记录，即使 V1 不需要凭据。

## 常用 API 接口

基础地址：`http://localhost:8080`。Vite 开发代理会将 `/api/*` 映射到后端，
并去除 `/api` 前缀。

- `GET /tasks/`：任务表单配置；`POST /tasks/add`：创建任务；
  `POST /tasks/update`：更新任务。
- `GET /tasks/list`、`GET /tasks/get?task_id=`、`GET /tasks/check?url=&use_proxy=`、
  `GET /tasks/del?task_id=`：分别用于列表、查询、校验与软删除任务。
- `GET|POST /llm_config/` 与 `/llm_config/update`：LLM 配置。
- `GET /tts_config/tts_list`、`GET /tts_config/tts_config_detail?engine=`、
  `POST /tts_config/update`：TTS 配置。
- `GET|POST /asr_config/` 与 `/asr_config/update`：ASR 配置。
- `GET|POST /proxy_config/` 与 `/proxy_config/update`：代理配置。
- 素材配置提供 Pexels/Pixabay 的列表、新增和删除接口。

`GET /tts_config/` 与 `GET /publish_config/` 都是占位接口；不要以它们的返回格式
作为其他 API 的范例。

## 验证要求

前端改动交付前，请运行最相关的检查；通常为：

```sh
cd front && npx vue-tsc --noEmit
cd front && npx vitest run
cd front && npm run build
```

本文件是仓库的唯一权威协作说明。项目约定或架构事实变更时，应同步更新本文件。
