import json
from types import SimpleNamespace

import pytest

from pipeline.bean.bgm_bean import BgmBean
from pipeline.pipeline_manager import PipelineManager
from pipeline.rendering.ffmpeg_assembly_video import FFMpegAssemblyVideo
from utils.exception import VPTException


def task_data(raw, enabled=True):
    manager = PipelineManager()
    task = SimpleNamespace(
        task_id="bgm-test", task_url="https://example.com/video",
        is_from_asr_or_subtitle=0, is_llm=0, is_rewrite_to_tts=0,
        is_rewrite_to_subtitle=0, is_bgm=int(enabled), bgm_volume=0.5,
        uploaded_bgm=raw, is_video_material=0,
    )
    manager.get_data().bgm_bean = BgmBean()
    manager._PipelineManager__process_task_info(task)
    data = manager.get_data()
    data.video_bean = SimpleNamespace(duration=1, height=1080, video_full_path="video.mp4")
    return data


@pytest.mark.parametrize("raw", ["{}", "", "  ", None])
def test_random_bgm_uses_audio_path(raw, tmp_path, monkeypatch):
    song = tmp_path / "output1.mp3"
    song.touch()
    monkeypatch.setattr("pipeline.rendering.ffmpeg_assembly_video.get_resource_bgm_path", lambda: str(tmp_path))
    renderer = FFMpegAssemblyVideo(task_data(raw))
    commands = []
    monkeypatch.setattr(renderer, "_FFMpegAssemblyVideo__run_ffmpeg", lambda command, *args: commands.append(command))
    renderer.assembly(str(tmp_path / "result.mp4"))
    command = commands[0]
    assert [command[i + 1] for i, arg in enumerate(command) if arg == "-i"] == ["video.mp4", str(song)]


def test_custom_bgm_extracts_saved_as(tmp_path, monkeypatch):
    song = tmp_path / "my song.mp3"
    song.touch()
    monkeypatch.setattr("utils.file_utils.get_current_path", lambda: str(tmp_path))
    data = task_data(json.dumps({"saved_as": song.name, "filename": "original.mp3"}))
    assert data.bgm_bean.uploaded_bgm == str(song)
    renderer = FFMpegAssemblyVideo(data)
    commands = []
    monkeypatch.setattr(renderer, "_FFMpegAssemblyVideo__run_ffmpeg", lambda command, *args: commands.append(command))
    renderer.assembly(str(tmp_path / "result.mp4"))
    assert str(song) in commands[0]


@pytest.mark.parametrize("raw", ['{broken', '[]', 'null', '"song.mp3"', '{"filename":"a.mp3"}', '{"saved_as":42}', '{"saved_as":" "}'])
def test_invalid_config_fails_during_task_initialization(raw):
    with pytest.raises(VPTException, match="BGM"):
        task_data(raw)


@pytest.mark.parametrize("custom", [False, True])
def test_missing_bgm_fails_before_material_preprocessing(custom, tmp_path, monkeypatch):
    raw = json.dumps({"saved_as": str(tmp_path / "missing.mp3")}) if custom else "{}"
    data = task_data(raw)
    data.is_material = True
    monkeypatch.setattr("pipeline.rendering.ffmpeg_assembly_video.get_resource_bgm_path", lambda: str(tmp_path))
    renderer = FFMpegAssemblyVideo(data)
    def unexpected(*args):
        pytest.fail("BGM should be validated before material preprocessing")
    monkeypatch.setattr(renderer, "_FFMpegAssemblyVideo__prepare_materials", unexpected)
    with pytest.raises(VPTException, match="BGM"):
        renderer.assembly(str(tmp_path / "result.mp4"))


def test_disabled_bgm_ignores_invalid_config(tmp_path, monkeypatch):
    renderer = FFMpegAssemblyVideo(task_data("{broken", enabled=False))
    commands = []
    monkeypatch.setattr(renderer, "_FFMpegAssemblyVideo__run_ffmpeg", lambda command, *args: commands.append(command))
    renderer.assembly(str(tmp_path / "result.mp4"))
    assert commands[0].count("-i") == 1
