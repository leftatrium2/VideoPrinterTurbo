# VideoPrinterTurbo

视频改写 AI 项目：下载视频 → 转录原文 → LLM 改写 → TTS 配音 → 搜索素材 → 合成新视频 → 发布。

---

## 协作分工规则

**Qoder 只负责 `front/` 目录的开发。**

- `front/` — Qoder 可读、可写，完全负责
- `server/` — Qoder 只可读，**不能修改任何文件**
- 其余根目录文件（`pyproject.toml`、`docker-compose.yml` 等）— 用户负责

---

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.11+, FastAPI + uvicorn, SQLAlchemy (async) + aiosqlite |
| 前端 | Vue 3 + Vite + TypeScript + Element Plus + Pinia + Vue Router + Vue I18n |
| 视频处理 | moviepy, yt-dlp, edge-tts, faster-whisper |
| 数据库 | SQLite（`server/db/VideoPrinterTurbo.db`） |

---

## 快速命令

```shell
# 启动后端
cd server && uvicorn app:app --host 0.0.0.0 --port 8080

# 启动前端
cd front && npm install && npm run dev   # http://localhost:5173

# 前端类型检查
cd front && npx vue-tsc --noEmit

# 前端测试
cd front && npx vitest run

# 前端构建
cd front && npm run build
```

---

## Server API 端点（只读参考）

后端运行在 `http://localhost:8080`，前端通过 Vite 代理（`/api/*` → `http://localhost:8080/*`，去除 `/api` 前缀）访问。**Qoder 不可修改后端代码，以下仅供开发前端时参考。**

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/` | 健康检查（返回 `{"message": "VideoPrinterTurbo API is running"}`） |
| `GET` | `/tasks/` | 添加任务页动态配置（`{code,msg,data}`；data 含 5 个字段，见下方说明） |
| `POST` | `/tasks/add` | 新建任务：生成 `task_id`（`utils/task_utils.gen_task_id`，`YYYYMMDDHHMMSS` + 6 位随机数，失败时回退 uuid4），将 `TaskItem` 全部业务字段写入 `vpt_tasks` 表；返回 `{code,msg,data}` 标准格式 |
| `GET` | `/tasks/list` | 查询任务列表，`page`（默认 1）/ `page_size`（默认 10，范围 10–50）；仅统计/查询 `is_deleted=0`；返回 `data: {total, data: VptTask[], page, page_size}`（每项已剔除 `id` 字段） |
| `GET` | `/tasks/get?task_id=<id>` | 查询单个任务详情（用于编辑模式回填）；`task_id` 为空返回 `TASK_ERR_TASK_ID_EMPTY`(1102)，未找到返回 `TASK_ERR_TASK_NOT_FOUND`(1103）；成功时返回 `VptTask` 记录（已剔除 `id`） |
| `GET` | `/tasks/check?url=<url>` | 检查视频链接是否可下载（`{code,msg,data}`；`code=0` 表示可用） |
| `GET` | `/tasks/del?task_id=<id>` | 删除任务（软删除，设置 `is_deleted=1`）；返回 `{code,msg,data}` 标准格式 |
| `GET` | `/llm_config/` | LLM 已保存配置（`{code,msg,data}`；data 含 5 个字段：`base_url`、`api_key`、`provider_name`、`llm_model_name`、`memo`，未配置时为空串） |
| `POST` | `/llm_config/update` | 保存 LLM 配置，body: `{base_url, api_key, provider_name, llm_model_name, memo}` |
| `GET` | `/tts_config/` | TTS 配置（stub，返回 `{"abc": "bcd"}`） |
| `GET` | `/tts_config/tts_list` | TTS 服务商列表（真实数据，返回 5 个 `{name, value}`：Azure TTS V1/V2、SiliconFlow、Google Gemini、Xiaomi MiMo） |
| `GET` | `/tts_config/tts_config_detail?engine=<n>` | 指定引擎的声音列表 + 已保存的配置（`voice[]`、`tts_area`、`tts_apikey`、`tts_voice`、`tts_server`）；`tts_voice`/`tts_server` 有值表示用户保存过，为空表示未配置 |
| `POST` | `/tts_config/update` | 保存 TTS 配置，body: `{tts_server, tts_voice, tts_area, tts_apikey}` |
| `GET` | `/asr_config/` | ASR 已保存配置（`{code,msg,data}`；data 含 6 个字段，未配置时为空串/0） |
| `POST` | `/asr_config/update` | 保存 ASR 配置，body: `{local_whisper_type, tencent_cloud_secret_id, tencent_cloud_secret_key, xfyun_appid, xfyun_secret_key, xfyun_web_api}` |
| `GET` | `/asr_config/local_whisper_list` | 本地 Whisper 模型列表（真实数据，返回 3 个 `{name, value}`：OpenAI Whisper、MLX Whisper、Faster Whisper） |
| `GET` | `/material_config/` | 素材配置（stub） |
| `GET` | `/publish_config/` | 发布配置（stub） |
| `GET` | `/proxy_config/` | 代理已保存配置（`{code,msg,data}`；data 含 4 个字段：`proxy_type`、`proxy_url`、`proxy_username`、`proxy_password`；未配置时 `proxy_type=0`、其余为空串） |
| `POST` | `/proxy_config/update` | 保存代理配置，body: `{proxy_type, proxy_url, proxy_username, proxy_password}` |

**`/tasks/config` 返回的 data 结构：**

| 字段 | 类型 | 说明 |
|---|---|---|
| `asr` | `{name, value: number}[]` | 可用的 ASR 方式；value 常量：1=字幕提取、2=本地Whisper、3=腾讯云ASR、4=科大讯飞ASR；始终包含字幕提取，其余按已配置凭证动态出现 |
| `tts` | `{name, value: string, voices: TtsVoiceItem[]}[]` | 可用的 TTS 服务商；value 为字符串常量（`TTS_LIST_AZURE_TTS_V1` 等）；voices 为该服务商声音列表 `{DisplayName, Value}[]` |
| `subtitle` | `{name, value: string}[]` | 字幕字体列表，value 为字体文件名（如 `"Charm-Bold.ttf"`） |
| `bgm` | `{name, value: string}[]` | BGM 库选项；当前返回 `random`（随机背景音乐）和 `custom`（自定义背景音乐） |
| `material` | 对象，含 4 个子数组（见下方） | 视频覆盖相关配置，不再是平铺数组 |
| `material.source` | `{name, value: string}[]` | 视频源；始终含 `local`（本地文件），Pexels / Pixabay 按已配置 API Key 动态出现 |
| `material.splicing` | `{name, value: number}[]` | 拼接模式；`1`=随机拼接（推荐）、`2`=顺序拼接 |
| `material.transition` | `{name, value: number}[]` | 转场模式；`1`=无转场、`2`=随机转场、`3`=渐入、`4`=渐出、`5`=淡入淡出、`6`=滑动入、`7`=滑动出 |
| `material.ratio` | `{name, value: number}[]` | 视频比例；`1`=9:16（竖屏）、`2`=16:9（横屏） |

**数据库表（`vpt_tasks`）：**

```
id, task_url, create_time, is_deleted, status, task_id, error_code, error_desc,
is_rewrite_to_tts, is_llm, is_publish, is_from_asr_or_subtitle, llm_prompt,
is_rewrite_to_subtitle, is_bgm, is_video_material,
tts_speed, subtitle_size, uploaded_bgm, bgm_volume,
video_material_type, uploaded_video_material, video_material_splicing_mode,
video_material_transition_mode, video_material_Video_ratio,
video_material_max_duration, video_material_generate_count,
subtitle_font, subtitle_font_color, subtitle_border_color,
audio_rewrite_type, tts_server, tts_voice, tts_volume, subtitle_position
```

`task_id` 为 `Text` 类型（非自增数字），由 `gen_task_id()` 生成，`/tasks/get` 用其查询任务。

状态码：`0` 待处理 / `1` 进行中 / `2` 完成 / `-1` 失败

---

## 后端目录结构

```
server/
├── app.py                  # FastAPI 入口，lifespan 管理（数据库初始化、配置同步、任务管理器启停）
├── config/
│   └── config.py           # 应用配置（YAML 加载）
├── middleware/
│   ├── cors_middleware.py  # CORS 中间件
│   └── exception_middleware.py  # 异常中间件
├── models/
│   ├── model.py            # SQLAlchemy ORM 模型
│   └── schemas.py          # Pydantic schemas
├── pipeline/               # 核心处理流水线
│   ├── downloader/         # 视频下载（yt-dlp）
│   ├── transcriber/        # 语音转文字（whisper 系列）
│   ├── llm/                # LLM 改写（OpenAI 兼容）
│   ├── material/           # 素材获取（Pexels/Pixabay/本地）
│   └── publisher/          # 发布模块
├── routers/                # API 路由
│   ├── index.py            # 健康检查
│   ├── tasks.py            # 任务 CRUD
│   ├── llm_config.py       # LLM 配置
│   ├── asr_config.py       # ASR 配置
│   ├── tts_config.py       # TTS 配置
│   ├── proxy_config.py     # 代理配置
│   ├── material_config.py  # 素材配置
│   └── publish_config.py   # 发布配置
├── service/
│   ├── task_manager.py     # 任务调度管理（APScheduler）
│   ├── task_const.py       # 任务常量
│   └── apscheduler_listener.py  # 调度器监听
├── utils/                  # 工具函数
├── resources/              # 字体 & 背景音乐资源
└── db/
    └── VideoPrinterTurbo.db  # SQLite 数据库文件
```

---

## 前端目录结构

```
front/
├── index.html
├── vite.config.ts          # 代理: /api/* → localhost:8080/*（rewrite 去除 /api 前缀）
├── package.json            # Vue 3, Element Plus, Pinia, Vue Router, Vitest
└── src/
    ├── main.ts             # 挂载 App，注册 EP icons / Pinia / Router / I18n
    ├── App.vue             # 根组件（仅 <RouterView />）
    ├── styles/
    │   └── variables.css   # 全局 CSS 变量（颜色、间距、阴影）
    ├── i18n/
    │   ├── index.ts        # createI18n + detectLocale + setLocale
    │   ├── zh.ts           # 中文翻译
    │   └── en.ts           # 英文翻译
    ├── router/
    │   └── index.ts        # 路由表（meta.breadcrumb 存 i18n 键）
    ├── services/
    │   ├── api.ts          # axios 封装 + Task 接口 + API 函数
    │   └── api.test.ts     # Vitest 单元测试
    ├── stores/
    │   ├── task.ts         # Pinia store：任务列表 + 5s 轮询
    │   └── task.test.ts    # Vitest 单元测试
    ├── components/
    │   ├── AppLayout.vue       # 布局壳（侧边栏 + 顶栏 + <RouterView>），翻译面包屑键
    │   ├── AppSidebar.vue      # 固定侧边栏（240px），文本通过 t() 获取
    │   ├── AppTopbar.vue       # 固定顶栏（面包屑 + 语言选择器 + 铃铛）
    │   └── PlaceholderPage.vue # "功能建设中"占位页
    └── views/
        ├── AddTask.vue     # 添加任务（8 个功能区块 + 开始任务按钮）
        ├── AsrConfig.vue   # ASR 配置（3 tab：Whisper/腾讯云/科大讯飞）
        ├── LlmConfig.vue   # LLM 配置（供应商名称/备注/API Key/API 请求地址 表单 + 使用说明弹框）
        ├── ProxyConfig.vue # 代理配置（类型/地址/用户名/密码 表单 + 卡片内 ⓘ 帮助图标）
        ├── TaskList.vue    # 任务列表（表格 + 分页 + FAB）
        └── TtsConfig.vue   # TTS 配置（服务商/声音/区域/Key 表单 + 使用说明弹框）
```

---

## 路由结构

所有页面挂载在 `AppLayout` 下，`meta.breadcrumb` 存 **i18n 键**，`AppLayout` 调用 `t(key)` 翻译后传给 `AppTopbar`。

**路由命名规范：路由 `path` 只允许使用字母和下划线（`snake_case`），禁止使用短横线（`-`）。**

| 路径 | 组件 | 面包屑键 |
|---|---|---|
| `/` | → redirect | → `/add_task` |
| `/add_task` | `AddTask.vue` | `['breadcrumb.addTask', 'breadcrumb.addTaskNew']` |
| `/get_task` | `AddTask.vue` | `['breadcrumb.addTask', 'breadcrumb.editTask']` |
| `/tasks` | `TaskList.vue` | `['breadcrumb.appName', 'breadcrumb.taskList']` |
| `/settings/asr` | `AsrConfig.vue` | `['breadcrumb.appName', 'breadcrumb.settings', 'breadcrumb.asr']` |
| `/settings/llm` | `LlmConfig.vue` | `['breadcrumb.appName', 'breadcrumb.settings', 'breadcrumb.llm']` |
| `/settings/material` | `PlaceholderPage` | `['breadcrumb.appName', 'breadcrumb.settings', 'breadcrumb.material']` |
| `/settings/publish_config` | `PlaceholderPage` | `['breadcrumb.appName', 'breadcrumb.settings', 'breadcrumb.publishConfig']` |
| `/settings/tts_config` | `TtsConfig.vue` | `['breadcrumb.appName', 'breadcrumb.settings', 'breadcrumb.ttsConfig']` |
| `/settings/proxy` | `ProxyConfig.vue` | `['breadcrumb.appName', 'breadcrumb.settings', 'breadcrumb.proxy']` |

---

## 国际化（i18n）

- 依赖：`vue-i18n@9`（composition API 模式，`legacy: false`）
- 支持语言：**中文（zh）** 和 **英文（en）**
- 语言选择器：顶栏右上角 `el-select` 下拉框

**Locale 检测逻辑（`src/i18n/index.ts`）：**
1. 读取 `localStorage.getItem('vpt_lang')`，有值则直接使用
2. 否则读取 `navigator.language`，以 `zh` 开头 → 中文，否则 → 英文

**切换语言：** 调用 `setLocale('zh' | 'en')`，同步写入 `localStorage`。

**翻译文件结构（`src/i18n/zh.ts` / `en.ts`）：**

```
lang.*         — 语言选项显示名称
sidebar.*      — 侧边栏导航文本
breadcrumb.*   — 路由面包屑键（路由 meta 存键，AppLayout 翻译）
addTask.*      — 添加任务页所有文本（区块标题、字段、选项、帮助文本、消息）
taskList.*     — 任务列表页所有文本
asrConfig.*    — ASR 配置页所有文本（tab 名、字段、消息）
llmConfig.*    — LLM 配置页所有文本（字段、使用说明、消息）
proxyConfig.*  — 代理配置页所有文本（字段、帮助图标弹框内容、消息）
ttsConfig.*    — TTS 配置页所有文本（字段、使用说明、消息）
placeholder.*  — 占位页文本
```

**扩展新语言：** 在 `src/i18n/` 新建 `<locale>.ts`，在 `index.ts` 的 `messages` 中注册，并在 `AppTopbar.vue` 的 `el-option` 中添加选项。

---

## 设计系统（`systematic_precision`）

```
页面背景:   #F0F2F5   --color-bg-page
卡片背景:   #FFFFFF   --color-bg-card
主色:       #409EFF   --color-primary
主色深:     #0060a9   --color-primary-dark
文字主:     #303133   --color-text-primary
文字常规:   #606266   --color-text-regular
文字次要:   #909399   --color-text-secondary
边框:       #DCDFE6   --color-border
卡片阴影:   0 2px 12px 0 rgba(0,0,0,0.1)   --shadow-card
侧边栏宽:  240px      --sidebar-width
顶栏高:     64px      --topbar-height
```

字体：Inter（正文 14px/400，标签 14px/500，标题 16–28px/600）

卡片圆角：8px；按钮/输入框圆角：4px

### 「使用说明」样式规范（全局统一）

**所有页面的「使用说明」链接必须使用统一样式，禁止各页面自定义颜色或字号。**

```css
.help-link {
  display: inline-flex;   /* 或 flex，视容器而定 */
  align-items: center;
  gap: 3px;
  font-size: 13px;
  color: var(--color-text-secondary);   /* 默认灰色 */
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
  transition: color 0.2s;
}
.help-link:hover { color: var(--color-primary); }  /* hover 变蓝 */
```

目前使用「使用说明」的页面：`TtsConfig.vue`、`LlmConfig.vue`、`AddTask.vue`（各区块内）。新增页面如需「使用说明」，直接复用此样式类，保持一致。

---

## 侧边栏导航

```
[Backend Admin]
[Management Suite]

+ 添加任务  →  /add_task
≡ 任务列表  →  /tasks

系统设置
🎙 ASR 配置    →  /settings/asr
✨ LLM 配置    →  /settings/llm
🖼 素材配置    →  /settings/material
▷  发布配置    →  /settings/publish_config
🎧 TTS 配置    →  /settings/tts_config
🔗 代理配置    →  /settings/proxy
```

激活样式：primary 蓝色文字 + 左侧 2px 蓝色竖条 + 浅蓝底色。

---

## 添加任务页（`AddTask.vue`）

页面由 8 个卡片区块纵向排列，底部为"开始任务"按钮。

每个区块结构：
```
┌─────────────────────────────────────────────┐
│ [图标] [复选框?] 区块名称         使用说明 🔘│  ← border-bottom
├─────────────────────────────────────────────┤
│  表单字段...                                 │
└─────────────────────────────────────────────┘
```

- "下载视频"无复选框（必填）；其余 7 个区块均有复选框作为"是否启用该步骤"开关
- 复选框状态存于 `enabled` reactive 对象，不影响内容显示（内容始终展示）
- "使用说明"点击触发 `el-popover`，内容见下方

### 各区块字段规格

#### ① 下载视频（无复选框）

| 字段 | 类型 | 说明 |
|---|---|---|
| 视频链接 | `el-input` + append 按钮 | 占位符：请输入抖音/Bilibili/Youtube视频链接 |
| 检查链接 | `el-button`（append slot） | 当前为 stub（功能开发中） |

使用说明弹框内容：填入视频播放页的URL地址，然后点击"检查链接"，如果弹出成功后，再继续往下进行，如果提示无法下载，可以在 GitHub 上面提 issue 给作者。

---

#### ② 音频转文字（默认关闭）

| 字段 | 类型 | 选项 |
|---|---|---|
| 选择音频转换方式 | `el-select` | 动态来自 `GET /tasks/config` 的 `data.asr[]`；`v-model` 绑定 `number` 类型 value |

使用说明：有两种方式将视频中的语音转换为文字，"从字幕提取"适合 YouTube 等带有自动字幕的视频网站；"从ASR转换"将直接提取视频中的语音并转为文字（除非是 YouTube 视频，否则建议使用 ASR 方式，避免出错）。

---

#### ③ LLM 改写（默认关闭）

| 字段 | 类型 | 说明 |
|---|---|---|
| LLM 提示词 (Prompt) | `el-input type="textarea"` rows=4 | 占位符：请输入改写要求... |

使用说明：选择 LLM 改写，并将提示词填入，会将当前提取到的文字经过 LLM 改写后重新输出。

---

#### ④ 输出到语音（默认关闭）

| 字段 | 类型 | 选项 / 范围 |
|---|---|---|
| TTS 服务 | `el-select`（全宽） | 动态来自 `GET /tasks/config` 的 `data.tts[]`；`v-model` 绑定 `value`（字符串常量如 `"TTS_LIST_AZURE_TTS_V1"`） |
| 声音角色 | `el-select` + 测试按钮 | 动态来自当前选中服务商的 `voices[]`；切换服务商时自动选第一项并重置试听 |
| 语音音量 | `el-slider` | 1.0–2.0，step 0.1；标签实时显示当前值 |
| 速度 | `el-slider` | 1.0–2.0，step 0.1；标签实时显示当前值 |

音量和速度滑块并排（两列布局）。

**测试按钮逻辑：**
- 未生成时显示「测试」；点击调 `GET /tts_config/tts_voice_preview?engine=<n>&voice=<v>`（engine 由 `TTS_ENGINE_MAP` 将字符串常量映射为数字 1–5），拿到文件路径后自动播放
- 已生成时按钮切换播放/暂停（「播放」/「暂停」）；换声音或换服务商时重置

使用说明："输出到语音"将把处理好的文字通过 TTS 方式转换为语音，并合并到新的视频中。

---

#### ⑤ 输出到字幕（默认关闭）

| 字段 | 类型 | 选项 / 范围 |
|---|---|---|
| 字体 | `el-select` | 动态来自 `GET /tasks/config` 的 `data.subtitle[]`；value 为字体文件名（如 `"Charm-Bold.ttf"`） |
| 位置 | `el-select` | 底部居中（推荐）/ 顶部居中 / 中间 / 自定义（70，离顶部70%位置） |
| 自定义位置 | `el-input`（条件显示） | 当位置选"自定义"时出现，默认值 "70" |
| 字幕颜色 | `<input type="color">` + hex 显示 | 默认 #ffffff（白色） |
| 描边颜色 | `<input type="color">` + hex 显示 | 默认 #000000（黑色） |
| 字幕大小 | `el-slider` | 30–100，默认 60 |

字幕颜色 / 描边颜色并排（两列布局）。

使用说明："输出到字幕"原视频中的语音不动，只是将处理好的文本转为字幕，添加到新的视频中。

---

#### ⑥ 背景音乐（默认关闭）

| 字段 | 类型 | 选项 / 说明 |
|---|---|---|
| 选择 BGM 库 | `el-select`（全宽） | 动态来自 `GET /tasks/config` 的 `data.bgm[]`；当前返回 `random`（随机背景音乐）/ `custom`（自定义背景音乐） |
| 上传本地音频 | `el-upload` drag 区域（**仅 `custom` 时显示**） | accept="audio/*"，auto-upload=false，`:show-file-list="false"`（文件列表自定义渲染）；选中文件后自动调用 `POST /tasks/upload_bgm`（multipart/form-data），返回 `data.saved_as`（服务器绝对路径）存入 `bgmUploadedPath`，成功弹 `ElMessage.success`，失败清空文件列表并弹错误提示；切换到其他选项时上传区隐藏但已上传文件状态保留，切回 `custom` 时文件仍显示；**不设 `:limit`**，每次选文件直接替换（设 limit=1 会导致第二次选文件触发 on-exceed 而非 on-change）|
| 已上传文件行 | 自定义文件行（`bgm-file-item`） | 显示文件名；「试听/暂停」按钮——点击后以 `ttsPreviewUrl(bgmUploadedPath)` 为 src 播放，再次点击暂停；状态由 `bgmIsPlaying` ref 驱动（不依赖 `audio.src` 判断，因 `audio.src=''` 会被浏览器解析为页面 URL）；「✕」按钮调 `handleBgmRemove` 清除文件与音频（清除用 `audio.removeAttribute('src')`，不用 `audio.src=''`）|
| 背景音乐音量 | `el-slider`（左右各一个扬声器图标 🔉 🔊） | 0.0–1.0，step 0.05，默认 0.5 |

上传区域与音量控制并排（两列布局）；选 `random` 时只显示音量控制。

使用说明：选择相关的背景音乐后，将会将此背景音乐合并到新的视频中。

---

#### ⑦ 视频覆盖（默认关闭）

**第一行（3 列 select）：**

| 字段 | 选项 |
|---|---|
| 视频源 | 动态来自 `GET /tasks/config` 的 `data.material.source[]`；始终含 `local`（本地文件），Pexels / Pixabay 按已配置 API Key 出现；选 `local` 时显示上传区域 `el-upload`（drag，accept="video/*"，multiple，`:show-file-list="false"`，自定义文件列表）；每次选文件后立即调用 `POST /tasks/upload_material`（multipart/form-data，field="files"，支持多文件），返回 `data[].saved_as` 累积存入 `materialUploadedPaths`；成功弹 `ElMessage.success`，失败从显示列表移除该文件并弹错误；自定义文件行显示文件名 + ✕ 移除按钮（复用 `.bgm-file-item` 样式），移除时同步清除 `materialUploadedPaths` 对应项；提交时以 `video_local_files: materialUploadedPaths` 传入 payload |
| 拼接模式 | 动态来自 `data.material.splicing[]`；value 为整数（`1`=随机拼接推荐、`2`=顺序拼接） |
| 转场模式 | 动态来自 `data.material.transition[]`；value 为整数 `1–7` |

**第二行（3 列）：**

| 字段 | 类型 | 选项 |
|---|---|---|
| 视频比例 | `el-select` | 动态来自 `data.material.ratio[]`；value 为整数（`1`=9:16竖屏、`2`=16:9横屏） |
| 视频片段最大时长(秒) | `el-input type="number"` | 默认 10 |
| 同时生成视频数量 | `el-input type="number"` | 默认 1，最大 5 |

使用说明：点击"视频覆盖"复选框后，将从 Pexels 等网站获取短视频进行拼接。

---

#### ⑧ 发布（默认关闭）

| 字段 | 类型 | 说明 |
|---|---|---|
| 发布设置 (JSON 配置或描述) | `el-input type="textarea"` rows=5 readonly | 占位内容：`{ 'platform': 'douyin', 'auto_publish': true, ... }` |

**复选框行为**：`:model-value="false"` 始终保持不选中；点击时触发 `ElMessage.warning`（「没有此功能，此复选框无法选中」），不写入 `enabled.publish`。

使用说明：此功能暂未开放。

---

### 编辑模式

`AddTask.vue` 同时挂载在 `/add_task` 和 `/get_task` 两个路由。当 URL 带 `task_id` 查询参数时（编辑模式），`onMounted` 会在加载完 `/tasks/` 配置后，额外调用 `GET /tasks/get?task_id=` 并用返回数据回填所有表单字段（含各区块开关、TTS/字幕/BGM/素材设置、已上传文件展示行）。加载失败时提示错误并跳转回 `/tasks`。提交逻辑不受影响，仍然调用 `POST /tasks/add`（会创建一条新任务，而非更新原任务）。

### 提交逻辑

点击"开始任务"：
1. 校验 `task_url` 非空
2. 按各 `enabled.*` 标志决定哪些字段写入请求体
3. 调用 `POST /api/tasks/add`
4. 成功后 `ElMessage.success` + 跳转 `/tasks`

---

## 任务列表页（`TaskList.vue`）

### 布局

```
[Task List 标题]                          [+ 新建任务 按钮]
┌──────────────────────────────────────────────────────┐
│ 地址(Address) │ 本地路径(Local Path) │ 状态 │ 操作  │
│ ...           │ ...                  │ ...  │ ...   │
├──────────────────────────────────────────────────────┤
│ Showing X to Y of Z entries     [< 1 2 3 ... 129 >] │
└──────────────────────────────────────────────────────┘
                                          [+ FAB 按钮]
```

### 表格列

| 列 | 内容 |
|---|---|
| 地址 (Address) | URL 超链接 + 状态图标；下方显示 "Added: YYYY-MM-DD HH:mm" |
| 本地路径 (Local Path) | 文件路径，无路径显示 "— No path assigned —"（斜体灰色） |
| 状态 (Status) | `el-tag`：完成(success绿) / 失败(danger红) / 进行中(warning橙) / 待处理(info灰)；失败时额外显示"查看日志"链接 |
| 操作 (Operations) | 完成 → [播放] [编辑] [删除]；失败 → [重试] [编辑] [删除]；其他 → [编辑] [删除] |

### 状态码映射

| status 值 | 标签 | Tag type |
|---|---|---|
| `2` | 完成 | success |
| `1` | 进行中 | warning |
| `0` | 待处理 | info |
| `-1` | 失败 | danger |

### 功能

- **播放**：弹出 `el-dialog`（800px），内含 `<video controls autoplay>` 指向 `/api/stream/{local_path}`
- **查看日志**：弹出 `el-dialog`（600px），显示 `task.error_desc`（`<pre>` 等宽字体）
- **重试**：重新调用 `POST /api/tasks/add`（携带原 `task_url`），刷新列表
- **编辑**：跳转 `/get_task?task_id=<encoded_task_id>`
- **删除**：弹出确认对话框，确认后调用 `GET /api/tasks/del?task_id=<id>`，成功后刷新列表
- **新建任务 / FAB**：跳转 `/add_task`
- **轮询**：每 5 秒自动刷新，仅当列表中有 `status === 1`（进行中）的任务时触发

### 分页

- `store.pageSize = 10`
- `el-pagination` layout: `prev, pager, next, jumper`
- 翻页时调用 `store.fetchTasks()`

---

## ASR 配置页（`AsrConfig.vue`）

仅替换主内容区（标题 + 单个白色卡片），侧边栏/顶栏不变。源自设计稿 `prototype/ASR配置页/`。

### 布局

```
ASR 配置
┌─────────────────────────────────────────────┐
│ Whisper（本地 ASR） │ 腾讯云 ASR │ 科大讯飞 ASR │
├─────────────────────────────────────────────┤
│  <各 tab 字段>                               │
├─────────────────────────────────────────────┤
│                        重填     提交          │
└─────────────────────────────────────────────┘
```

### 各 Tab 字段

| Tab | 字段 | 类型 |
|---|---|---|
| Whisper（本地 ASR） | 模型选择 | `el-select`，列表来自 `GET /asr_config/local_whisper_list`，回显字段 `local_whisper_type` |
| 腾讯云 ASR | secret_id | `el-input`，回显字段 `tencent_cloud_secret_id` |
| 腾讯云 ASR | secret_key | `el-input type="password" show-password`，回显字段 `tencent_cloud_secret_key` |
| 科大讯飞 ASR | APPID | `el-input`，回显字段 `xfyun_appid` |
| 科大讯飞 ASR | SecretKey | `el-input type="password" show-password`，回显字段 `xfyun_secret_key` |
| 科大讯飞 ASR | WebAPI | `el-input`，回显字段 `xfyun_web_api` |

**初始化逻辑（`onMounted`）：**  
`Promise.allSettled` 并发调用 `GET /asr_config/local_whisper_list` 和 `GET /asr_config/`，两者完成后：
- 若 `local_whisper_type` 非零则回显，否则默认选列表第一项
- 其余字段若非空则回显到对应 Tab 表单

- **重填**：重置当前激活 tab 的表单到空值（`model` 重置为 0）
- **提交**：三个 tab 的数据合并为一个对象，调用 `POST /asr_config/update`；按钮带 loading 状态，成功/失败均有 `ElMessage` 提示

---

## LLM 配置页（`LlmConfig.vue`）

仅替换主内容区（标题 + 单个白色卡片），侧边栏/顶栏不变。源自设计稿 `prototype/LLM配置/`。

### 布局

```
LLM 配置  ⓘ使用说明
┌─────────────────────────────────────────────┐
│  供应商名称  [___________________________]   │
│  备注        [___________________________]   │
│  API Key     [___________________________] 👁│
│  API 请求地址                                │
│  （填写兼容 OpenAI Response 格式的服务端点）  │
│              [___________________________]   │
├─────────────────────────────────────────────┤
│                              清空     提交    │
└─────────────────────────────────────────────┘
```

### 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| 供应商名称 | `el-input` | 占位符：请输入 |
| 备注 | `el-input` | 占位符：请输入 |
| API Key | `el-input type="password" show-password` | 占位符：请输入 |
| API 请求地址 | `el-input` | 标签下方有辅助文字：填写兼容 OpenAI Response 格式的服务端点地址 |
| 模型名称 | `el-input` | 占位符：请输入 |

表单布局：160px 标签列 + 弹性输入列（`grid-template-columns: 160px 1fr`）。

**初始化逻辑（`onMounted`）：** 调用 `GET /llm_config/`，将返回的 5 个字段回显到对应表单项，失败时 `ElMessage.error`。

**字段映射（接口 ↔ form）：**

| 接口字段 | form 属性 | 页面元素 |
|---|---|---|
| `provider_name` | `supplierName` | 供应商名称 |
| `memo` | `remarks` | 备注 |
| `api_key` | `apiKey` | API Key |
| `base_url` | `apiEndpoint` | API 请求地址 |
| `llm_model_name` | `modelName` | 模型名称 |

- **清空**：重置所有字段为空
- **提交**：调用 `POST /llm_config/update`，body 为上表字段的反向映射；按钮带 loading 状态，成功/失败均有 `ElMessage` 提示
- **使用说明**：标题右侧 `el-popover`，内容：本系统暂时只支持一个LLM配置，如果确定需要多个LLM配置，请从github上面的issue提交需求

---

## 代理配置页（`ProxyConfig.vue`）

仅替换主内容区（标题 + 单个白色卡片），侧边栏/顶栏不变。

### 布局

```
代理配置
┌─────────────────────────────────────────────┐
│ 代理服务设置                              [ⓘ] │  ← border-bottom，ⓘ = el-icon(InfoFilled)
├─────────────────────────────────────────────┤
│  代理服务类型   [HTTPS / SOCKS5 ▾]           │
│  地址           [_______________________]    │
│  用户名         [___________] 密码 [___] 👁  │
├─────────────────────────────────────────────┤
│                              清空     提交    │
└─────────────────────────────────────────────┘
```

**帮助图标**：卡片标题右侧的 `el-icon(InfoFilled)`，点击弹出 `el-popover`，说明代理用途（非 `.help-link` 样式）。

### 字段

| 字段 | 类型 | 选项 / 说明 |
|---|---|---|
| 代理服务类型 | `el-select` | HTTPS（`proxy_type=1`）/ SOCKS5（`proxy_type=2`） |
| 地址 | `el-input` | `proxy_url` |
| 用户名 | `el-input` | `proxy_username` |
| 密码 | `el-input type="password" show-password` | `proxy_password`，与用户名并排（两列布局） |

表单布局：160px 标签列 + 弹性输入列（`grid-template-columns: 160px 1fr`）。

**初始化逻辑（`onMounted`）：** 调用 `GET /proxy_config/`，回显 4 个字段；若 `proxy_type=0`（未配置）则默认选 HTTPS（`1`）。

- **清空**：重置所有字段为默认值（`proxyType=PROXY_TYPE_HTTPS`, 其余为空串）
- **提交**：调用 `POST /proxy_config/update`，body `{proxy_type, proxy_url, proxy_username, proxy_password}`；按钮带 loading 状态，成功/失败均有 `ElMessage` 提示

---

## TTS 配置页（`TtsConfig.vue`）

仅替换主内容区（标题 + 单个白色卡片），侧边栏/顶栏不变。源自设计稿 `prototype/TTS配置页/`。

### 布局

```
TTS 配置  ⓘ使用说明
┌─────────────────────────────────────────────┐
│ TTS服务器          │ 朗读声音      [试听语音合成]│
│ [选择服务商 ▾]      │ [选择声音 ▾]               │
│ 选择语音生成的主引擎。│                           │
│                                               │
│ 服务区域（条件显示） │ API Key（条件显示）        │
│ [_______________] │ [_______________] 👁       │
├─────────────────────────────────────────────┤
│                              放弃更改   保存   │
└─────────────────────────────────────────────┘
```

### 字段与行为

| 字段 | 来源 | 说明 |
|---|---|---|
| TTS 服务器 | `onMounted` 调用 `GET /tts_config/tts_list` | 真实接口返回 5 个服务商（无 Edge TTS），默认选中第一项并触发详情加载 |
| 朗读声音 | `GET /tts_config/tts_config_detail?engine=<n>` | 切换服务商时动态拉取；若返回 `tts_voice` 非空则恢复用户上次选择，否则默认选第一项 |
| 服务区域 / API Key | 同上接口，`tts_area` / `tts_apikey` | 切换服务商时始终覆盖写入（含空串）；Azure TTS V1（`value=1`）不显示任何凭证字段；Azure TTS V2（`value=2`）显示区域+Key；其余服务商只显示 Key |

- **API Key 输入框**：`el-input type="password" show-password`，原生眼睛图标切换明文。
- **保存**：调用 `POST /tts_config/update`，body `{tts_server, tts_voice, tts_area, tts_apikey}`，成功/失败均有 `ElMessage` 提示，按钮带 loading 状态。
- **放弃更改**：重置 form 并重新加载当前服务商的声音列表。
- **试听语音合成**：调用 `GET /tts_config/tts_voice_preview`，返回文件路径后由 `<audio>` 播放；再次点击切换播放/暂停。
- **使用说明**：标题右侧的 `使用说明` 链接，`el-popover` 弹出说明：配置 API Key 等信息后才能在"添加任务"页看到对应服务商，否则只显示免费的 Azure TTS V1。

---

## API 封装（`src/services/api.ts`）

**自定义 Header：** 所有请求通过 axios 拦截器自动添加 `X-I18n` Header，用于标识当前语言环境：
- 中文环境（`zh`）→ `X-I18n: cn`
- 英文环境（`en`）→ `X-I18n: en`

```typescript
// Task 接口（对应 vpt_tasks 表）
interface Task {
  id: number
  task_url: string
  create_time: string
  is_deleted: number
  status: number          // 0/1/2/-1
  task_id: number
  error_code: number
  error_desc: string
  local_path?: string
}

getTasks(page, pageSize)      // GET /api/tasks/list -> TaskListResult（{total, data, page, page_size}，仅返回 is_deleted=0 的任务）
addTask(params)               // POST /api/tasks/add -> {code, msg, data}
checkTaskUrl(url)             // GET /api/tasks/check?url=<url> -> {code, msg, data}
deleteTask(taskId)            // GET /api/tasks/del?task_id=<id> -> {code, msg, data}
getTaskConfig()               // GET /api/tasks/ -> TaskConfigData（asr/tts/subtitle/bgm/material 五个字段）
getTaskDetail(taskId)         // GET /api/tasks/get?task_id=<id> -> TaskDetail（VptTask 全部业务字段，布尔字段为 0/1，uploaded_bgm/uploaded_video_material 为 JSON 字符串）
streamUrl(path)               // returns /api/stream/{path}
getLlmConfig()                // GET /api/llm_config/ -> LlmConfigData（5 个字段）
updateLlmConfig(params)       // POST /api/llm_config/update，body: LlmConfigData（5 个字段全量提交）
getAsrConfig()                // GET /api/asr_config/ -> AsrConfigData（含各服务商已保存凭证 + local_whisper_type）
getLocalWhisperList()         // GET /api/asr_config/local_whisper_list -> {name, value}[]
updateAsrConfig(params)       // POST /api/asr_config/update，body: AsrConfigData（6 个字段全量提交）
getTtsList()                  // GET /api/tts_config/tts_list -> {name, value}[]
getTtsConfigDetail(engine)    // GET /api/tts_config/tts_config_detail?engine=<n>
                              //   -> {voice[], tts_area, tts_apikey, tts_voice, tts_server}
updateTtsConfig(params)       // POST /api/tts_config/update
                              //   body: {tts_server, tts_voice, tts_area, tts_apikey}
getTtsVoicePreview(engine, voice) // GET /api/tts_config/tts_voice_preview -> {output}
ttsPreviewUrl(filePath)       // returns /api/tts_config/preview?file_path=<path>
getProxyConfig()              // GET /api/proxy_config/ -> ProxyConfigData（4 个字段）
updateProxyConfig(params)     // POST /api/proxy_config/update，body: ProxyConfigData（4 个字段全量提交）
uploadBgm(file)               // POST /tasks/upload_bgm（multipart/form-data，field="file"）-> saved_as: string（服务器绝对路径，供 ttsPreviewUrl 使用）
uploadMaterial(files)         // POST /tasks/upload_material（multipart/form-data，field="files"，支持多文件）-> MaterialUploadItem[]（每项含 filename、saved_as、size、content_type）

// ProxyConfigData: { proxy_type: number, proxy_url: string, proxy_username: string, proxy_password: string }
// 常量: PROXY_TYPE_HTTPS=1, PROXY_TYPE_SOCKS5=2；proxy_type=0 表示未配置，回退到 HTTPS

// TaskConfigData: { asr: TaskConfigAsrItem[], tts: TaskConfigTtsItem[], subtitle: TaskConfigOptionItem[], bgm: TaskConfigOptionItem[], material: TaskConfigMaterialData }
// TaskConfigAsrItem: { name: string, value: number }
// TaskConfigTtsItem: { name: string, value: string, voices: TtsVoiceItem[] }
// TaskConfigOptionItem: { name: string, value: string }
// TaskConfigMaterialData: {
//   source: TaskConfigOptionItem[],          // 视频源，value 为字符串 "local"/"pexels"/"pixabay"
//   splicing: { name: string, value: number }[],   // 拼接模式，value 为整数 1=随机 2=顺序
//   transition: { name: string, value: number }[], // 转场模式，value 为整数 1–7
//   ratio: { name: string, value: number }[]       // 视频比例，value 为整数 1=9:16 2=16:9
// }
// AddTaskParams 中 video_material_splicing_mode / video_material_transition_mode / video_material_Video_ratio 均为 number（整数）
// TTS_ENGINE_MAP（前端常量）: 将 tts.value 字符串映射到数字 engine id，供 getTtsVoicePreview 使用
//   TTS_LIST_AZURE_TTS_V1→1, TTS_LIST_AZURE_TTS_V2→2, TTS_LIST_SILICON_FLOW_TTS→3, TTS_LIST_GOOGLE_GEMINI_TTS→4, TTS_LIST_XIAOMI_MIMO_TTS→5
```

`/tasks/` 等任务接口响应为服务器直接返回的 JSON（无包装层）；LLM / ASR / TTS / tasks/config 等配置接口响应格式为 `{code, msg, data}`，`code=0` 表示成功。

---

## 前端测试

```shell
cd front && npx vitest run
```

测试文件：
- `src/services/api.test.ts` — getTasks 端点、addTask 端点、网络错误、streamUrl
- `src/stores/task.test.ts` — fetchTasks、loading flag、轮询生命周期

当前 7 个用例全部通过。
