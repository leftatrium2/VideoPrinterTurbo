from sympy.abc import M

from models import model
from pipeline.bean.asr_bean import AsrBean
from pipeline.bean.bgm_bean import BgmBean
from pipeline.bean.ffmpeg_bean import FFMPEGBean
from pipeline.bean.llm_bean import LLMBean
from pipeline.bean.subtitle_bean import SubtitleBean
from pipeline.bean.tts_bean import TTSBean
from pipeline.bean.video_downloader_bean import VideoDownloaderBean
from pipeline.bean.video_overlay_bean import MaterialVideoBean
from utils import const


class PipeLineData:
    task_id: str = ""
    url: str = ""
    status: int = const.PIPELINE_STATUS_INI
    is_remote_video: bool = True
    video_bean: VideoDownloaderBean = VideoDownloaderBean()
    # 是否启用ASR或者拉取字幕（从youtube.com）
    is_asr: bool = False
    asr_bean: AsrBean = AsrBean()
    # 是否启用LLM改写
    is_llm: bool = False
    llm_bean: LLMBean = LLMBean()
    # 是否启用TTS语音
    is_tts: bool = False
    tts_bean: TTSBean = TTSBean()
    # 是否启用字幕（输出的时候，将字幕打在屏幕上）
    is_rewrite_subtitle: bool = False
    subtitle_bean: SubtitleBean = SubtitleBean()
    # 是否启用BGM（如果启用，那么会在当前视频中合并一个BGM音轨进去）
    is_bgm: bool = False
    bgm_bean: BgmBean = BgmBean()
    # 是否启用视频改写（如果启用，那么当前视频直接被覆盖）
    is_material: bool = False
    material_video_bean: MaterialVideoBean = MaterialVideoBean()
    # 最后整理出来，往ffmpeg送的数据
    ffmpeg_bean: FFMPEGBean = FFMPEGBean()

    def __str__(self) -> str:
        return f"""
        PipeLineData(
        task_id: {self.task_id}, 
        url: {self.url}, 
        status: {self.status}, 
        video_bean: {self.video_bean if self.video_bean else ''}, 
        is_asr: {self.is_asr},
        asr_bean: {self.asr_bean if self.asr_bean else ''},
        is_llm: {self.is_llm},
        llm_bean: {self.llm_bean if self.llm_bean else ''},
        is_tts: {self.is_tts},
        tts_bean: {self.tts_bean if self.tts_bean else ''},
        is_rewrite_subtitle: {self.is_rewrite_subtitle},
        subtitle_bean: {self.subtitle_bean if self.subtitle_bean else ''},
        is_bgm: {self.is_bgm},
        bgm_bean: {self.bgm_bean if self.bgm_bean else ''},
        is_material: {self.is_material},
        material_video_bean: {self.material_video_bean if self.material_video_bean else ''},
        ffmpeg_bean: {self.ffmpeg_bean if self.ffmpeg_bean else ''}
        )
        """
