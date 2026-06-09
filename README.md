# VideoPrinterTurbo 🎬

视频改写 AI 项目 — 将网站视频进行 AI 改写：下载、提取原文、LLM 改写、合成新视频并发布。

## 功能特性

- ✅ **下载源视频** — 使用 yt-dlp 从 YouTube / Bilibili 等网站下载
- ✅ **智能提取原文** — 优先提取字幕，无字幕则 ASR 语音识别
- ✅ **AI 改写文案** — 支持 OpenAI / DeepSeek / Gemini 等多种 LLM
- ✅ **TTS 配音** — edge-tts 多种语音可选
- ✅ **素材搜索** — Pexels / Pixabay 高清素材自动匹配
- ✅ **视频合成** — 新配音 + 新字幕 + 新画面 + BGM
- ✅ **一键发布** — 支持发布到 TikTok / Instagram
- ✅ **插件架构** — 每步可插拔，方便扩展
- ✅ **WebUI + API** — Streamlit 前端 + FastAPI 后端

## 快速开始

### 安装

```shell
git clone https://github.com/leftatrium2/VideoPrinterTurbo.git
cd VideoPrinterTurbo

# 推荐使用 uv
uv sync --frozen

# 或使用 pip
pip install -e .
```

### 配置

```shell
cp config.example.toml config.toml
```

编辑 `config.toml`，配置 API Key：

- `openai_api_key` — LLM 提供商（也支持 DeepSeek / Gemini）
- `pexels_api_keys` — 视频素材搜索
- `llm_provider` — `"openai"` / `"deepseek"` / `"gemini"`

### 启动

```shell
# API 服务
python main.py

# WebUI（新开终端）
streamlit run webui/Main.py --browser.gatherUsageStats=False
```

### Docker

```shell
docker-compose up
```

访问 http://localhost:8501 (WebUI) 或 http://localhost:8080/docs (API)

## 架构

详见 [AGENTS.md](./AGENTS.md)。

## License

MIT
