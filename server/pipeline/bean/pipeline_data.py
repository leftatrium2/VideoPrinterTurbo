from dataclasses import dataclass
from typing import Optional

from pipeline.bean.asr_bean import AsrBean
from pipeline.bean.bgm_bean import BgmBean
from pipeline.bean.llm_bean import LLMBean
from pipeline.bean.tts_bean import TTSBean
from pipeline.bean.video_downloader_bean import VideoDownloaderBean
from pipeline.bean.video_overlay_bean import VideoOverlayBean
from utils import const
from utils.convert_subtitle_ttml_to_srt import SubtitleBean


@dataclass
class PipeLineData:
    task_id: str = ""
    url: str = ""
    status: int = const.PIPELINE_STATUS_INI
    video_bean: Optional[VideoDownloaderBean] = None
    # 是否启用ASR或者拉取字幕（从youtube.com）
    is_asr_or_subtitle: bool = False
    asr_bean: Optional[AsrBean] = None
    # 是否启用LLM改写
    is_llm: bool = False
    llm_bean: Optional[LLMBean] = None
    # 是否启用TTS语音
    is_tts: bool = False
    tts_bean: Optional[TTSBean] = None
    # 是否启用字幕（输出的时候，将字幕打在屏幕上）
    is_subtitle: bool = False
    subtitle_bean: Optional[SubtitleBean] = None
    # 是否启用BGM（如果启用，那么会在当前视频中合并一个BGM音轨进去）
    is_bgm: bool = False
    bgm_bean: Optional[BgmBean] = None
    # 是否启用视频改写（如果启用，那么当前视频直接被覆盖）
    is_video_overlay: bool = False
    video_overlay_bean: Optional[VideoOverlayBean] = None
