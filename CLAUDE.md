# VideoPrinterTurbo

视频改写 AI 项目：下载视频 → 转录原文 → LLM 改写 → TTS 配音 → 搜索素材 → 合成新视频 → 发布。

---

## 协作分工规则

**Claude 只负责 `front/` 目录的开发。**

- `front/` — Claude 可读、可写，完全负责
- `server/` — Claude 只可读，**不能修改任何文件**
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
# 启动后端（用户负责）
cd server && uvicorn app:app --host 0.0.0.0 --port 8080

# 启动前端（Claude 负责）
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

后端运行在 `http://localhost:8080`，前端通过 Vite 代理（`/api/*` → `http://localhost:8080/*`，去除 `/api` 前缀）访问。

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/` | 查询所有未删除任务（有真实数据） |
| `GET` | `/tasks/` | 查询任务列表（stub，返回 `{"tasks": []}` ） |
| `POST` | `/tasks/add` | 新建任务（stub，返回 `{"message": "任务添加成功"}` ） |
| `GET` | `/llm_config/` | LLM 配置（stub） |
| `GET` | `/asr_tts_config/` | ASR/TTS 配置（stub） |
| `GET` | `/material_config/` | 素材配置（stub） |
| `GET` | `/publish_config/` | 发布配置（stub） |

**数据库表（`vpt_tasks`）：**

```
id, task_url, create_time, is_deleted, status, task_id, error_code, error_desc
```

状态码：`0` 待处理 / `1` 进行中 / `2` 完成 / `-1` 失败

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
        └── TaskList.vue    # 任务列表（表格 + 分页 + FAB）
```

---

## 路由结构

所有页面挂载在 `AppLayout` 下，`meta.breadcrumb` 存 **i18n 键**，`AppLayout` 调用 `t(key)` 翻译后传给 `AppTopbar`。

**路由命名规范：路由 `path` 只允许使用字母和下划线（`snake_case`），禁止使用短横线（`-`）。**

| 路径 | 组件 | 面包屑键 |
|---|---|---|
| `/` | → redirect | → `/add_task` |
| `/add_task` | `AddTask.vue` | `['breadcrumb.addTask', 'breadcrumb.addTaskNew']` |
| `/tasks` | `TaskList.vue` | `['breadcrumb.appName', 'breadcrumb.taskList']` |
| `/settings/asr` | `PlaceholderPage` | `['breadcrumb.appName', 'breadcrumb.settings', 'breadcrumb.asr']` |
| `/settings/llm` | `PlaceholderPage` | `['breadcrumb.appName', 'breadcrumb.settings', 'breadcrumb.llm']` |
| `/settings/material` | `PlaceholderPage` | `['breadcrumb.appName', 'breadcrumb.settings', 'breadcrumb.material']` |
| `/settings/publish_config` | `PlaceholderPage` | `['breadcrumb.appName', 'breadcrumb.settings', 'breadcrumb.publishConfig']` |
| `/settings/tts_config` | `PlaceholderPage` | `['breadcrumb.appName', 'breadcrumb.settings', 'breadcrumb.ttsConfig']` |
| `/settings/proxy` | `PlaceholderPage` | `['breadcrumb.appName', 'breadcrumb.settings', 'breadcrumb.proxy']` |

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
| 选择音频转换方式 | `el-select` | 从字幕提取 / 从ASR转换 |

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
| TTS 服务 | `el-select`（全宽） | Edge TTS / Azure TTS V1 / Azure TTS V2 / SiliconFlow TTS / Google Gemini TTS / Xiaomi MiMo TTS |
| 声音角色 | `el-select` + 测试按钮 | zh-CN-XiaoXiaoNeural / zh-CN-YunXiNeural / zh-CN-XiaoYiNeural |
| 语音音量 | `el-slider` | 1.0–2.0，step 0.1；标签实时显示当前值 |
| 速度 | `el-slider` | 1.0–2.0，step 0.1；标签实时显示当前值 |

音量和速度滑块并排（两列布局）。

使用说明："输出到语音"将把处理好的文字通过 TTS 方式转换为语音，并合并到新的视频中。

---

#### ⑤ 输出到字幕（默认关闭）

| 字段 | 类型 | 选项 / 范围 |
|---|---|---|
| 字体 | `el-select` | 思源黑体 Bold / 思源黑体 Regular / 微软雅黑 Bold / 微软雅黑 Regular / Charm Bold / Charm Regular |
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
| 选择 BGM 库 | `el-select`（全宽） | 推荐轻快背景乐 / 推荐舒缓背景乐 / 随机背景音乐 / 无背景音乐 |
| 上传本地音频 | `el-upload` drag 区域（始终显示） | accept="audio/*"，auto-upload=false |
| 背景音乐音量 | `el-slider`（左右各一个扬声器图标 🔉 🔊） | 0.0–1.0，step 0.05，默认 0.5 |

上传区域与音量控制并排（两列布局）。

使用说明：选择相关的背景音乐后，将会将此背景音乐合并到新的视频中。

---

#### ⑦ 视频覆盖（默认关闭）

**第一行（3 列 select）：**

| 字段 | 选项 |
|---|---|
| 视频源 | Pexels / Pixabay / 本地文件（选"本地文件"后显示上传区域） |
| 拼接模式 | 顺序拼接 / 随机拼接（推荐） |
| 转场模式 | 无转场 / 随机转场 / 渐入 / 渐出 / 淡入淡出 / 滑动入 / 滑动出 |

**第二行（3 列）：**

| 字段 | 类型 | 选项 |
|---|---|---|
| 视频比例 | `el-select` | 9:16 (竖屏) / 16:9 (横屏) |
| 视频片段最大时长(秒) | `el-input type="number"` | 默认 10 |
| 同时生成视频数量 | `el-input type="number"` | 默认 1，最大 5 |

使用说明：点击"视频覆盖"复选框后，将从 Pexels 等网站获取短视频进行拼接。

---

#### ⑧ 发布（默认关闭）

| 字段 | 类型 | 说明 |
|---|---|---|
| 发布设置 (JSON 配置或描述) | `el-input type="textarea"` rows=5 readonly | 占位内容：`{ 'platform': 'douyin', 'auto_publish': true, ... }` |

使用说明：此功能暂未开放。

---

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
| 操作 (Operations) | 完成 → [播放] [编辑]；失败 → [重试] [编辑]；其他 → [编辑] |

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
- **编辑**：跳转 `/add_task?video_url=<encoded_url>`
- **新建任务 / FAB**：跳转 `/add_task`
- **轮询**：每 5 秒自动刷新，仅当列表中有 `status === 1`（进行中）的任务时触发

### 分页

- `store.pageSize = 10`
- `el-pagination` layout: `prev, pager, next, jumper`
- 翻页时调用 `store.fetchTasks()`

---

## API 封装（`src/services/api.ts`）

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

getTasks(page, pageSize)  // GET /api/tasks/
addTask(params)           // POST /api/tasks/add
streamUrl(path)           // returns /api/stream/{path}
```

响应格式为服务器直接返回的 JSON（无 `{status, data}` 包装层）。

---

## 前端测试

```shell
cd front && npx vitest run
```

测试文件：
- `src/services/api.test.ts` — getTasks 端点、addTask 端点、网络错误、streamUrl
- `src/stores/task.test.ts` — fetchTasks、loading flag、轮询生命周期

当前 7 个用例全部通过。
