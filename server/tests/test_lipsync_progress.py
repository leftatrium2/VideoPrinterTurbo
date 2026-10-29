"""Progress contracts without provider credentials, paid jobs or listening sockets."""
import io
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from pipeline.lip_sync.progress import ProgressReporter, ProgressFile, format_progress, valid_percent
from pipeline.lip_sync.sync_labs import SyncLabs
from pipeline.lip_sync.heygen import HeyGen
from pipeline.lip_sync.fal_latentsync import FalLatentSync


@pytest.mark.parametrize('value', [None, True, '20', -1, 101, float('nan'), float('inf')])
def test_invalid_percentage_is_not_invented(value):
    assert valid_percent(value) is None


def test_phase_change_heartbeat_and_callback_failure_are_safe(monkeypatch, caplog):
    import pipeline.lip_sync.progress as module
    clock = SimpleNamespace(now=0.)
    monkeypatch.setattr(module, 'time', SimpleNamespace(monotonic=lambda: clock.now))
    events = []
    reporter = ProgressReporter('heygen', events.append, interval=5)
    reporter.emit('queued')
    clock.now = 1
    reporter.emit('queued')
    assert len(events) == 1
    clock.now = 6
    reporter.emit('queued')
    assert events[-1]['elapsed_seconds'] == 6
    assert events[-1]['percent'] is None
    reporter.emit('running')
    assert len(events) == 3
    reporter.callback = Mock(side_effect=RuntimeError('database down'))
    reporter.emit('completed', percent=100)
    assert 'callback failed' in caplog.text


def test_streaming_upload_keeps_content_length_and_reports_bytes():
    from requests.utils import super_len
    events = []
    reporter = ProgressReporter('fal', events.append, interval=0)
    source = io.BytesIO(b'abcdef')
    wrapped = ProgressFile(source, reporter.emit, 'upload_video', 6)
    assert super_len(wrapped) == 6
    assert wrapped.read(2) == b'ab'
    assert wrapped.read(4) == b'cdef'
    assert events[-1]['percent'] == 100
    assert events[-1]['completed'] == events[-1]['total'] == 6
    assert '上传视频' in format_progress(events[-1])


def prepare(adapter):
    events = []
    adapter._progress_reporter = ProgressReporter(adapter.PROGRESS_PROVIDER, events.append, interval=0)
    return events


def test_sync_requests_real_progress_and_does_not_finish_before_download(monkeypatch):
    adapter = SyncLabs('test-only', poll_interval=.001)
    events = prepare(adapter)
    adapter._api = Mock(side_effect=[{'status': 'PROCESSING', 'progress_percent': 42.5},
                                     {'status': 'COMPLETED', 'outputUrl': 'https://example.invalid/result.mp4'}])
    assert adapter._wait(object(), {'id': 'job-1', 'status': 'PENDING'}) == 'https://example.invalid/result.mp4'
    assert [event['stage'] for event in events] == ['queued', 'running', 'remote_completed']
    assert events[1]['percent'] == 42.5
    assert not any(event['stage'] == 'completed' for event in events)
    for call in adapter._api.call_args_list:
        assert call.args[1] == 'GET'
        assert call.kwargs['params'] == {'include': 'progress'}


def test_heygen_uses_only_documented_status_without_guessing_percentage():
    adapter = HeyGen('test-only', poll_interval=.001)
    events = prepare(adapter)
    adapter._api = Mock(side_effect=[{'status': 'pending'}, {'status': 'running'},
                                     {'status': 'completed', 'video_url': 'https://example.invalid/result.mp4'}])
    adapter._wait(object(), {'lipsync_id': 'job-1'})
    assert [event['stage'] for event in events] == ['queued', 'running', 'remote_completed']
    assert all(event['percent'] is None for event in events)


def test_fal_queue_position_and_logs_are_enabled_and_redacted():
    adapter = FalLatentSync('test-only', poll_interval=.001)
    events = prepare(adapter)
    adapter._json = Mock(side_effect=[{'status': 'IN_QUEUE', 'queue_position': 0},
                                      {'status': 'IN_PROGRESS', 'logs': [{'message': 'step 10 test-only https://secret.invalid/token'}]},
                                      {'status': 'COMPLETED'}, {'video': {'url': 'https://example.invalid/result.mp4'}}])
    adapter._wait(object(), {'request_id': 'job-1'})
    assert events[0]['queue_position'] == 0
    assert events[1]['percent'] is None
    assert 'test-only' not in events[1]['detail']
    assert 'https://' not in events[1]['detail']
    for call in adapter._json.call_args_list[:-1]:
        assert call.kwargs['params'] == {'logs': 'true'}


def test_fal_completed_with_error_is_reported_as_failure():
    adapter = FalLatentSync('test-only')
    events = prepare(adapter)
    adapter._json = Mock(return_value={'status': 'COMPLETED', 'error': 'no face'})
    with pytest.raises(RuntimeError, match='no face'):
        adapter._wait(object(), {'request_id': 'job-1'})
    assert events[-1]['stage'] == 'failed'
    assert not any(event['stage'] in ('remote_completed', 'completed') for event in events)


@pytest.mark.parametrize('provider', ['remote', 'sync', 'heygen', 'fal'])
def test_pipeline_forwards_progress_to_every_adapter(tmp_path, monkeypatch, provider):
    from pipeline.utils import pipeline_lipsync_utils as module
    from utils import const
    async def directory():
        return str(tmp_path)
    monkeypatch.setattr(module, 'get_lip_sync_path', directory)
    def balance(**kwargs):
        from pathlib import Path
        Path(kwargs['output_wav_path']).write_bytes(b'prepared')
    monkeypatch.setattr(module, '_balance_video_and_audio_duration', balance)
    received = []
    class Adapter:
        def __init__(self, *args, **kwargs):
            self.callback = kwargs['on_progress']
        def lip_sync(self, video, audio, output_path):
            from pathlib import Path
            self.callback({'provider': provider, 'stage': 'running'})
            Path(output_path).write_bytes(b'result')
            return output_path
    for name in ('RemoteLipSync', 'SyncLabs', 'HeyGen', 'FalLatentSync'):
        monkeypatch.setattr(module, name, Adapter)
    kind = {'remote': const.TASK_CONFIG_LIP_SYNC_REMOTE, 'sync': const.TASK_CONFIG_LIP_SYNC_SYNCLABS,
            'heygen': const.TASK_CONFIG_LIP_SYNC_HEYGEN, 'fal': const.TASK_CONFIG_LIP_SYNC_FALLATENT}[provider]
    module.lip_sync('video.mp4', 'audio.wav', kind, 'task', on_progress=received.append,
                    remote_base_url='http://localhost:8081', sync_labs_apikey='test-only',
                    hey_gen_apikey='test-only', fal_latent_sync_apikey='test-only')
    assert received == [{'provider': provider, 'stage': 'running'}]
