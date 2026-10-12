# 验证记录（2026-10-12）

本机为 Windows x64，构建 Python 3.11.9。

- 前端 `vue-tsc --noEmit` 通过。
- 前端 Vitest：7 个文件、46 项测试通过，包含模型下载与失败重试界面。
- 前端生产构建通过，有依赖注释与包体积提示。
- 后端 pytest：9 项通过，覆盖下载失败重试、并发复用、离线缓存、模型文件校验、
  large-v3 文件差异、CPU 加载、旧 SQLite 表重复迁移和接口输入校验。
- 从 Hugging Face 实际下载 tiny 模型并校验文件。
- 阻止模型下载接口后，成功从缓存加载并运行 CPU/int8 推理。
- Windows 合成英文音频被识别为 “Hello World. This is a local speech recognition test.”。
- 源码桌面服务健康检查、ASR 配置和模型列表、SPA 路由均正常返回。
- 合成本地视频提交到任务队列后，成功输出包含上述识别文本的 SRT。
- 源码重复启动复用现有实例。
- 最终单 EXE（516.5 MiB）在中文和空格数据路径下成功启动；启动 PATH 仅含 Windows 系统目录，
  不包含外部 Python 或 FFmpeg。
- 最终 EXE 内首次下载 tiny、校验成功；使用内置 FFmpeg 和 CPU Whisper 完成测试视频转录及输出。
- 最终 EXE 重复启动复用已有实例。
- 重启最终 EXE 并设置 `HF_HUB_OFFLINE=1` 后，第二个测试视频仍成功输出正确字幕和视频。
- 产物 SHA256：`5642c1895a85a790793682498ea57abc2e318495bd265d2ef4ec6c7d436cd929`。

测试数据位于仓库忽略的 `build/`，未修改原有用户数据库或配置。
浏览器权限拒绝了本地页面访问，未完成视觉检查。
尚未在无 Python/Node 的干净 Windows 机器上验收；其他云服务、GPU、人声分离、
全部模型和完整视频改写效果不在本次已验证范围内。
