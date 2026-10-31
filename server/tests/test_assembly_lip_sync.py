import json
import subprocess

import pytest

from pipeline.bean.pipeline_data import PipeLineData
from pipeline.rendering.ffmpeg_assembly_video import FFMpegAssemblyVideo
from utils.exception import VPTException


@pytest.mark.parametrize('lip_sync,tts', [(False, False), (False, True), (True, False), (True, True)])
@pytest.mark.parametrize('background', ['none', 'separated', 'custom'])
@pytest.mark.parametrize('subtitles', [False, True])
def test_render(tmp_path, lip_sync, tts, background, subtitles):
    video = tmp_path / 'lip.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                    'color=c=blue:s=160x120:r=30', '-f', 'lavfi', '-i',
                    'sine=frequency=440:sample_rate=48000', '-t', '1',
                    '-c:v', 'libx264', '-c:a', 'aac', str(video)], check=True)
    data = PipeLineData()
    data.video_bean.video_full_path = 'missing-original.mp4' if lip_sync else str(video)
    data.video_bean.duration = 1
    data.video_bean.width = 160
    data.video_bean.height = 120
    data.is_lip_sync = lip_sync
    data.lip_sync_bean.lip_sync_full_path = str(video)
    # Empty materials and missing TTS must be ignored with lip sync enabled.
    data.is_material = lip_sync
    data.is_tts = tts
    data.tts_bean.tts_full_path = 'missing-tts.wav' if lip_sync else str(video)
    data.is_bgm = background == 'custom'
    data.bgm_bean.uploaded_bgm = str(video)
    data.bgm_bean.bgm_volume = 0.2
    data.is_need_audio_separator = background != 'none'
    data.audio_separator_bean.bgm_path = str(video) if background == 'separated' else 'missing-bgm.wav'
    data.is_asr = subtitles
    data.is_rewrite_subtitle = subtitles
    final = tmp_path / 'final.srt'
    final.write_text('1\n00:00:00,000 --> 00:00:00,900\nHello\n', encoding='utf-8')
    data.asr_bean.subtitle_full_path = str(final)
    data.is_llm = subtitles
    data.llm_bean.llm_full_path = 'missing-llm.srt' if tts else str(final)
    data.tts_bean.final_subtitle_path = str(final)
    output = tmp_path / 'result.mp4'
    assert FFMpegAssemblyVideo(data).assembly(str(output)) == str(output)
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format',
                             '-of', 'json', str(output)], check=True, capture_output=True, text=True)
    info = json.loads(result.stdout)
    assert {stream['codec_type'] for stream in info['streams']} == {'audio', 'video'}
    assert float(info['format']['duration']) == pytest.approx(1, abs=0.1)
    assert not list(tmp_path.glob('.vpt_materials_*'))


@pytest.mark.parametrize('path', ['', 'missing.mp4'])
def test_missing_lip_sync_result(tmp_path, path):
    data = PipeLineData()
    data.is_lip_sync = True
    data.is_material = True
    data.lip_sync_bean.lip_sync_full_path = path
    with pytest.raises(VPTException, match='对口型结果视频不存在'):
        FFMpegAssemblyVideo(data).assembly(str(tmp_path / 'result.mp4'))
