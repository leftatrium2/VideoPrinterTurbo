import asyncio
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import config.config as config
from utils import file_utils, const
from pipeline.downloader.yt_dlp.yt_dlp_downloader import YtDlpDownloader


@pytest.mark.parametrize('getter,key', [
    ('get_storage_path', 'path'), ('get_upload_path', 'upload'),
    ('get_download_path', 'download'), ('get_subtitle_path', 'subtitle'),
    ('get_video_to_text_path', 'video_to_text'), ('get_separate_vocals_path', 'audio_separator'),
    ('get_llm_rewrite_path', 'llm_rewrite'), ('get_tts_rewrite_path', 'tts_rewrite'),
    ('get_material_path', 'material'), ('get_output_path', 'output'),
])
def test_config_forward_slashes_create_native_absolute_directories(tmp_path, monkeypatch, getter, key):
    monkeypatch.setenv('VPT_DATA_DIR', str(tmp_path / '用户 data'))
    storage = {key: 'storage/downloads'}
    monkeypatch.setitem(config.config, 'storage', storage)
    result = asyncio.run(getattr(file_utils, getter)())
    assert result == str((tmp_path / '用户 data/storage/downloads').resolve())
    assert Path(result).is_dir()
    assert storage[key] == 'storage/downloads'


def test_absolute_paths_and_relative_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv('VPT_DATA_DIR', str(tmp_path))
    target = tmp_path / 'storage/downloads/video.mp4'
    assert file_utils.get_absolute_path(str(target)) == str(target.resolve())
    assert file_utils.get_relative_path(str(target)) == 'storage/downloads/video.mp4'
    assert file_utils.get_absolute_path(file_utils.get_relative_path(str(target))) == str(target.resolve())


@pytest.mark.parametrize('outcome', ['none', 'missing', 'empty', 'error', 'success'])
def test_downloader_only_reports_success_for_existing_nonempty_file(tmp_path, monkeypatch, outcome):
    factory = MagicMock()
    ydl = factory.return_value.__enter__.return_value
    ydl.extract_info.return_value = None if outcome == 'none' else {'title': 'test'}
    if outcome == 'error':
        ydl.extract_info.side_effect = RuntimeError('Download failed: network unavailable')
    monkeypatch.setattr('pipeline.downloader.yt_dlp.yt_dlp_downloader.yt_dlp.YoutubeDL', factory)
    output = tmp_path / '用户 data' / 'task.mp4'
    output.parent.mkdir()
    if outcome in ('empty', 'success'):
        output.write_bytes(b'video' if outcome == 'success' else b'')
    result = YtDlpDownloader().download('https://example.com/video', str(output.with_suffix('')))
    assert factory.call_args.args[0]['ignoreerrors'] is False
    if outcome == 'success':
        assert result['status'] == 0
        assert result['video_path'] == str(output.resolve())
    else:
        assert result['status'] == -1
        assert result['message']
        assert 'video_path' not in result


@pytest.mark.parametrize('result', [None, {'status': -1, 'message': 'network unavailable'},
                                   {'status': 0}, {'status': 0, 'video_path': 'missing.mp4'}])
def test_pipeline_stops_and_persists_download_failures(tmp_path, monkeypatch, result):
    import pipeline.pipeline_manager as module
    from models.model import VptTasks
    monkeypatch.setenv('VPT_DATA_DIR', str(tmp_path))
    monkeypatch.setattr(module, 'check_video', lambda **kwargs: True)
    monkeypatch.setattr(module, 'download_video', lambda **kwargs: result)
    saved = MagicMock()
    monkeypatch.setattr(module.PipelineManager, '_PipelineManager__update_db_task', staticmethod(saved))
    asr = MagicMock()
    monkeypatch.setattr(module, 'asr_convert', asr)
    manager = module.PipelineManager()
    task = VptTasks(task_id='test', task_url='https://example.com/video', is_from_asr_or_subtitle=1)
    assert manager.process_now(task) is None
    assert task.task_status in (const.PIPELINE_ERR_YT_DLP, const.PIPELINE_ERR_DOWNLOADER_SAVE_LOCAL_PATH)
    assert task.task_message
    if result and result.get('status') == -1:
        assert task.task_message == 'network unavailable'
    assert saved.call_args.args[0] is task
    asr.assert_not_called()


def test_pipeline_accepts_legacy_downloader_result_without_status(tmp_path, monkeypatch):
    import pipeline.pipeline_manager as module
    from models.model import VptTasks
    monkeypatch.setenv('VPT_DATA_DIR', str(tmp_path))
    video = tmp_path / 'video.mp4'
    video.write_bytes(b'video')
    monkeypatch.setattr(module, 'check_video', lambda **kwargs: True)
    monkeypatch.setattr(module, 'download_video', lambda **kwargs: {'video_path': str(video)})
    monkeypatch.setattr(module.PipelineManager, '_PipelineManager__update_db_task', staticmethod(MagicMock()))
    entered_asr = MagicMock(side_effect=RuntimeError('entered ASR'))
    monkeypatch.setattr(module.PipelineManager, '_PipelineManager__get_asr_config', staticmethod(entered_asr))
    task = VptTasks(task_id='test', task_url='https://example.com/video', is_from_asr_or_subtitle=1)
    with pytest.raises(RuntimeError, match='entered ASR'):
        module.PipelineManager().process_now(task)
    entered_asr.assert_called_once()
