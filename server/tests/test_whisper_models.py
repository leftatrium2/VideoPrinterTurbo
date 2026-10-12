import hashlib
from pathlib import Path
import threading
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from service.whisper_model_manager import WhisperModelManager


def fake_hub(manager, fail=False, block=None, model="tiny"):
    payload = b'model fixture'
    siblings = [SimpleNamespace(rfilename=name, size=len(payload), lfs=SimpleNamespace(sha256=hashlib.sha256(payload).hexdigest())) for name in manager._required(model)]

    def download(repo, name, **kwargs):
        if block:
            block.wait(5)
        if fail:
            raise OSError('network unavailable')
        target = Path(kwargs['local_dir']) / name
        target.write_bytes(payload)
        return str(target)

    return patch('huggingface_hub.HfApi.model_info', return_value=SimpleNamespace(sha='test-revision', siblings=siblings)), patch('huggingface_hub.hf_hub_download', side_effect=download)


def test_download_verified_and_reused_offline(tmp_path):
    manager = WhisperModelManager(tmp_path)
    api, files = fake_hub(manager)
    with api, files as download:
        path = manager.ensure('tiny')
        assert download.call_count == 4
    restarted = WhisperModelManager(tmp_path)
    with patch('huggingface_hub.HfApi.model_info', side_effect=AssertionError('must stay offline')):
        assert restarted.ensure('tiny') == path
    assert restarted.status('tiny')['state'] == 'ready'


def test_failed_download_can_retry(tmp_path):
    manager = WhisperModelManager(tmp_path)
    api, files = fake_hub(manager, fail=True)
    with api, files, pytest.raises(RuntimeError, match='network unavailable'):
        manager.ensure('base')
    assert manager.status('base')['state'] == 'failed'
    assert not (tmp_path / 'base' / 'ready.json').exists()
    api, files = fake_hub(manager)
    with api, files:
        manager.ensure('base')
    assert manager.status('base')['state'] == 'ready'


def test_concurrent_requests_share_download(tmp_path):
    manager = WhisperModelManager(tmp_path)
    gate = threading.Event()
    api, files = fake_hub(manager, block=gate)
    with api, files as download:
        manager.start('small')
        original = manager._threads['small']
        manager.start('small')
        assert manager._threads['small'] is original
        gate.set()
        manager.ensure('small')
        assert download.call_count == 4


def test_incomplete_or_tampered_cache_is_not_ready(tmp_path):
    manager = WhisperModelManager(tmp_path)
    api, files = fake_hub(manager)
    with api, files:
        path = manager.ensure('tiny')
    (path / 'model.bin').write_bytes(b'truncated')
    assert WhisperModelManager(tmp_path).status('tiny')['state'] == 'missing'
    assert manager.status('tiny')['state'] == 'missing'


def test_model_name_cannot_escape_cache(tmp_path):
    with pytest.raises(ValueError):
        WhisperModelManager(tmp_path).start('../outside')


def test_faster_engine_loads_local_cpu_model(tmp_path):
    from pipeline.transcriber.whisper_asr.engine.faster_engine import FasterWhisperEngine
    with patch('service.whisper_model_manager.model_manager.ensure', return_value=tmp_path), patch('faster_whisper.WhisperModel') as model:
        FasterWhisperEngine(model_size='small')._load_model()
        model.assert_called_once_with(str(tmp_path), local_files_only=True, device='cpu', compute_type='int8')


def test_large_v3_downloads_preprocessor_and_json_vocabulary(tmp_path):
    manager = WhisperModelManager(tmp_path)
    api, files = fake_hub(manager, model="large-v3")
    with api, files as download:
        path = manager.ensure('large-v3')
        assert download.call_count == 5
    assert (path / 'preprocessor_config.json').exists()
    assert (path / 'vocabulary.json').exists()
