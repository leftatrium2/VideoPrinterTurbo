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
