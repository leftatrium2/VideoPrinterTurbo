# 对口型实现

当前提供自建服务、Sync Labs、HeyGen、fal.ai 四种实现，统一实现
`LipSyncBase.lip_sync(video_path, audio_path, output_path)`，已接入任务流水线。
进度通过可选回调及 INFO 日志显示，详见文末进度说明。

```python
import os
from pipeline.lip_sync.sync_labs import SyncLabs

service = SyncLabs(api_key=os.environ["SYNC_API_KEY"], model="lipsync-2")
result = service.lip_sync("speaker.mp4", "final_voice.m4a", "speaker_synced.mp4")
```

- 输入是本地文件，配音不含 BGM，音画共享同一时间起点。时长差超过 150ms 时在上传前拒绝；
  该容差仅用于编码取整，不是重新分配配音时间。
- 使用官方资产上传流程：申请签名地址、流式 PUT、注册资产，以 assetId 提交生成。
  单文件应用上限 5 GiB，账号套餐仍可能有更低限制；上传素材会保存在云端账号中。
- `sync_mode="silence"`，不启用循环或变速。下载后校验视频时长和完整解码，
  复制云端视频画面，并用传入配音重新封装音轨。
- 输出必须是新的 `.mp4` 文件。所有临时文件在成功或失败后清理；输入文件保持不变。
- 可配置 `proxy_url`、`request_timeout`、`upload_timeout`、`poll_interval`、`job_timeout`。
  代理通过参数显式配置，不读取环境代理。
- 生成失败或拒绝时报告任务 ID 和错误。超时不会取消云端任务，
  `last_generation_id` 可用于查找原任务。生成提交不自动重试，以免重复付费；
  连接在提交响应前断开时，可能无法获得任务 ID，应先在 Sync 控制台核查。
- API 密钥仅发往配置的 API 地址，不传给素材存储或下载地址；签名 URL 不写日志。
- 模拟服务测试只能验证 HTTP 契约、文件和音轨处理，不能证明实际口型质量。

官方文档：

- https://sync.so/docs/developer-guides/asset-uploads
- https://sync.so/docs/api-reference/api/generate-api/create
- https://sync.so/docs/api-reference/api/generate-api/get
- https://sync.so/docs/developer-guides/sync-mode

本地 HTTP 测试见 `server/tests/lip_sync_mock/README.md`。

## fal.ai LatentSync

`FalLatentSync` 实现同一个 `LipSyncBase.lip_sync()` 接口，调用固定模型
`fal-ai/latentsync`，已接入任务流水线。

```python
import os
from pipeline.lip_sync.fal_latentsync import FalLatentSync

service = FalLatentSync(api_key=os.environ["FAL_KEY"], guidance_scale=1, seed=123)
result = service.lip_sync("speaker.mp4", "final_voice.wav", "speaker_synced.mp4")
```

- 上传使用官方 Python 客户端同样支持的 REST storage initiation（`storage_type=gcs`）
  和流式 PUT；不需要安装 fal SDK，不使用全局环境密钥。上传后媒体 URL 可供云端访问。
- 以 `Authorization: Key …` 提交队列，处理 `IN_QUEUE`、`IN_PROGRESS`、`COMPLETED`。
  `COMPLETED` 中的 `error`/`error_type` 以及结果接口的 HTTP 错误都按失败处理。
- 构造函数支持 `proxy_url`、请求/上传/任务超时、轮询间隔；
  `queue_base_url`、`storage_base_url` 可指向本地模拟服务。
- 与 Sync Labs 一样，要求输入共享时间起点且时长差不超过 150ms。
  此外音频不得长于视频（1ms 测量容差），防止 LatentSync 触发循环/倒放；
  不通过截断音频或改变视频时长修正输入。AAC 容器时长超出时可提供已对齐的 WAV。
- 不配置 `loop_mode`，并在下载后验证视频时长和完整解码，再替换为传入配音音轨。
  输出须为新的 `.mp4`，失败清理临时文件。
- `last_request_id` 保留已提交的队列任务编号。超时不表示云端已取消；
  不自动重提付费任务，应先查询 fal 控制台中的原请求。
- API 密钥不发送到签名上传地址或下载地址；队列返回的查询地址须在配置的 API 来源内。

契约来源：

- https://fal.ai/models/fal-ai/latentsync/api
- https://fal.ai/docs/documentation/model-apis/inference/queue
- https://github.com/fal-ai/fal/blob/main/projects/fal_client/src/fal_client/client.py

本地模拟测试（不调用模型、不产生费用）：

```sh
postman simulation run server/tests/lip_sync_mock/fal.sim.yaml --port 4908 --output ndjson --no-history
# 另一终端，从 server/ 执行
VPT_FAL_SIM_URL=http://127.0.0.1:4908/fal .venv/bin/python -m pytest -q tests/test_fal_latentsync.py
```

模拟契约来自官方文档；未复用云端维护方 mock。测试覆盖实际 HTTP 与文件处理，
真实账号的访问权限、媒体限制、处理耗时和口型质量仍需样片验证。

## HeyGen

`HeyGen` 使用独立口型同步接口，不调用视频翻译或语音生成接口。

```python
import os
from pipeline.lip_sync.heygen import HeyGen

service = HeyGen(api_key=os.environ["HEYGEN_API_KEY"], mode="precision")
result = service.lip_sync("speaker.mp4", "final_voice.m4a", "speaker_synced.mp4")
```

- `mode` 默认 `precision`，也支持 `speed`。上传使用 v3 direct upload：初始化、流式 PUT、
  complete 注册后，将两个 `asset_id` 提交至 `POST /v3/lipsyncs`。
- 视频支持 MP4/WebM，直传上限 200 MiB；音频上传支持 WAV/MP3，上限 1.5 GiB，
  也遵守初始化返回的 `max_bytes`。M4A 等音频在本机转换为 WAV 临时副本，输入保持不变。
- 输入时长差最多 150ms，仅容忍编码取整；关闭 `enable_dynamic_duration`、字幕和音频增强，
  启用移除原 BGM，要求保留格式和帧率。下载后校验视频时长、完整解码，使用传入配音封装最终音轨。
- 输出必须是新的 `.mp4`。支持 `base_url`、`proxy_url`、`request_timeout`、`upload_timeout`、
  `poll_interval`、`job_timeout`。代理显式配置，不读取环境代理。
- `last_lipsync_id` 保留任务编号；失败、未知状态、缺少下载地址或本地超时均报错，
  失败不留下最终输出。超时不自动取消云端任务，也不自动重新提交付费任务。
- 签名上传时原样传递 `upload_headers`，不附加 API 密钥；下载同样不携带密钥。
  上传素材保留在用户的 HeyGen 账号，代码不自动删除云端资产。
- 已接入任务流水线。账号套餐权限、模型质量和真实处理时间仍需使用样片验证。

官方契约：

- https://developers.heygen.com/lipsync-precision
- https://developers.heygen.com/lipsync-speed
- https://developers.heygen.com/docs/upload-assets

本地 HTTP 模拟测试（fixture 根据官方文档编写，未复用维护方 mock，不调用真实服务）：

```sh
postman simulation run server/tests/lip_sync_mock/heygen.sim.yaml --port 4909 --output ndjson --no-history
# 另一终端，从 server/ 执行
VPT_HEYGEN_SIM_URL=http://127.0.0.1:4909/heygen .venv/bin/python -m pytest -q tests/test_heygen.py
```


## 自建 CUDA 服务（断点续传）

`RemoteLipSync` 调用 VideoPrinterTurbo_LipSync 后台，仍实现 `LipSyncBase.lip_sync()`。
服务及模型部署方式见相邻仓库 `VideoPrinterTurbo_LipSync/README.md`，接口见其 `API.md`。

```python
from pipeline.lip_sync.remote import RemoteLipSync

service = RemoteLipSync(base_url="http://192.168.1.100:8081", api_key="your-key",
                        timeline="strict", readiness_timeout=600, job_timeout=0)
result = service.lip_sync("speaker.mp4", "final_voice.wav", "speaker_synced.mp4")
```

- 构造函数配置 `request_timeout`、`poll_interval`、`job_timeout`、`chunk_size`、`retries`、`retry_delay`。
  直接连接服务，不读取环境代理；单实例不并发调用。
- 视频和音频跨机器上传，分块默认 8 MiB，服务端偏移为准。提交幂等，同一会话只生成一个任务。
- 输出旁保存 `.lipsync.json` 和 `.lipsync.part`；相同输入和输出路径再次调用即可续传，检查点不含密钥。
  服务端重启丢失状态时自动重新上传，失败任务不自动重提；手动删除检查点或换输出路径可重试。
- 支持 Range/If-Range 结果续传；成功前检查 SHA-256、时长、音视频流及完整解码，原子发布新 MP4。
  保留轻量 `.lipsync.lock` 文件用于跨进程互斥；锁在退出时自动释放，不必手动删除。
- 默认 strict 模式要求输入共享时间起点且时长差不超过 150ms；显式 `timeline="audio"`
  时允许不等长素材，按完整音频长度输出，视频不足时使用 MuseTalk 正放/倒放循环，较短音频则提前结束输出。
  两种模式均保留输入文件、不覆盖已有输出，检查视频和完整配音时长、哈希与解码。
  本地超时保留检查点，`last_job_id` 可查询远端原任务，超时不意味着取消。
- 配置显式传入，未新增数据库、前端入口或任务流水线行为。
- 测试位于相邻仓库 `VideoPrinterTurbo_LipSync/tests/test_transfer.py`，需同时保留两个仓库。

客户端会先访问 `/health` 等待模型就绪，音频模式还要求服务器明确声明 audio 支持。
模型恢复导致的 503 使用独立 `readiness_timeout`（默认 600 秒），不受短暂网络错误的三次重试次数限制；
重复 503 也有等待上限。401/403/422 等明确错误立即失败。已有任务恢复时直接查询原 ID，失败任务不会重做。
`request_timeout` 是单次 HTTP 请求超时；`job_timeout` 从输入预检和哈希完成后开始，涵盖就绪等待、
上传、排队、推理等待、下载与最终验证。自建服务客户端默认 `job_timeout=0`，不设总时限，
适用于高分辨率长视频；可显式设置正数秒数限制总等待时间。单次请求与模型就绪超时仍然生效。
客户端超时保留检查点，不取消远程工作；使用相同输入、输出路径和模式重试，会恢复原任务。

模式保存在 `.lipsync.json` 的身份信息中；模式改变新建会话。旧版无模式字段的检查点仅在 strict 下迁移复用。
旧 strict 服务和旧调用仍兼容；audio 模式需要同步更新客户端及服务端，不能单独取消客户端时长检查。

Windows NTFS 优先硬链接发布；文件系统明确不支持硬链接时，使用系统独占重命名。Linux/macOS 使用
对应的原子“不替换”接口；若系统或文件系统不能保证不覆盖则报错并保留下载文件。权限不足、磁盘满和
文件已存在不会静默降级，最终文件在完整校验之前不会出现。

真实 HTTP/GPU 验收，在本项目 `server/` 使用可用的 Python 环境和 FFmpeg/ffprobe：

```bash
python -m pipeline.lip_sync.check_remote \
  --base-url http://192.168.1.100:8081 \
  --video /absolute/path/speaker.mp4 --audio /absolute/path/voice.wav \
  --output /absolute/path/new_synced.mp4 --timeline audio
```

开启鉴权时在运行环境设置 `LIPSYNC_API_KEY`。工具生成 `.remote-verification.json`（无密钥），
记录模式、任务 ID、耗时、音视频时长和 SHA-256；播放输出验收口型和脸部融合。strict 验收应使用已对齐素材。

## 进度提示（2026-10-28 核对）

四种适配器现在均通过任务流水线选择，支持可选的 `on_progress(event)` 回调。
未传回调时也会输出 INFO 进度日志。同一阶段最多每 5 秒通知一次，阶段切换立即通知；
持续轮询会刷新已用时间。流水线将提示写入 `task_message`，任务列表沿用现有 5 秒轮询显示。
进度回调失败只记录警告，不会中止生成或重新提交付费任务。

| 实现 | 可显示信息 | 官方查询契约 |
| --- | --- | --- |
| 自建服务 | 排队位置、时间轴校验、已处理帧/总帧数及百分比、编码与校验阶段 | `GET /v1/jobs/{id}` 新增可选 `progress`；旧服务无此字段时显示状态和已用时 |
| Sync Labs | 状态和真实百分比（有返回时） | `GET /v2/generate/{id}?include=progress` 的 `progress_percent` |
| fal.ai LatentSync | 队列前方任务数、运行状态、最新运行日志 | status 查询带 `logs=true`，读取 `queue_position` 和 `logs` |
| HeyGen | 排队、运行、完成或失败及已用时 | `GET /v3/lipsyncs/{id}`；公开文档未列出百分比字段 |

百分比属于当前阶段，不是整个视频工作流的总进度。接口不提供百分比时返回 `null`，
不会用等待时长估算。服务端生成完成后仍会显示下载、校验阶段；本地文件成功发布后才报告
`stage=completed`、100%。上传/下载有已知大小时显示阶段字节百分比，否则仅显示阶段。
fal 运行日志经过密钥/URL 脱敏及长度限制，不作为通用的推理百分比解析。

回调字典包含 `provider`、`stage`、`percent`、`completed`、`total`、`unit`、
`queue_position`、`job_id`、`elapsed_seconds`、`detail`，未知项为 `None`。
日志和任务列表使用 `progress.format_progress()` 统一格式化，不需要新增数据库字段。

契约来源：

- https://sync.so/docs/api-reference/api/generate-api/get （`include=progress`，不能与 `wait=true` 组合）
- https://fal.ai/docs/documentation/model-apis/inference/queue
- https://developers.heygen.com/lipsync-precision

进度回归：`python -m pytest tests/test_lipsync_progress.py`。
三个现有 Postman 模拟用例增加进度断言，仍需按模拟服务说明启动后运行；
未使用真实云端凭据或付费生成任务验证。
