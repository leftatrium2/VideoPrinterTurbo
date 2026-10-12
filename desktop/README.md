# Windows 单 EXE

## 使用

双击 `dist/VideoPrinterTurbo.exe`。程序在本机启动服务并打开默认浏览器。
保留启动窗口；按 Ctrl+C 退出，正在执行的任务会先结束。
关闭浏览器页面不会关闭服务。

进入 ASR 配置，选择 faster-whisper 和模型（默认 small），点击“下载 / 重试”。
下载进度按完成文件数显示，大文件传输期间计数可能保持不变。
模型完成校验后显示“已就绪”。保存配置后，新任务使用该模型。
直接提交转录任务也会自动下载缺失模型；下载失败会使任务失败，修复网络后可重试下载。

模型来源为 Hugging Face 的 `Systran/faster-whisper-*`，首次下载需要可访问该服务。
可使用启动进程的 `HTTPS_PROXY` 环境变量配置下载代理；它独立于任务下载代理。
已下载模型无需联网即可进行本地转录；远程 LLM、素材搜索等功能仍需联网。
桌面版使用 CPU / int8，不要求 CUDA；不提供 MLX 或 OpenAI Whisper 引擎。
现有的人声分离功能保留，其模型和依赖独立于 Whisper。

持久数据默认位于 `%LOCALAPPDATA%\VideoPrinterTurbo`：

- `models/faster_whisper`：模型缓存，升级 EXE 不需重新下载。
- `db`：SQLite 数据库。
- `config.yaml`、`downloader.json`：用户配置。
- `logs`、`storage`、`output`：日志、素材和结果。

EXE 内只包含默认配置、程序依赖、前端、FFmpeg/ffprobe 和资源，不包含个人 API 密钥、
数据库或 Whisper 模型。单文件启动会解压依赖到临时目录，首次启动可能较慢。
本机默认端口 18080；已有同端口桌面实例时打开现有实例，端口被其他程序占用时使用空闲端口。

## 构建

需要 Windows、Python 3.11/3.12、Node.js，以及 FFmpeg/ffprobe。
先从 `server/` 执行 `uv sync --extra dev`，从 `front/` 执行 `npm ci`，然后在仓库根目录：

```powershell
./desktop/build.ps1 -FFmpegDirectory D:\ffmpeg\bin
```

默认使用 `server/.venv/Scripts/python.exe`，可通过 `-Python` 指定其他构建环境。
产物：`dist/VideoPrinterTurbo.exe`。构建脚本临时设置前端 API 地址为 `/api`。
FFmpeg 应包含目标 Windows 架构所需 DLL；优先使用可信的静态构建。
分发时需遵守所用 FFmpeg 构建、依赖和模型各自的许可证。

调试启动：

```powershell
server/.venv/Scripts/python.exe desktop/launcher.py --no-browser --port 18080
```

可用 `VPT_DATA_DIR` 指定独立数据目录，`VPT_MODEL_DIR` 指定模型缓存目录。
源码调试前先以 `VITE_API_BASE_URL=/api` 构建前端。

## 验证

```powershell
cd server
.venv/Scripts/python.exe -m pytest -q
cd ../front
npx vue-tsc --noEmit
npx vitest run
npm run build
```

发布前还应在未安装 Python/Node 的干净 Windows 机器上验证首次下载、重启离线转录、
中文路径和实际视频任务。构建机上的测试不能替代干净机器验收。

真实模型检查（会下载 tiny 模型到指定目录）：

```powershell
server/.venv/Scripts/python.exe desktop/smoke_model.py --cache build/model_smoke
```

可加 `--audio path/to/test.wav` 验证指定的本地音频；脚本随后阻止模型下载接口，
确认缓存可离线加载并执行 CPU 推理。
