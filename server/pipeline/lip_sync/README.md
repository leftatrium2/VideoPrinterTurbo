# 对口型实现

当前提供 `SyncLabs`，实现 `LipSyncBase.lip_sync(video_path, audio_path, output_path)`。
模型调用独立于 `PipelineManager`，暂未添加任务字段或前端入口。

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
`fal-ai/latentsync`，尚未接入任务流水线。

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
- 尚未接入任务流水线。账号套餐权限、模型质量和真实处理时间仍需使用样片验证。

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
