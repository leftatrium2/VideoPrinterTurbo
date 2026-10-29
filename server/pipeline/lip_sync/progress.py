"""Stage-scoped progress shared by the local and cloud lip-sync clients."""
import logging
import math
import time

logger = logging.getLogger(__name__)
PROVIDERS = {'remote': '自建服务', 'sync_labs': 'Sync Labs', 'heygen': 'HeyGen', 'fal': 'fal.ai'}
STAGES = {
    'preparing': '检查输入', 'waiting_ready': '等待服务就绪',
    'upload_video': '上传视频', 'upload_audio': '上传音频', 'submitting': '提交任务',
    'queued': '排队等待', 'running': '服务端处理', 'remote_completed': '服务端生成完成',
    'timestamp_validation': '校验视频时间轴', 'video_decode': '读取视频帧',
    'face_detection': '检测人脸', 'audio_decode': '读取音频', 'audio_features': '提取音频特征',
    'inference': '处理视频帧', 'encoding_finalize': '完成视频编码',
    'finalizing': '封装并校验结果', 'download': '下载结果', 'validating': '校验结果',
    'completed': '对口型完成', 'failed': '对口型失败',
}


def valid_percent(value):
    return (float(value) if isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and 0 <= value <= 100 else None)


def format_progress(event):
    provider = PROVIDERS.get(event.get('provider'), '对口型')
    stage = STAGES.get(event.get('stage'), '处理中')
    text = f'对口型 · {provider} · {stage}'
    percent = valid_percent(event.get('percent'))
    if percent is not None:
        text += f' {percent:.1f}%'
    completed, total = event.get('completed'), event.get('total')
    if type(completed) is int and type(total) is int and total > 0:
        unit = '帧' if event.get('unit') == 'frames' else '字节'
        text += f'（{completed}/{total} {unit}）'
    elif type(completed) is int and completed >= 0:
        text += (f'（已处理 {completed} 帧）' if event.get('unit') == 'frames'
                 else f'（已传输 {completed / 1024**2:.1f} MiB）')
    position = event.get('queue_position')
    if isinstance(position, int) and not isinstance(position, bool) and position >= 0:
        text += f'，前方 {position} 个任务'
    elapsed = event.get('elapsed_seconds')
    if isinstance(elapsed, (int, float)) and math.isfinite(elapsed) and elapsed >= 0:
        text += f'，已用时 {int(elapsed)} 秒'
    detail = event.get('detail')
    if detail:
        text += f' · {detail}'
    return text


class ProgressReporter:
    def __init__(self, provider, callback=None, interval=5):
        self.provider, self.callback, self.interval = provider, callback, interval
        self.started = time.monotonic()
        self.last_time, self.last_stage = -math.inf, None

    def emit(self, stage, *, percent=None, completed=None, total=None, unit=None,
             queue_position=None, job_id=None, detail=None, force=False):
        now = time.monotonic()
        if stage == self.last_stage and not force and now - self.last_time < self.interval:
            return
        percent = valid_percent(percent)
        if (percent is None and type(completed) is int and type(total) is int
                and 0 <= completed <= total and total > 0):
            percent = 100 * completed / total
        event = {'provider': self.provider, 'stage': stage, 'percent': percent,
                 'completed': completed, 'total': total, 'unit': unit,
                 'queue_position': queue_position, 'job_id': job_id,
                 'elapsed_seconds': round(now - self.started, 1), 'detail': detail}
        self.last_time, self.last_stage = now, stage
        logger.info('%s', format_progress(event))
        if self.callback:
            try:
                self.callback(dict(event))
            except Exception as exc:
                # UI/database progress failure must not resubmit a paid generation.
                logger.warning('LipSync progress callback failed (%s)', type(exc).__name__)


class ProgressFile:
    """Transparent readable file; Requests keeps streaming and its content length."""
    def __init__(self, source, report, stage, total):
        self.source, self.report, self.stage, self.total = source, report, stage, total
        report(stage, completed=source.tell(), total=total, unit='bytes', force=True)

    def __getattr__(self, name):
        return getattr(self.source, name)

    def read(self, size=-1):
        data = self.source.read(size)
        position = self.source.tell()
        self.report(self.stage, completed=position, total=self.total, unit='bytes',
                    force=position == self.total)
        return data


def response_size(response):
    if response.headers.get('Content-Encoding', 'identity').lower() != 'identity':
        return None
    value = response.headers.get('Content-Length', '')
    return int(value) if isinstance(value, str) and value.isdigit() and int(value) > 0 else None
